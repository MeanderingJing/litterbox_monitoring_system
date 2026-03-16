"""
MCP client for the Postgres MCP server (HenkDz).

Spawns the server via npx and communicates over stdio. Provides a class-based
client (PostgresMCPClient) with AsyncExitStack for lifecycle, plus
get_schema() and execute_query() for use with Claude (NL -> SQL -> results).

- Class-based client with AsyncExitStack for connect/cleanup and correct
  teardown order (stdio transport then session).
- session(), list_tools(), call_tool() implemented; get_schema() and
  execute_query() use them so one client can serve both without respawning.
- Optional tool list cache so list_tools() is called once per client.

For asyncio on Windows, set: asyncio.set_event_loop_policy(
  asyncio.WindowsProactorEventLoopPolicy()) before asyncio.run().
"""

import json
import logging
import os
from contextlib import AsyncExitStack
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

# Default connection string (same as app/docker-compose)
_DEFAULT_CONNECTION_STRING = (
    "postgresql://example_user:example_password@localhost:5435/example_db"
)


def get_connection_string() -> str:
    """Read Postgres connection string from env."""
    return (
        os.environ.get("POSTGRES_CONNECTION_STRING")
        or os.environ.get("DATABASE_URL")
        or _DEFAULT_CONNECTION_STRING
    )


def _server_params(connection_string: str) -> StdioServerParameters:
    """Build stdio server parameters for the Postgres MCP server."""
    return StdioServerParameters(
        command="npx",
        args=[
            "-y",
            "@henkey/postgres-mcp-server",
            "--connection-string",
            connection_string,
        ],
        env=None,  # inherit so npx works (PATH, etc.)
    )


def _text_from_tool_result(result: types.CallToolResult) -> str:
    """Extract plain text from a types.CallToolResult for display or schema."""
    if result.content:
        return "".join(
            getattr(c, "text", str(c)) for c in result.content if hasattr(c, "text")
        )
    if result.structuredContent is not None:
        return json.dumps(result.structuredContent, indent=2)
    return ""


def _rows_from_tool_result(
    result: types.CallToolResult,
) -> tuple[list[str], list[list[Any]]]:
    """
    Try to get columns and rows from a types.CallToolResult (e.g. execute_query).
    Returns (columns, rows); if not structured, returns ([], []).
    """
    if result.structuredContent:
        sc = result.structuredContent
        if isinstance(sc, dict):
            cols = sc.get("columns") or sc.get("columnNames") or []
            rows = sc.get("rows") or sc.get("data") or []
            if cols or rows:
                return (
                    list(cols),
                    [list(r) if not isinstance(r, list) else r for r in rows],
                )
    text = _text_from_tool_result(result)
    if not text:
        return ([], [])
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            cols = data.get("columns", data.get("columnNames", []))
            rows = data.get("rows", data.get("data", []))
            return (
                list(cols),
                [list(r) if not isinstance(r, list) else r for r in rows],
            )
        if isinstance(data, list) and data and isinstance(data[0], dict):
            cols = list(data[0].keys())
            rows = [[r[k] for k in cols] for r in data]
            return (cols, rows)
    except json.JSONDecodeError:
        pass
    return ([], [])


