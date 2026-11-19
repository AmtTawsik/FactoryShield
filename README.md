# FactoryShield AI

FactoryShield AI is a safety and compliance management system for small and medium-sized garment factories in Bangladesh.

It brings factory information, safety inspections, workplace incidents, and corrective actions together in one place. Factory teams can keep track of inspection findings, follow up on unresolved issues, and monitor safety activities across their factories.

The system also includes an AI assistant that works with live factory records and a collection of safety-related documents. Users can ask questions in Bangla or English and get answers based on the available data and documents.

## Links

| | |
|---|---|
| Git repository | https://github.com/AmtTawsik/FactoryShield |
| Video (Google Drive) | Not published yet |
| Live API (Swagger) | https://factoryshield-api-n0ih.onrender.com/docs |
| Web app | https://factory-shield.vercel.app |

The API runs on a free Render plan. If it has been idle, the first request (API or web app sign-in) can take about a minute while the server starts.

## Demo accounts

These accounts work on the live web app and the live API.

> **Note:** These accounts and passwords are shared only for evaluation. The passwords will be changed and the repository will be made private after the evaluation.

| Role | Organization | Name | Email | Password | Factories |
|---|---|---|---|---|---|
| Platform administrator | – | Abdullah Al Mubin | amttawsik.cse@gmail.com | Platform@2026 | None (manages organizations and the shared library) |
| Admin | Meghna Apparel Group | Farhana Rahman | farhana@meghnagroup.com | Admin@2026 | All 6 |
| Staff | Meghna Apparel Group | Mahmudul Hasan | mahmudul@meghnagroup.com | Staff@2026 | Sonali Thread Knit Composite, Bangshi Denim Works |
| Staff | Meghna Apparel Group | Nusrat Jahan | nusrat@meghnagroup.com | Staff@2026 | Padma Stitch Apparels |
| Staff | Meghna Apparel Group | Arif Hossain | arif@meghnagroup.com | Staff@2026 | Karnaphuli Seamline Garments, Turag Weave Fashions, Dhaleshwari Sweaters |
| Admin | Shapla Knitwear Ltd | Sabrina Akter | sabrina@shaplaknit.com | Admin@2026 | Both |
| Staff | Shapla Knitwear Ltd | Rakib Hossain | rakib@shaplaknit.com | Staff@2026 | Shapla Knitwear Ashulia Unit, Shapla Knitwear Tongi Unit |

Admins can create, edit and delete records. Staff can only view the factories assigned to them. Each organization sees only its own data.

## The problem

Many small and medium-sized garment factories still rely on paper registers and Excel sheets to manage fire, electrical, and building safety records.

This makes it difficult to keep track of inspection findings and follow up on problems. Corrective actions can miss their deadlines, incident reports may not receive proper attention, and important records can be difficult to find when needed.

These gaps can create problems during buyer audits, lead to penalties from the Department of Inspection for Factories and Establishments (DIFE), and, more importantly, put workers at risk.

FactoryShield is designed to make these records easier to manage and give factory teams a clearer picture of what needs attention.

## Who it is for

FactoryShield is intended for owners and compliance teams managing small groups of garment factories.

- **Buyer:** Factory owners and compliance managers responsible for groups with 1 to 10 factory units, mainly in Dhaka, Gazipur, Narayanganj, and Chattogram.
- **Daily users:** Compliance managers who use the admin account and safety officers who manage their assigned factories through staff accounts.

Each company operates within its own organization in FactoryShield. Its users can only access their organization's records, and staff members can only see the factories assigned to them.

## Main features

