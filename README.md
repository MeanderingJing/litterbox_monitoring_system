# Overview of the Litterbox Monitoring System (LitterLog)
The litterbox monitoring system aims to address the challenge of tracking feline health and behavior patterns that are often invisible to pet owners. It targets health-conscious cat owners who need reliable, continuous monitoring to detect early signs of urinary tract infections (UTI) that first manifest through changes in litterbox usage patterns, as well as to track treatment progress and recovery by monitoring improvements in litterbox behavior during active UTI treatment.

The end-to-end solution combines edge computing (implemented as a litterbox simulator here), ETL processing, data analysis, and user-friendly web interface, delivering predictive health insights that can detect subtle deviations before they become apparent to cat owners.

This is an on-going project that is constantly being improved.

# System Diagram
![System Diagram](https://github.com/MeanderingJing/litterbox_monitoring_system/blob/main/LitterLog-high-level-diagram.png)

# Spin up the backend using Docker compose
`sudo docker compose up`
## What does the docker compose command do?
- Spin up the PostgreSQL database
- Spin up the RabbitMQ service
- Run the litterbox simulator in docker container, which produces litterbox usage data to RabbitMQ
- Run the data persister in docker container, which consumes messages from RabbitMQ and send it to the database

# Run backend flask app locally for development
Create a virtual environment first. The run: 
`pip install -r requirements.txt`
`flask run --port 8000`

Using `flask run` locally instead of Docker for this allows fast iteration, as I don't need to rebuild the container every time when there're code changes.

For production, use gunicorn and nginx (my own production server), a third-party platform-as-a-service (Heroku, Fly.io, etc), or a cloud provider.

# Run frontend locally for development
`npm install` 
`npm run dev`

For production, deploy to Vercel or a cloud provider.
## Litterlog Sign in Page
![Sign in Page](https://github.com/MeanderingJing/litterbox_monitoring_system/blob/main/Litterlog_sign_in.png)
## Litter Box Usage Visualization
![Litter Box Usage Visualization](https://github.com/MeanderingJing/litterbox_monitoring_system/blob/main/litterbox_usage_data_visualization.png)

### Natural-language database queries with Postgres MCP and Claude

The backend includes a **Postgres MCP (Model Context Protocol) client** and a **Claude AI integration** that let you query the litterbox PostgreSQL database in plain English from a CLI.

- **MCP server**: Uses the community Postgres MCP server (`@henkey/postgres-mcp-server`) and talks to it over stdio via `npx`. The client is implemented in `backend/src/db_ask/mcp_client.py` as `PostgresMCPClient`.
- **Claude integration**: `backend/src/db_ask/claude.py`, `chat.py`, and `tools.py` wrap the Anthropic Messages API and expose the Postgres MCP tools to Claude as tools it can call while answering questions.
- **CLI entry point**: `backend/src/db_ask/cli.py` provides a command-line interface that:
  - Starts the Postgres MCP server and fetches schema (via `pg_manage_schema` with `operation: "get_info"`).
  - Boots a Claude chat loop with that schema in the system prompt.
  - Lets you ask free-form questions like “What are the tables in the database?” or “How many litterbox events were recorded yesterday?”, and Claude decides when to call the MCP tools and returns a natural-language answer.

#### Configuration

Create a `.env` file under `backend/` with:

```env
ANTHROPIC_API_KEY=your_anthropic_key_here
CLAUDE_MODEL=claude-3-5-sonnet-20241022
POSTGRES_CONNECTION_STRING=postgresql://example_user:example_password@localhost:5435/example_db
```

`POSTGRES_CONNECTION_STRING` is optional; if omitted, the backend defaults to the same connection string used by the Docker Compose setup.

#### Running the CLI

From the `backend` directory:

```bash
poetry run db-ask
```

You’ll see it connect to the Postgres MCP server and fetch schema, then an interactive prompt:

```text
Ask DB >
```

Type a question about your data (for example, `What tables exist in this database?`) and press Enter. The tool will use the Postgres MCP tools to inspect schema and run safe, read-only queries, and Claude will summarize the results in concise, human-friendly text.