# FRIDAY Cloud Agent

The agent sends timestamped CPU, memory, disk and uptime metrics to the
Monitoring Metrics API. The dashboard reads those metrics from the backend; the
agent never sends data directly to the webpage.

## Account and device registration

On first start, if no device credentials are saved, the agent asks whether to
create a website account or sign in to an existing account. It prompts for the
account email and hidden password, then registers this installation under that
account. The password and user access token are used only during enrollment
and are not saved.

After successful enrollment, the agent saves the device ID and device-specific
token to `~/FRIDAY/device_credentials.json` with owner-only permissions. It
reuses that token on later starts without asking for the website password or
token again. The installation ID is persisted separately and reused if
enrollment needs to be retried. Set `FRIDAY_DEVICE_TOKEN` (legacy
`FRIDAY_AGENT_TOKEN` is also accepted) to provide an already-issued device
token instead of saved credentials. Never commit or share a device token.

The backend must support the account registration and device enrollment APIs
described in the generated backend requirements PDF. In particular, the
existing API handoff does not specify an endpoint that lets a signed-in user
register a device and obtain its device token.

## API configuration

The default API base is
`https://monitoring-metrics-api.onrender.com`. Override it with
`FRIDAY_API_BASE_URL` if needed. The agent posts to
`/api/v1/agent/metrics` using the device token in a Bearer authorization header.
It sends the API contract fields `cpu_percent`, `memory_percent`,
`disk_percent`, `uptime_seconds`, and timezone-aware `timestamp`.

`FRIDAY_HEARTBEAT_INTERVAL` controls the interval in seconds; it defaults to 30
and accepts values from 5 through 3600. Requests verify TLS certificates and
use a bounded 30-second timeout for enrollment and 20-second timeout for
metrics. A successful upload must return HTTP 202. Failed uploads are logged
without credentials or response bodies and retried on the next sampling
interval. If the server returns 401 for the device token, stop the agent,
remove `~/FRIDAY/device_credentials.json`, and start it again to sign in and
re-enroll.

Run from the `agent` directory with:

```sh
python -m agent.main
```

Press Ctrl+C to stop the agent cleanly.