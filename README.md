# FactoryShield AI

FactoryShield AI is a safety and compliance management system built for small and medium-sized garment factories in Bangladesh.

It helps factory teams manage their factory information, safety inspections, workplace incidents, and corrective actions from a single platform. The system also includes an AI assistant that can answer questions using factory records and a collection of safety-related documents.

## Running with Docker

You will need Docker and Docker Compose v2 installed on your machine.

### 1. Set up the environment

Copy the example environment file:

```bash
cp .env.example .env
```

Open `.env` and provide the required values.

| Variable | Description |
|---|---|
| `POSTGRES_PASSWORD` | Password for PostgreSQL. Use letters and numbers because this value is also included in the database URL. |
| `DATABASE_URL` | Database connection string with the same password. This is used when running the API directly on your machine. |
| `JWT_SECRET_KEY` | Secret key used for JWT authentication. It should contain at least 32 random characters. |
| `SEED_SUPER_ADMIN_PASSWORD` | Password for the demo platform administrator account (minimum 8 characters). |
| `SEED_ADMIN_PASSWORD` | Password for the demo organization admin accounts (minimum 8 characters). |
| `SEED_STAFF_PASSWORD` | Password for the demo staff accounts (minimum 8 characters). |
| `LLM_PROVIDER` | AI assistant provider: `groq` (default) or `openrouter`. |
| `GROQ_API_KEY` / `OPENROUTER_API_KEY` | API key of the chosen provider (optional). The application works without it, but chat requests will return a 503 response. The model is set with `GROQ_MODEL` or `OPENROUTER_MODEL`. |

To generate a secure JWT secret, you can run:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

The `.env` file is excluded from Git and the Docker build context, so your local secrets are not included in the repository or Docker image.

### 2. Start the application

Once the environment file is ready, run:

```bash
docker compose up --build
```

Docker Compose starts the following services:

| Service | Container | Purpose | Host port |
|---|---|---|---|
| `db` | `factoryshield-db` | PostgreSQL 16 with pgvector. Database files are stored in the `factoryshield_postgres_data` volume. | `127.0.0.1:5440` |
| `embeddings` | `factoryshield-embeddings` | Runs Text Embeddings Inference using `intfloat/multilingual-e5-small`. Model files are kept in the `factoryshield_embedding_models` volume. | `127.0.0.1:8091` |
| `migrate` | `factoryshield-migrate` | Applies database migrations using Alembic and exits when finished. | – |
| `api` | `factoryshield-api` | FastAPI backend providing the REST API (`/api/v1`) and MCP server (`/mcp`). | `8000` |

### Startup process

The services start in a specific order:

1. PostgreSQL starts and waits until its health check passes.
2. The migration service applies pending database migrations.
3. Once migrations finish successfully, the API starts.

If a migration fails, the API will not start. You can check the migration logs with:

```bash
docker compose logs migrate
```

The API also has a health check at `GET /api/v1/health`. It reports the application as healthy only when the database is reachable.

The embedding service needs a little extra time on its first run. It downloads the `intfloat/multilingual-e5-small` model, which is approximately 500 MB. Subsequent runs use the downloaded files from the Docker volume.

The API does not wait for the embedding service to become ready. Until it passes its health check, chat requests can still run without document retrieval, while document ingestion will report that the embedding service is unavailable.

### 3. Verify the application

Check the running containers:

```bash
docker compose ps
```

The expected status is:

- `db`: healthy
- `embeddings`: healthy
- `api`: healthy
- `migrate`: exited (0)

You can also check the API directly:

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:

```json
{"status":"ok","database":"ok"}
```

API documentation is available at:

http://localhost:8000/docs

### Database migrations

Migrations are applied automatically whenever you start the application with Docker Compose.

If you need to manage them manually, use the following commands:

```bash
# Apply pending migrations
docker compose run --rm migrate

# Check the current database revision
docker compose exec api alembic current

# Roll back the last migration
docker compose exec api alembic downgrade -1
```

When you make changes to the database models, create a new migration from your host machine:

```bash
uv run alembic revision --autogenerate -m "describe your changes"
```

Review the generated migration before committing it along with the related code.

### Loading demo data and safety documents

FactoryShield includes scripts for adding sample users, factories, inspection records, and safety documents.

Run the seed script:

```bash
docker compose exec api python -m scripts.seed
```

This creates the platform administrator `amttawsik.cse@gmail.com` and two demo organizations:

- **Meghna Apparel Group**: admin `farhana.rahman@factoryshield.demo`, three staff accounts and six factories.
- **Shapla Knitwear Ltd**: admin `sabrina.akter@shapla.demo`, one staff account and two factories.

The passwords come from `.env`. Each organization sees only its own records; the platform administrator manages organizations and the shared document library and cannot see any organization's records. New companies can also sign up from the web app.

The seed script can be run more than once without creating duplicate demo records.

To add the sample safety documents to the knowledge base, run:

```bash
docker compose exec api python -m scripts.ingest_knowledge
```

Make sure the embedding service is healthy before running this command.

The ingestion script skips documents that have not changed, so it is safe to run again when needed.