- **Factory management:** Maintain factory details, including licence numbers, addresses, districts, worker counts, floor counts, and contact information.
- **Safety inspections:** Record inspections across fire, electrical, structural, chemical, PPE, and general safety categories. Each inspection can include a score and findings.
- **Incident reporting:** Record workplace incidents with their type, severity, injury details, and current status.
- **Corrective actions:** Create actions linked to inspections or incidents, assign due dates, and track overdue items.
- **Dashboard:** View open incidents, overdue corrective actions, inspection score trends, and upcoming inspections.
- **User and organization management:** Manage admin and staff accounts, assign factories, register new companies, and manage organizations through a platform administrator account.
- **AI assistant:** Ask questions about factory records and safety requirements. The assistant can retrieve live data through tools, search safety documents, and provide answers with their sources. Conversations are saved for later reference.
- **Document library:** Keep shared safety documents alongside documents uploaded by individual companies. Supported formats include PDF, TXT, and Markdown.
- **MCP server:** Allow compatible AI clients to access FactoryShield data through the Model Context Protocol.
- **Web application:** A Next.js frontend for managing the system. More details are available in [frontend/README.md](frontend/README.md).
- **CSV export:** Export factory, inspection, incident, and corrective action records.

## Technology stack

| Part | Technology |
|---|---|
| API | Python 3.12, FastAPI, Pydantic, pydantic-settings, uv |
| Database | PostgreSQL 16 with pgvector, async SQLAlchemy 2 (asyncpg), Alembic |
| Authentication | JWT (PyJWT), Argon2 password hashing |
| AI assistant | Groq (`openai/gpt-oss-120b`) or OpenRouter, through the OpenAI-compatible API |
| Embeddings | Hugging Face Text Embeddings Inference with `intfloat/multilingual-e5-small` (384 dimensions) |
| MCP | Official MCP Python SDK, Streamable HTTP and stdio |
| Web app | Next.js (App Router), TypeScript, Tailwind CSS, SWR, Recharts |
| Containers | Docker, Docker Compose |
| Hosting | Render (API), Neon (PostgreSQL), Hugging Face Spaces (embeddings), Vercel (web app) |

## Architecture

The browser communicates with the Next.js application, which handles API requests on the server side. Other clients, including Swagger, curl, and MCP clients, can access the backend through their respective interfaces.

The main request flow looks like this:

```text
Browser ──> Next.js web app ──(server side, Bearer token)──┐
Swagger / curl ────────────────────────────────────────────┤
MCP client ──> /mcp (HTTP) or stdio ───────────────────────┤
                                                           v
                                  FastAPI  /api/v1  (controllers)
                                    │ Depends: database session, current user, role, factory scope
                                    v
                                  services ──> repositories ──> PostgreSQL + pgvector
                                    │
                                    ├──> app/integrations/llm/         ──> Groq or OpenRouter
                                    └──> app/integrations/embeddings/  ──> embedding service (TEI)
```

The backend is organized into separate feature modules under `app/modules/`. Each module handles a specific part of the application:

- `auth`
- `organizations`
- `users`
- `factories`
- `inspections`
- `incidents`
- `corrective_actions`
- `dashboard`
- `knowledge`
- `chat`

A module generally contains its controller, service, repository, schemas, models, and dependencies.

Controllers handle incoming HTTP requests, services contain the application logic, and repositories are responsible for database queries. FastAPI `Depends` is used to connect these parts and provide the required dependencies.

Data access is restricted by both organization and user permissions. Every query is scoped to the user's organization, and staff members are further limited to their assigned factories.

The same access rules apply across the REST API, dashboard, AI assistant tools, document search, and MCP server.

## Requirements

Before running the project, make sure you have:

