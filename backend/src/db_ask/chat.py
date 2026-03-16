"""Chat loop: natural language -> Claude with Postgres MCP tools -> final answer."""

from anthropic.types import MessageParam

from db_ask.claude import Claude
from db_ask.mcp_client import PostgresMCPClient
from db_ask.tools import execute_tool_requests, get_tools_for_claude


SYSTEM_PROMPT_TEMPLATE = """You are a helpful assistant that answers questions about a PostgreSQL database for a litterbox monitoring system.

Use the provided MCP tools to inspect the schema and run SQL when needed. Prefer read-only queries (SELECT). Only use the tools that are available.

Database schema information (for reference; you can also use the schema/table tools if available):

{schema}

Answer the user's question concisely. When you run a query, summarize the results in natural language."""


class DbChat:
    """Single-turn or multi-turn chat using Claude and Postgres MCP tools."""

    def __init__(
        self,
        client: PostgresMCPClient,
        claude: Claude,
        schema: str,
    ):
        self.client = client
        self.claude = claude
        self.schema = schema
        self.messages: list[MessageParam] = []

    def _system_prompt(self) -> str:
        return SYSTEM_PROMPT_TEMPLATE.format(schema=self.schema)

    async def run(self, query: str) -> str:
        """Process one user query; may involve multiple tool calls. Returns final assistant text."""
        self.messages.append({"role": "user", "content": query})
        tools = await get_tools_for_claude(self.client)

        while True:
            response = self.claude.chat(
                messages=self.messages,
                system=self._system_prompt(),
                tools=tools,
                temperature=0.0,
            )
            self.claude.add_assistant_message(self.messages, response)

            if response.stop_reason == "tool_use":
                print("  (running tools…)")
                tool_results = await execute_tool_requests(
                    self.client, response
                )
                self.claude.add_user_message(self.messages, tool_results)
            else:
                return self.claude.text_from_message(response)
