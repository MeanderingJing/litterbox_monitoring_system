"""Tool listing and execution for Postgres MCP client (Anthropic tool format)."""

import json
from typing import Any, Literal

from anthropic.types import Message, ToolResultBlockParam

from db_ask.mcp_client import PostgresMCPClient, _text_from_tool_result


def _tool_result_content(result: Any) -> str:
    """Extract string content from MCP CallToolResult for tool_result block."""
    return _text_from_tool_result(result)


def _build_tool_result_part(
    tool_use_id: str,
    text: str,
    status: Literal["success"] | Literal["error"],
) -> ToolResultBlockParam:
    return {
        "tool_use_id": tool_use_id,
        "type": "tool_result",
        "content": text,
        "is_error": status == "error",
    }


async def get_tools_for_claude(client: PostgresMCPClient) -> list[dict]:
    """Return tools from the Postgres MCP client in Anthropic tool format."""
    mcp_tools = await client.list_tools()
    return [
        {
            "name": t.name,
            "description": t.description or "",
            "input_schema": t.inputSchema or {},
        }
        for t in mcp_tools
    ]


async def execute_tool_requests(
    client: PostgresMCPClient,
    message: Message,
) -> list[ToolResultBlockParam]:
    """Execute tool_use blocks from the assistant message using the Postgres MCP client."""
    tool_requests = [
        block for block in message.content if block.type == "tool_use"
    ]
    results: list[ToolResultBlockParam] = []
    for tr in tool_requests:
        tool_use_id = tr.id
        tool_name = tr.name
        tool_input = tr.input or {}

        try:
            result = await client.call_tool(tool_name, tool_input)
            content = _tool_result_content(result) if result else "No result"
            if not content and result and result.structuredContent is not None:
                content = json.dumps(result.structuredContent, indent=2)
            status: Literal["success"] | Literal["error"] = (
                "error" if (result and result.isError) else "success"
            )
            results.append(
                _build_tool_result_part(tool_use_id, content, status)
            )
        except Exception as e:
            results.append(
                _build_tool_result_part(
                    tool_use_id,
                    json.dumps({"error": str(e)}),
                    "error",
                )
            )
    return results