- Docker and Docker Compose v2.
- Python 3.12 and [uv](https://docs.astral.sh/uv/) if you want to run parts of the backend outside Docker.
- Node.js 20 or newer for local frontend development.
- A Groq or OpenRouter API key for the AI assistant. The rest of the application can run without one.

## Running with Docker

### 1. Set up the environment

Clone the repository and move into the project directory:

```bash
git clone https://github.com/AmtTawsik/FactoryShield.git
cd FactoryShield
cp .env.example .env
```

Open `.env` and configure the required values.

| Variable | Description |
|---|---|
| `POSTGRES_PASSWORD` | Password for PostgreSQL. Use letters and numbers because this value is also included in the database URL. |
| `DATABASE_URL` | Database connection string with the same password. This is used when running the API directly on your machine. |
| `JWT_SECRET_KEY` | Secret key used for JWT authentication. It should contain at least 32 random characters. |
| `SEED_SUPER_ADMIN_PASSWORD` | Password for the demo platform administrator account (minimum 8 characters). |
| `SEED_ADMIN_PASSWORD` | Password for the demo organization admin accounts (minimum 8 characters). |
| `SEED_STAFF_PASSWORD` | Password for the demo staff accounts (minimum 8 characters). |
| `LLM_PROVIDER` | AI assistant provider: `groq` (default) or `openrouter`. |
| `GROQ_API_KEY` / `OPENROUTER_API_KEY` | API key for the selected provider. Optional, but chat requests return 503 without a valid key. The model is configured through `GROQ_MODEL` or `OPENROUTER_MODEL`. |
| `CORS_ORIGINS` | Comma-separated list of browser origins allowed to call the API directly. Optional. The web app does not need this because its server communicates with the API. |

The remaining settings in `.env.example` already have working defaults, with comments explaining their purpose.

The API will not start if `DATABASE_URL` or `JWT_SECRET_KEY` is missing or invalid.

To generate a JWT secret, you can use:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

The `.env` file is excluded from Git and the Docker build context, so your local secrets are not included in the repository or Docker image.

### 2. Start the application

Once the environment file is ready, start the project:

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
| `frontend` | `factoryshield-frontend` | Next.js web application. | `3000` |

### Startup process

Docker Compose starts the services in the following order:

1. PostgreSQL starts and waits until its health check passes.
2. The migration service applies pending database migrations.
3. The API starts after the migrations complete successfully.
4. The frontend starts once the API becomes healthy.

If a migration fails, the API will not start. Check the migration logs to find the cause:

```bash
docker compose logs migrate
```

The API also provides a health check at `GET /api/v1/health`. It reports a healthy status only when the database is reachable.

On the first run, the embedding service downloads the `intfloat/multilingual-e5-small` model, which is approximately 500 MB. This can take a few minutes. On later runs, Docker loads the model files from the existing volume.

The API does not wait for the embedding service to become healthy. Until it is ready, chat can still work with factory records, but document search will be unavailable. Document ingestion also requires the embedding service to be running.

### 3. Verify the application

Check the status of the containers:

```bash
docker compose ps
```

Once everything is running, you should see:

- `db`: healthy
- `embeddings`: healthy
- `api`: healthy
- `frontend`: healthy
- `migrate`: exited (0)

You can also check the API directly:

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:

```json
{"status":"ok","database":"ok"}
```

Once the services are ready, you can access:

- API documentation (Swagger): http://localhost:8000/docs
- Web application: http://localhost:3000

### Database migrations

Database migrations are applied automatically when you start the project with Docker Compose.

If you need to run or inspect them manually, use these commands:

```bash
# Apply pending migrations
docker compose run --rm migrate

# Check the current database revision
docker compose exec api alembic current

# Roll back the last migration
docker compose exec api alembic downgrade -1
```

When you change the database models, create a migration from your host machine:

```bash
uv run alembic revision --autogenerate -m "describe your changes"
```

Review the generated migration before committing it with the related code.

### Loading demo data and safety documents

FactoryShield includes seed data for testing the application with sample users, organizations, factories, and records.

Run the seed script:

```bash
docker compose exec api python -m scripts.seed
```

The script creates the platform administrator:

`amttawsik.cse@gmail.com`

It also creates two demo organizations:

- **Meghna Apparel Group:** Admin `farhana@meghnagroup.com`, three staff accounts, and six factories.
- **Shapla Knitwear Ltd:** Admin `sabrina@shaplaknit.com`, one staff account, and two factories.

Account passwords are taken from `.env`.

Each organization can only access its own records. The platform administrator manages organizations and the shared document library but cannot view individual organizations' records.

New companies can also register through the web application.

The seed script is safe to run more than once and will not create duplicate demo records.

To add the sample safety documents to the knowledge base, run:

```bash
docker compose exec api python -m scripts.ingest_knowledge
```

Make sure the embedding service is healthy before running the ingestion script.

Documents that have not changed are skipped, so you can run the script again when needed.

The source documents and their licence information are listed in `knowledge/SOURCES.md`.

### Stopping the application

To stop the running containers:

```bash
docker compose down
```

Your database and downloaded embedding model files will remain in their Docker volumes, so you can use them again when you restart the application.

To remove the containers and their associated volumes as well, run:

```bash
docker compose down -v
```

This also deletes the stored database and downloaded model files. Make sure you do not need that data before running the command.

### Running the API without Docker

For backend development, you can run the API directly on your machine while keeping PostgreSQL and the embedding service inside Docker.

Start the required services:

```bash
docker compose up -d db embeddings
```

Install the dependencies and apply the database migrations:

```bash
uv sync
uv run alembic upgrade head
```

Start the development server:

```bash
uv run uvicorn app.main:app --reload
```

To run the web application locally, follow the instructions in [frontend/README.md](frontend/README.md).

## API examples

All API endpoints are available under `/api/v1`.

The examples below use the local API and a demo admin account. Except for registration, login, and the health check, requests require an access token obtained through login.

### Authentication

Company registration creates a new organization along with its first admin account:

```bash
# Register a company (201)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"organization_name": "Rupali Apparel Group", "full_name": "Nasrin Sultana", "email": "nasrin@rupali.example", "password": "Rupali2026"}'
```

To sign in, send the user's email and password:

```bash
# Login and receive a JWT
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "farhana@meghnagroup.com", "password": "<SEED_ADMIN_PASSWORD>"}'
```

A successful login returns a response similar to:

```json
{"access_token": "eyJhbGciOi...", "token_type": "bearer", "expires_in": 3600}
```

Use the returned access token for authenticated requests:

```bash
TOKEN=<access_token>

# Get the current user's details, including role and organization
curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer $TOKEN"
```

An incorrect email and an incorrect password return the same `401` response.

Tokens expire after the configured `JWT_EXPIRE_MINUTES` period. The user's role is loaded from the database on every request, so changes to a user's role or account status take effect immediately.

### CRUD operations (factories)

Factory records support create, list, retrieve, update, and delete operations.

Inspections (`/inspections`), incidents (`/incidents`), and corrective actions (`/corrective-actions`) follow the same general API pattern.

```bash
# Create a factory (admin only): 201
curl -X POST http://localhost:8000/api/v1/factories \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Sonali Thread Knit Composite Ltd", "license_number": "FL-GZP-04512", "address": "Plot 14, Konabari BSCIC Industrial Area", "district": "Gazipur", "worker_count": 1450, "floor_count": 6, "contact_person": "Kamrul Islam", "contact_phone": "01711-234567"}'

# List factories with search, filters and pagination
curl "http://localhost:8000/api/v1/factories?search=sonali&district=Gazipur&page=1&size=20" \
  -H "Authorization: Bearer $TOKEN"

# Get a single factory
curl http://localhost:8000/api/v1/factories/1 -H "Authorization: Bearer $TOKEN"

# Update selected fields
curl -X PATCH http://localhost:8000/api/v1/factories/1 \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"worker_count": 1520}'

# Delete a factory (204)
curl -X DELETE http://localhost:8000/api/v1/factories/1 -H "Authorization: Bearer $TOKEN"
```

The API uses the following status codes:

| Status | Meaning |
|---|---|
| `201` | Resource created |
| `204` | Resource deleted |
| `401` | Missing or invalid access token |
| `403` | User does not have the required role |
| `404` | Resource not found or belongs to another organization |
| `409` | Conflict, such as a duplicate licence number |
| `422` | Invalid input |

Error responses do not expose stack traces or database messages.

### Chat

You can start a conversation with the AI assistant through the chat endpoint.

For example:

```bash
# Start a conversation, optionally about a specific factory
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message": "Which corrective actions are overdue?"}'
```

A response looks like this:

```json
{
  "conversation_id": 12,
  "factory_id": null,
  "reply": "Three actions are overdue ...",
  "tools_used": ["get_overdue_corrective_actions"],
  "sources": []
}
```

To continue the conversation, send its ID with the next message:

```bash
# Continue an existing conversation
# Earlier messages are loaded from the database
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"conversation_id": 12, "message": "Which of them is the most urgent?"}'

# List saved conversations
curl http://localhost:8000/api/v1/chat/conversations -H "Authorization: Bearer $TOKEN"

# Get a specific conversation
curl http://localhost:8000/api/v1/chat/conversations/12 -H "Authorization: Bearer $TOKEN"
```

If a client manages its own conversation history, it can also send `previous_messages` when starting a conversation. This should be a list of messages in the following format:

```json
[
  {"role": "user", "content": "..."},
  {"role": "assistant", "content": "..."}
]
```

Without a valid API key for the selected LLM provider, chat requests return `503`.

## How the assistant uses tools

The chat implementation is located in `app/modules/chat/`. It communicates with the selected language model through `app/integrations/llm/`.

A system prompt defines the assistant's role in factory safety and compliance. It also sets clear limits: answers should be based on available factory records and safety documents rather than invented information.

The assistant has access to three tools backed by the database:

| Tool | What it returns |
|---|---|
| `get_factory_inspection_summary` | Inspection counts by status and category, scores, recent findings, and upcoming inspections for a factory. |
| `get_overdue_corrective_actions` | Overdue actions, including how many days they are overdue and who is responsible. Results can be filtered by factory or priority. |
| `search_recent_safety_incidents` | Recent incidents within the requested number of days, with optional filters for factory, severity, status, or keyword. |

When a user asks a question, the model decides whether it needs additional information from one of these tools.

If a tool is needed, the API validates its arguments and runs the corresponding query through the normal application services. The result is then passed back to the model, which uses it to prepare the response.

Tool access follows the same permission rules as the rest of the application. For example, a staff member can only retrieve information about their assigned factories.

The tool-calling loop allows up to 4 rounds, with a maximum of 5 calls per round. The response also includes the tools used in the `tools_used` field.

## How document search (RAG) works

FactoryShield uses retrieval-augmented generation (RAG) to let the assistant answer questions using safety documents.

The process has four main steps.

### 1. Document ingestion

The ingestion process starts with `scripts/ingest_knowledge.py`, which reads the document list from `knowledge/manifest.toml`.

It extracts text from PDF, TXT, and Markdown files, then splits the content into smaller chunks of up to 900 characters, using headings and paragraphs to keep related content together.

Each chunk is converted into an embedding using `multilingual-e5-small` and stored in the `knowledge_chunks` table. The database uses a pgvector `vector(384)` column for these embeddings.

Admins can also upload documents through the web application. Uploaded documents go through the same ingestion process.

### 2. Document search

When a user sends a chat message, the question is converted into an embedding.

pgvector then searches for the most similar document chunks that the user is allowed to access. These can come from the shared document library, the user's organization, or their assigned factories.

### 3. Generating an answer

Only chunks with a similarity score of at least `RAG_MIN_SCORE` (0.80) are passed to the language model.

The model receives the relevant content along with its title and status, which indicates whether it is official text or general guidance.

The generated answer includes its supporting documents in the `sources` field. Each source contains its title, authority, URL, and verification date.

### 4. When no relevant document is found

If no document chunk meets the similarity threshold, the assistant is informed that the search did not find relevant material.

Instead of making up an answer, it responds that the available documents do not cover the question.

If the embedding service is unavailable, the assistant can still answer questions using live factory records, but document search will not be available.

The embedding model supports both Bangla and English. This means users can ask questions in Bangla and retrieve relevant English documents, or ask in English and find relevant Bangla content.

## MCP Server

FactoryShield also provides an MCP server for connecting external AI clients to factory data through the Model Context Protocol.

It uses the same application services and PostgreSQL database as the REST API. Access follows the authenticated user's permissions. Staff members can only access their assigned factories, while admins can access all factories within their own organization.

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

Every request must include a valid FactoryShield access token.

First, log in through the authentication endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "..."}'
```

The response contains an `access_token`. Copy it and include it in the Authorization header when connecting to the MCP server.

Requests without a token, with an expired token, or from an inactive user receive a `401` response.

Token expiration is controlled by the `JWT_EXPIRE_MINUTES` setting. Log in again if you need a new token.

#### Using MCP Inspector

Start MCP Inspector:

```bash
npx @modelcontextprotocol/inspector
```

Configure the connection with these values:

- Transport: `Streamable HTTP`
- URL: `http://localhost:8000/mcp`
- Header: `Authorization: Bearer <access_token>`

