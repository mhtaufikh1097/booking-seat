# Whoosh Operations CMS

Standalone React/Vite Back Office for the existing Whoosh employee seat frontend. It lives in `cms/` so the root employee app and GitHub Pages deployment remain unchanged.

## Run locally

Start the FastAPI backend first, then from this directory:

```powershell
npm install
$env:VITE_API_BASE_URL="http://127.0.0.1:8000/api/v1"
npm run dev
```

Open `http://127.0.0.1:5174`.

For a production build:

```powershell
npm run build
npm run preview
```

## Authentication

The CMS calls `POST /auth/login` using the existing FastAPI OAuth2 form login. The access token is held in `sessionStorage` for this browser session. Every API request sends it as a Bearer token. `GET /auth/me` provides the authoritative user and role; employees are blocked from CMS access.

Allowed CMS roles are Admin, Operator, and Manager. The backend remains the final authorization layer.

## Available modules

- Dashboard: live train, carriage, and seat counts from the existing APIs
- Trains: list, search, status filter, create, edit, activate/deactivate
- Carriages: select a train, list, create, edit, activate/deactivate
- Seats: select train/carriage, view generated seats, generate configured seats
- Manifest, Employees, Bookings, Reports, System Logs: explicit Coming Soon states

The CMS does not implement Excel import, employee booking, or fake data.
