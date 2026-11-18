# FactoryShield Web App

The FactoryShield frontend is built with Next.js, using the App Router, TypeScript, and Tailwind CSS. It connects to the FactoryShield API and provides the interface for managing factory safety and compliance activities.

## Pages and access

The application includes the following pages:

| Path | Description | Access |
|---|---|---|
| `/login` | Sign-in page | All users |
| `/` | Dashboard with overall statistics, inspection score trends, incidents by severity, overdue actions, and upcoming inspections | Signed-in users |
| `/factories`, `/factories/[id]` | Factory list and individual factory details | Signed-in users; editing is restricted to admins |
| `/inspections` | Safety inspection records | Signed-in users; changes are restricted to admins |
| `/incidents` | Workplace incident records | Signed-in users; changes are restricted to admins |
| `/actions` | Corrective action tracking | Signed-in users; changes are restricted to admins |
| `/knowledge` | Safety knowledge documents, including upload and delete options | Signed-in users; upload and delete are restricted to admins |
| `/assistant` | AI assistant with chat and conversation history | Signed-in users |
| `/users` | User management | Admins only |
| `/account` | Personal profile and password settings | Signed-in users |

Staff members can only view factories assigned to them. Administrative actions are available only to admins, and the API applies the same permission checks on the backend.

## API integration and authentication

The frontend communicates with the FactoryShield API through Next.js server-side routes. API access tokens are never exposed to the browser.

Here's how authentication and API requests work:

- **Login:** `POST /api/auth/login` sends the user's credentials to the API. Once authenticated, the returned token is stored in an httpOnly cookie named `fs_token`.
- **API requests:** Requests made through `/api/backend/*` are forwarded to the backend with the user's token in the `Authorization: Bearer` header. This also handles JSON requests and file uploads.
- **Logout:** `POST /api/auth/logout` removes the authentication cookie.
- **Route protection:** `src/proxy.ts` redirects users without an authentication cookie to `/login`. After signing in, they are returned to the page they originally tried to visit.

The application also keeps list filters and pagination in the URL. This makes it possible to bookmark a filtered view or share a link without losing the current filters.

### Session expiration

The application handles expired sessions without forcing users to reload the page.

During login, the frontend also sets an `fs_expires` cookie containing the token's expiry time. Unlike the authentication cookie, this one is readable by the page.

A warning bar appears five minutes before the session expires. Once the session ends, a sign-in dialog opens over the current page.

If an API request fails because the token has expired, the request waits until the user signs in again. After successful authentication, the rejected requests are sent again automatically. This helps preserve the current page and prevents users from losing work they have already entered.

### Exporting records

CSV export is available for the following sections:

- Factories
- Inspections
- Incidents
- Corrective actions

The export includes all records matching the current filters, not just the rows displayed on the current page.

Files are exported as UTF-8, making them suitable for opening in Excel.

## Environment variables

The frontend uses the following environment variables:

| Variable | Default | Description |
|---|---|---|
| `API_BASE_URL` | `http://localhost:8000/api/v1` | Base URL of the FactoryShield API. Used by the Next.js server only. |
| `COOKIE_SECURE` | `false` | Set to `true` when running the application over HTTPS. |

## Running locally

Make sure Node.js 22 is installed and the FactoryShield API is already running. See the main project README for backend setup instructions.

From the frontend directory, install the dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The application will be available at:

http://localhost:3000

### Running checks

Before building or committing changes, you can run the following checks:

```bash
# TypeScript check
npx tsc --noEmit

# ESLint
npm run lint

# Production build
npm run build
```

## Running with Docker

The frontend is available as the `frontend` service in the root `docker-compose.yml`.

Docker builds the frontend from this directory and starts it after the API becomes healthy. The application listens on the port configured through `FRONTEND_PORT`, which defaults to `3000`.

Inside the Docker Compose network, the frontend connects to the API using:

```text
http://api:8000/api/v1
```

To build and start the frontend:

```bash
docker compose up -d --build frontend
```