#### Connecting with a Python client

The MCP SDK can also be used to connect from a Python application:

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

Add the following setting to your `.env` file:

```env
MCP_STDIO_USER_EMAIL=you@example.com
```

Use the email address of an existing, active FactoryShield user. The server uses this account to determine which factory records the client can access.

Start the server from the `FactoryShield` project directory:

```bash
uv run python -m app.mcp.stdio
```

The database must be running before you start the server. If the configured user does not exist or is inactive, the server exits and prints an error to stderr.

#### Client configuration

Most desktop MCP clients support a JSON configuration similar to this:

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

You can also launch MCP Inspector directly with the stdio configuration:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/FactoryShield run python -m app.mcp.stdio
```

### Error handling

The MCP server validates incoming requests and checks whether the authenticated user can access the requested factory.

Common errors include:

- **Invalid arguments:** Incorrect argument types, unsupported priority values, or values outside the allowed range return a tool error (`is_error: true`).
- **Factory not found:** Returned when the requested factory does not exist or is outside the user's access scope.
- **Resource and prompt errors:** Resource and prompt requests return MCP errors containing the corresponding messages.
- **Database connection issues:** If PostgreSQL is temporarily unavailable, the server returns:

  `The database is temporarily unavailable, please try again shortly`

These checks ensure that MCP clients follow the same data access restrictions as the main application.

## Testing

With Docker running and the demo data loaded, you can test the main application features.

1. Open http://localhost:8000/docs. Call `POST /api/v1/auth/login`, click **Authorize**, and paste the returned access token. You can then try the available API endpoints directly from Swagger.
2. Test the role restrictions. A staff account should receive `403` when trying to create, update, or delete records, and `404` when requesting a factory that has not been assigned to it.
3. Try the AI assistant with questions such as:
   - "Which corrective actions are overdue?" — this should use a database tool.
   - "What does the Labour Act say about fire exits?" — this should search the safety documents and return supporting sources.
4. Connect to the MCP server using MCP Inspector and try the available tools as described above.

To check the frontend, run:

```bash
cd frontend
npm ci
npm run lint
npx tsc --noEmit
npm run build
```

## Deployment

The current deployment setup uses free-tier services:

- Render for the API.
- Neon for PostgreSQL.
- Hugging Face Spaces for the embedding service.
- Vercel for the web application.

No secrets are stored in the Git repository. Each service gets its configuration through its own dashboard.

### 1. Database (Neon)

1. Create a Neon project in a region close to the Render service. The current `render.yaml` uses Render's Ohio region, so Neon's AWS US East 2 (Ohio) is a suitable choice.
2. Copy the **direct connection string** from Neon. Do not use the pooled connection string, as the pooler does not work with asyncpg's prepared statements.
3. Update the connection string to match the format expected by the API. Use `postgresql+asyncpg://` at the beginning and `?ssl=require` at the end. Remove `sslmode` and `channel_binding`.

   ```text
   postgresql+asyncpg://<user>:<password>@<host>/<database>?ssl=require
   ```