class PostgresMCPClient:
    """
    MCP client for the Postgres MCP server (HenkDz).

    Uses AsyncExitStack to manage stdio transport and session lifecycle.
    Reuse one client for get_schema() + execute_query() to avoid spawning
    the server multiple times.
    """

    def __init__(self, connection_string: Optional[str] = None):
        self._connection_string = connection_string or get_connection_string()
        self._server_params = _server_params(self._connection_string)
        self._exit_stack: AsyncExitStack = AsyncExitStack()
        self._session: Optional[ClientSession] = None
        self._tools_cache: Optional[list[types.Tool]] = None

    async def connect(self) -> None:
        """Spawn the MCP server and initialize the session."""
        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(self._server_params)
        )
        read_stream, write_stream = stdio_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await self._session.initialize()
        logger.debug("Postgres MCP session initialized")

    def session(self) -> ClientSession:
        """Return the current session. Raises if not connected."""
        if self._session is None:
            raise ConnectionError(
                "Client not connected. Call connect() first or use async with PostgresMCPClient(...)."
            )
        return self._session

    async def list_tools(self) -> list[types.Tool]:
        """Return the list of tools exposed by the MCP server (cached after first call)."""
        if self._tools_cache is not None:
            return self._tools_cache
        result = await self.session().list_tools()
        self._tools_cache = list(result.tools)
        logger.debug("Available MCP tools: %s", [t.name for t in self._tools_cache])
        return self._tools_cache

    async def call_tool(
        self, tool_name: str, tool_input: Optional[dict[str, Any]] = None
    ) -> types.CallToolResult:
        """Call a tool by name with the given arguments."""
        return await self.session().call_tool(tool_name, tool_input or {})

    async def get_schema(self) -> str:
        """
        Get schema information from the Postgres MCP server (tables, columns).
        Returns a string suitable for inclusion in a Claude prompt.
        """
        tool_list = await self.list_tools()
        tool_names = [t.name for t in tool_list]
        schema_tool = None
        # Prefer known Postgres MCP schema tool first.
        if "pg_manage_schema" in tool_names:
            schema_tool = "pg_manage_schema"
        else:
            for name in (
                "schema_management",
                "get_schema_info",
                "list_tables",
                "get_schema",
            ):
                if name in tool_names:
                    schema_tool = name
                    break
            if not schema_tool:
                for name in tool_names:
                    if "schema" in name.lower() or "table" in name.lower():
                        schema_tool = name
                        break
        if not schema_tool:
            return (
                "Schema tool not found. Available tools: "
                + ", ".join(tool_names)
                + ". Using table list from execute_query on information_schema."
            )
        args: dict[str, Any] = {}
        # For pg_manage_schema, use the supported 'get_info' operation.
        if schema_tool == "pg_manage_schema":
            args = {"operation": "get_info"}
        elif "schema_management" in schema_tool or "get_schema" in schema_tool:
            args = {"operation": "list_tables"}
        result = await self.call_tool(schema_tool, args if args else None)
        text = _text_from_tool_result(result)
        if result.isError:
            logger.warning("Schema tool returned error: %s", text)
        return text if text else ("No schema content from tool " + schema_tool)

    async def execute_query(self, sql: str) -> tuple[list[str], list[list[Any]]]:
        """
        Execute a read-only SQL query via the MCP server.
        Returns (columns, rows).
        """
        tool_names = [t.name for t in await self.list_tools()]
        query_tool = None
        for name in ("execute_query", "execute_sql", "execute_query_tool"):
            if name in tool_names:
                query_tool = name
                break
        if not query_tool:
            for name in tool_names:
                if "query" in name.lower() or "execute" in name.lower():
                    query_tool = name
                    break
        if not query_tool:
            raise RuntimeError(
                "No execute/query tool found. Available: " + ", ".join(tool_names)
            )
        args: dict[str, Any] = {"query": sql}
        if "execute_query" in query_tool:
            args = {"operation": "select", "query": sql, "limit": 1000}
        result = await self.call_tool(query_tool, args)
        if result.isError:
            raise RuntimeError(_text_from_tool_result(result))
        columns, rows = _rows_from_tool_result(result)
        if not columns and result.content:
            columns = ["result"]
            rows = [[_text_from_tool_result(result)]]
        return (columns, rows)

    async def cleanup(self) -> None:
        """Close the session and server process."""
        await self._exit_stack.aclose()
        self._session = None
        self._tools_cache = None

    async def __aenter__(self) -> "PostgresMCPClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.cleanup()


# ---------------------------------------------------------------------------
# Convenience functions: one-shot use (one session per call).
# For get_schema + execute_query in one flow, use the class and one client.
# ---------------------------------------------------------------------------


# async def postgres_mcp_session(connection_string: Optional[str] = None):
#     """
#     Async context manager: start Postgres MCP server and yield a ClientSession.
#     Prefer PostgresMCPClient for session reuse and get_schema/execute_query.
#     """
#     async with PostgresMCPClient(connection_string) as client:
#         yield client.session()


# async def get_schema(connection_string: Optional[str] = None) -> str:
#     """
#     Get schema information from the Postgres MCP server (one-shot).
#     For multiple operations, use PostgresMCPClient and call client.get_schema().
#     """
#     async with PostgresMCPClient(connection_string) as client:
#         return await client.get_schema()


# async def execute_query(
#     sql: str,
#     connection_string: Optional[str] = None,
# ) -> tuple[list[str], list[list[Any]]]:
#     """
#     Execute a read-only SQL query via the Postgres MCP server (one-shot).
#     For get_schema + execute_query in one flow, use one PostgresMCPClient.
#     """
#     async with PostgresMCPClient(connection_string) as client:
#         return await client.execute_query(sql)
