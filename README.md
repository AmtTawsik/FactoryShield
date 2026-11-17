# FactoryShield AI

Safety and compliance management for small and medium garment factories in Bangladesh.

FactoryShield keeps track of factories, safety inspections, workplace incidents and corrective actions in one place. It also includes an assistant that answers questions from live factory data and from a safety knowledge base.
## MCP server

FactoryShield exposes its records to MCP clients through the official Python MCP SDK. Both transports use the same application services and PostgreSQL database as the REST API, and every result is limited to the factories the user may access (admins see all factories).

| Type | Name | Description |
|---|---|---|
| Tool | `get_factory_inspection_summary` | `factory_id` (required). Counts by status and category, average and lowest scores, latest completed inspections with findings, scheduled inspections |
| Tool | `get_overdue_corrective_actions` | `factory_id`, `priority` (`low`, `medium`, `high`), `limit` (1–50, default 20), all optional. Overdue actions with days overdue and assignee |
| Resource | `factory://{factory_id}/overview` | Factory profile, latest inspection scores and open counts (plain text) |
| Prompt | `safety_inspection_review` | `factory_id`. A review request with the factory's current records and the steps to follow |

### HTTP (`/mcp`)

Streamable HTTP in stateless JSON mode at `http://localhost:8000/mcp` while the API is running (`uv run uvicorn app.main:app`). Every request needs a FactoryShield access token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "..."}'
# copy access_token from the response
```

A request without a token, with an expired token, or for an inactive user gets `401 {"detail": ...}`. Tokens expire after `JWT_EXPIRE_MINUTES`; log in again for a new one.

MCP Inspector (`npx @modelcontextprotocol/inspector`): choose transport **Streamable HTTP**, URL `http://localhost:8000/mcp`, and add the header `Authorization: Bearer <access_token>`.

Python client:

```python
import asyncio

import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client


async def main() -> None:
    http = httpx2.AsyncClient(headers={"Authorization": "Bearer <access_token>"})
    async with Client(streamable_http_client("http://localhost:8000/mcp", http_client=http)) as client:
        result = await client.call_tool("get_overdue_corrective_actions", {"priority": "high"})
        print(result.structured_content)


asyncio.run(main())
```

### stdio

For MCP clients on the same machine that start a local command. Set the user the server acts as in `.env`; it must be an existing, active FactoryShield user:

```
MCP_STDIO_USER_EMAIL=you@example.com
```

Command: `uv run python -m app.mcp.stdio` (from the `FactoryShield` folder; the database must be running). Without a valid user the server exits with an error on stderr.

Client configuration (JSON format used by most desktop MCP clients):

```json
{
  "mcpServers": {
    "factoryshield": {
      "command": "uv",
      "args": ["--directory", "/path/to/FactoryShield", "run", "python", "-m", "app.mcp.stdio"]
    }
  }
}
```

MCP Inspector: `npx @modelcontextprotocol/inspector uv --directory /path/to/FactoryShield run python -m app.mcp.stdio`.

### Errors

- Invalid arguments (wrong type, out of range, unknown priority) and factories that do not exist or are outside the user's scope return a tool error (`is_error: true`) with the reason, for example `Factory not found`.
- The resource and the prompt return an MCP error with the same messages.
- If the database is unreachable, the call fails with "The database is temporarily unavailable, please try again shortly".