The source documents and their licence information are listed in `knowledge/SOURCES.md`.

### Stopping the application

To stop all running containers:

```bash
docker compose down
```

This keeps the database and downloaded embedding model files for the next run.

If you also want to remove the stored database and model files, run:

```bash
docker compose down -v
```

Be careful with this command, as it permanently removes the data stored in those Docker volumes.

### Running the API without Docker

For local development, you can run the API directly on your machine while keeping PostgreSQL and the embedding service inside Docker.

Start the required services first:

```bash
docker compose up -d db embeddings
```

Then install the project dependencies and prepare the database:

```bash
uv sync
uv run alembic upgrade head
```

Start the development server:

```bash
uv run uvicorn app.main:app --reload
```

To run the test suite:

```bash
uv run pytest
```

---

## MCP Server

FactoryShield also provides an MCP server, allowing compatible AI clients to work with factory records through the Model Context Protocol.

It uses the same application services and PostgreSQL database as the REST API. Access is controlled by the authenticated user's permissions, so staff can only access factories assigned to them, while admins can access all factories of their own organization.

The server currently provides two tools, one resource, and one prompt.

### Available tools

| Name | Arguments | What it does |
|---|---|---|
| `get_factory_inspection_summary` | `factory_id` (required) | Returns inspection statistics by status and category, average and lowest scores, recent completed inspections with findings, and upcoming scheduled inspections. |
| `get_overdue_corrective_actions` | `factory_id`, `priority`, `limit` (all optional) | Lists overdue corrective actions, including how many days they are overdue and who is responsible for them. |

For `get_overdue_corrective_actions`:

- `priority` accepts `low`, `medium`, or `high`.
- `limit` accepts values from 1 to 50.
- The default limit is 20.

### Available resource

| Resource URI | Description |
|---|---|
| `factory://{factory_id}/overview` | Provides a text summary of the factory profile, recent inspection scores, and open record counts. |

### Available prompt

| Name | Argument | Description |
|---|---|---|
| `safety_inspection_review` | `factory_id` | Provides a review request containing the factory's current records and instructions for carrying out the review. |

### Connecting through HTTP

The MCP server uses Streamable HTTP with stateless JSON mode.

When the API is running, the endpoint is available at:

```text
http://localhost:8000/mcp
```

You must provide a valid FactoryShield access token with every request.

First, log in through the authentication endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "..."}'
```

The response includes an `access_token`. Copy that token and use it in the Authorization header when connecting to the MCP server.

Requests without a token, with an expired token, or from an inactive user will receive a `401` response.

Tokens expire according to the `JWT_EXPIRE_MINUTES` setting. Log in again to obtain a new token.

#### Using MCP Inspector

Start the inspector:

```bash
npx @modelcontextprotocol/inspector
```

Configure the connection as follows:

- Transport: `Streamable HTTP`
- URL: `http://localhost:8000/mcp`
- Header: `Authorization: Bearer <access_token>`

#### Connecting with a Python client

You can also connect to the server from a Python application using the MCP SDK:

```python
import asyncio

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client


async def main() -> None:
    http = httpx2.AsyncClient(
        headers={"Authorization": "Bearer <access_token>"}
    )

    async with Client(
        streamable_http_client(
            "http://localhost:8000/mcp",
            http_client=http
        )
    ) as client:
        result = await client.call_tool(
            "get_overdue_corrective_actions",
            {"priority": "high"}
        )
        print(result.structured_content)


asyncio.run(main())
```

### Connecting through stdio

For MCP clients running on the same machine, FactoryShield also supports the stdio transport.

Set `MCP_STDIO_USER_EMAIL` in your `.env` file:

```env
MCP_STDIO_USER_EMAIL=you@example.com
```

This must be the email address of an existing, active FactoryShield user. The server uses this account to determine which factory records the client can access.

Start the server from the `FactoryShield` project directory:

```bash
uv run python -m app.mcp.stdio
```

The database must be running before starting the server. If the configured user is missing or inactive, the server exits and prints an error to stderr.

#### Client configuration

Most desktop MCP clients accept a JSON configuration similar to this:

```json
{
  "mcpServers": {
    "factoryshield": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/FactoryShield",
        "run",
        "python",
        "-m",
        "app.mcp.stdio"
      ]
    }
  }
}
```

Replace `/path/to/FactoryShield` with the actual path to your project directory.

You can also start MCP Inspector directly with stdio:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/FactoryShield run python -m app.mcp.stdio
```

### Error handling

The MCP server handles common request and access errors and returns an explanation when something goes wrong.

- **Invalid arguments:** Requests with incorrect argument types, unsupported priority values, or values outside the allowed range return a tool error (`is_error: true`).
- **Factory not found:** The server returns an error if the requested factory does not exist or the current user does not have permission to access it.
- **Resource and prompt errors:** Resource and prompt requests return MCP errors with the same underlying messages.
- **Database connection issues:** If PostgreSQL is temporarily unavailable, the server returns:

  `The database is temporarily unavailable, please try again shortly`

These checks help keep factory data restricted to the records each user is allowed to access.