The first database migration enables the `vector` extension, which is supported by Neon.

### 2. Embedding service (Hugging Face Space)

1. Create a new Space using the **Gradio** SDK. Select the Blank template and **ZeroGPU** hardware, which is the free option. Set the Space to **private**.
2. Upload the three files from [deploy/embeddings-space/](deploy/embeddings-space/):
   - `app.py`
   - `requirements.txt`
   - `README.md`

   The Space serves the same model used by the Docker Compose `embeddings` service, through the same `/v1/embeddings` endpoint.
3. Wait until the Space status changes to **Running**. Its address will be `https://<space-host>` and is shown under "Embed this Space".
4. Create a Hugging Face access token with read permission. The API uses this token through the `EMBEDDING_API_KEY` setting.

A free Space goes to sleep after two days without requests. It wakes up when the next request arrives, which can take a minute or two.

During that time, chat can still work with factory records, but document search will be unavailable.

### 3. API (Render)

1. In Render, select **New → Blueprint** and choose this repository. The [render.yaml](render.yaml) file defines the `factoryshield-api` web service.
2. Add the required environment variables when prompted:

   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | The Neon connection URL from step 1 |
   | `GROQ_API_KEY` | Your Groq API key |
   | `EMBEDDING_BASE_URL` | `https://<space-host>/v1` |
   | `EMBEDDING_API_KEY` | Your Hugging Face access token |
   | `CORS_ORIGINS` | Leave empty, or provide browser origins that need direct API access |

   Render generates `JWT_SECRET_KEY` automatically. The remaining settings are loaded from `render.yaml`.

