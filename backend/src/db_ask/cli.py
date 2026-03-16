"""
CLI for natural-language database queries via Postgres MCP and Claude.

Usage:
  poetry run db-ask
  poetry run python -m db_ask.cli

Requires .env or environment:
  ANTHROPIC_API_KEY  - Anthropic API key
  CLAUDE_MODEL       - e.g. claude-sonnet-4-20250514, claude-3-5-sonnet-20241022
  POSTGRES_CONNECTION_STRING or DATABASE_URL (optional; has default for local Docker)
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

from db_ask.chat import DbChat
from db_ask.claude import Claude
from db_ask.mcp_client import PostgresMCPClient, get_connection_string

load_dotenv()


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        print(f"Error: {name} must be set (e.g. in .env).", file=sys.stderr)
        sys.exit(1)
    return value


async def run_cli() -> None:
    _require_env("ANTHROPIC_API_KEY")
    claude_model = _require_env("CLAUDE_MODEL")

    connection_string = get_connection_string()
    print("Connecting to Postgres MCP and fetching schema…", flush=True)

    async with PostgresMCPClient(connection_string) as client:
        schema = await client.get_schema()
        claude = Claude(model=claude_model)
        chat = DbChat(client=client, claude=claude, schema=schema)

        print(
            "Ask questions about the database in natural language. "
            "Type 'quit' or 'exit' to stop.\n",
            flush=True,
        )
        while True:
            try:
                user_input = input("Ask DB > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye.")
                break
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                print("Bye.")
                break
            try:
                answer = await chat.run(user_input)
                print(f"\n{answer}\n")
            except Exception as e:
                print(f"Error: {e}\n", file=sys.stderr)


def main() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
