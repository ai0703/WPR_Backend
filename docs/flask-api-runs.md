# Using the Flask `/api/runs` Endpoint from the Dashboard

This guide walks through wiring the React dashboard to the new Flask backend so that visiting URLs like `/dashboard?since=2025-09-01&until=2025-09-07&mode=calendar&n=0` automatically loads data from `GET /api/runs`.

## 1. Prerequisites

1. **Flask service deployed** – note the base URL  `https://d8e32195cd18.ngrok-free.app/`.
2. **Ingest token** – the frontend must include `Authorization: Bearer <INGEST_TOKEN>` in every request.
3. **CORS enabled** – if the React app is hosted on another origin, ensure Flask is configured to allow it (Flask-CORS or reverse-proxy headers).

## 2. Frontend Environment Configuration

In the React project, introduce environment variables so the API host and token can be swapped per environment:

```
REACT_APP_API_BASE_URL=https://d8e32195cd18.ngrok-free.app/
REACT_APP_API_TOKEN=your-shared-token
```

When running locally alongside the Flask dev server, use `http://127.0.0.1:5000` for the base URL.

## 3. Extracting URL Parameters in React

The dashboard route already receives `since`, `until`, `mode`, and `n` via the query string. Inside the `/dashboard` page component use the router (e.g. `useLocation`) to read them:

```tsx
import { useLocation } from "react-router-dom";

function useDashboardQuery() {
  const { search } = useLocation();
  const params = new URLSearchParams(search);

  return {
    since: params.get("since") ?? "",
    until: params.get("until") ?? "",
    mode: params.get("mode") ?? "calendar",
    step: Number(params.get("n") ?? 0),
  };
}
```

If the URL omits `since`/`until`, decide on sensible defaults before calling the API.

## 4. Calling the Flask Endpoint

Create a small API helper that encodes the query parameters and sends the bearer token:

```tsx
async function fetchRuns(windowStart: string, windowEnd: string) {
  const baseUrl = process.env.REACT_APP_API_BASE_URL;
  const token = process.env.REACT_APP_API_TOKEN;

  if (!baseUrl || !token) {
    throw new Error("API base URL or token not configured");
  }

  const query = new URLSearchParams({ since: windowStart, until: windowEnd });
  const response = await fetch(`${baseUrl}/api/runs?${query.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Runs request failed: ${response.status} ${message}`);
  }

  return response.json();
}
```

> **Tip** – The Flask service accepts timestamps (`2025-09-08 00:00:00`) and plain dates (`2025-09-08`). No need to pre-sanitize the query string.

## 5. Loading Data in the Dashboard Page

Combine the query hook with the API helper inside a React effect:

```tsx
const DashboardPage = () => {
  const { since, until } = useDashboardQuery();
  const [data, setData] = useState<RunsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!since || !until) {
      return;
    }

    setLoading(true);
    fetchRuns(since, until)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [since, until]);

  // …render loading/error states and the dashboard using `data.runs`
};
```

Shape of the JSON returned by Flask:

```json
{
  "since": "2025-09-08 00:00:00",
  "until": "2025-09-14 23:59:59",
  "runs": {
    "n8n_2025-09-08 00:00:00_2025-09-14 23:59:59": {
      "rep_rga_data": { "tableByRep": [...] },
      "won_lost_analysis": { ... },
      "pipeline_metrics": { ... }
    }
  }
}
```

Each run is keyed by its `runId`; the payloads match what the ingest route stored.

## 6. Handling Multiple Environments

When the React app and Flask API are hosted separately:

| Environment | `REACT_APP_API_BASE_URL` | `REACT_APP_API_TOKEN` |
|-------------|--------------------------|-----------------------|
| Local dev   | `http://127.0.0.1:5000`  | token from `.env`     |
| Staging     | `https://staging-api.example.com` | staging token |
| Production  | `https://api.example.com` | production token |

If the API sits behind an HTTPS load balancer, confirm the certificate and CORS headers are correct before deploying the frontend change.

## 7. Testing Checklist

1. Start Flask locally (`python -m app` or `flask --debug run`).
2. Hit the endpoint manually:
   ```bash
   curl "http://127.0.0.1:5000/api/runs?since=2025-09-08%2000:00:00&until=2025-09-14%2023:59:59" \
     -H "Authorization: Bearer 1234567"
   ```
3. Run the helper script (`python scripts/test_runs_window.py`) to ensure JSON is returned and saved.
4. Visit `http://localhost:5173/dashboard?since=2025-09-08%2000:00:00&until=2025-09-14%2023:59:59` during development; confirm the React app renders data.

## 8. Migration Notes

- Remove the legacy Express route wiring once the React app switches to Flask.
- Keep `INGEST_TOKEN` synchronized between n8n, Flask, and the frontend.
- If additional query parameters (`mode`, `n`) drive UI state only, keep handling them in the React component—they do not need to be sent to Flask.
- If you expect large responses, add caching or pagination on the frontend to avoid re-fetching the same window unnecessarily.

With these steps the dashboard will seamlessly consume the Flask backend regardless of where each service is hosted.