3. Each time the service starts, [scripts/start.sh](scripts/start.sh) applies pending database migrations and then starts the API on Render's assigned port. Render checks the service through `/api/v1/health`.
4. Once deployment is complete, open:

   `https://<service>.onrender.com/docs`

   This takes you to the live Swagger documentation.

A free Render service goes to sleep after 15 minutes without requests. The first request after it wakes up can take around a minute.

### 4. Demo data in production

The free Render plan does not provide shell access. Because of that, the seed and document ingestion scripts need to be run from your local machine against the production database and embedding service.

Environment variables exported in the shell take priority over values in `.env`.

Set the production values first:

```bash
export DATABASE_URL="postgresql+asyncpg://<user>:<password>@<host>/<database>?ssl=require"
export EMBEDDING_BASE_URL="https://<space-host>/v1"
export EMBEDDING_API_KEY="<hugging face token>"
export SEED_SUPER_ADMIN_PASSWORD="<new password>"
export SEED_ADMIN_PASSWORD="<new password>"
export SEED_STAFF_PASSWORD="<new password>"
```

Then run the scripts:

```bash
uv run python -m scripts.seed
uv run python -m scripts.ingest_knowledge
```

Use passwords different from your local demo passwords. The production API is publicly accessible, so default or reused passwords should not be used.

### 5. Web app (Vercel)

1. Import the repository into Vercel and set the **Root Directory** to `frontend`.
2. Add the following environment variables:

   | Variable | Value |
   |---|---|
   | `API_BASE_URL` | `https://<service>.onrender.com/api/v1` |
   | `COOKIE_SECURE` | `true` |

3. Deploy the application.

The Next.js server communicates with the API directly. The browser does not send requests to Render, so the web application does not need a CORS configuration for this setup.

## Business model

FactoryShield follows a subscription model based on the number of factory units.

- **Monthly subscription:** BDT 3,000 per factory.
- **Example:** A company managing five factories pays BDT 15,000 per month.
- **One-time onboarding fee:** Covers importing existing Excel records, setting up user accounts and factory assignments, and adding the company's own safety procedures to the document library.

### Why a factory would pay for it

Paper registers and Excel sheets are useful for keeping records, but they do not provide a reliable way to track overdue actions, connect incidents with their corrective measures, or quickly find relevant safety information.

Preparing for a buyer audit can also mean spending days searching through different files and records.

Larger compliance platforms are often designed for major exporters and may be too expensive for smaller factories.

FactoryShield aims to provide a simpler way to manage these activities. Factory teams can keep their records together, see which issues need attention, and ask safety-related questions in Bangla or English using their own records and the available safety documents.

## Future improvements

Some features that could be added in future versions include:

- Email or SMS reminders before corrective action deadlines.
- Photo and file attachments for inspections and incidents.
- Login rate limiting and revocable sessions using refresh tokens.
- Options for deleting organizations and conversations, along with an audit log of changes.
- More verified Bangladesh-specific safety documents, including the Bangladesh National Building Code, fire service rules, and buyer codes of conduct.
- A mobile-friendly inspection checklist for safety officers working on the factory floor.
- Monthly PDF reports for each factory, suitable for sharing with buyers and auditors.