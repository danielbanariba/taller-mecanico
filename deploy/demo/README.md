# Public test deployment

A shareable test instance of the app at
<https://inventario-taller.danielbanariba.com>, served from the developer's
machine through the existing named Cloudflare tunnel `ceiba-demos`. It is a
test link for real users to try the app, not production: one machine, no
backups unless you take them, and it goes down whenever the machine does.

## What runs where

| Piece | Runs as | Listens on |
| --- | --- | --- |
| Postgres 17 | container `taller-demo-db`, volume `taller-demo-pgdata`, `--restart unless-stopped` | `127.0.0.1:5441`, database `taller_demo` |
| API (FastAPI) | systemd user unit `taller-demo-api.service` (`uvicorn`) | `127.0.0.1:3013` |
| Web (built SPA) | systemd user unit `taller-demo-web.service` (`vite preview` over `web/dist`) | `127.0.0.1:3012` |
| Public entry | `ceiba-tunnel.service` (`~/.cloudflared/ceiba-demos.yml`) | `inventario-taller.danielbanariba.com` |

The tunnel splits by path: `^/api/` goes to the API on 3013, everything else
to the web on 3012 (see `cloudflared-ingress.yml` here). Web and API therefore
share one origin, which the `SameSite=Lax` session cookie needs, and no CORS
is involved. `vite preview` itself still proxies `/api` to the dev API on
`:8010` (it inherits `server.proxy`), so hitting `127.0.0.1:3012/api/...`
directly does not reach the demo API; only the tunnel's path rule does.

Code runs from a dedicated, detached git worktree,
`/home/banar/Desktop/taller-mecanico-worktrees/demo`, so the demo never
follows whatever branch the dev checkout has checked out. Do not remove that
worktree while the units are running.

All units are enabled with `WantedBy=default.target` and the user has
linger enabled, so everything comes back after a reboot without a login.

## Configuration

`~/.config/taller-mecanico/demo.env` (directory mode 700, file mode 600,
never committed) is the single env file both units load:

- `TALLER_DATABASE_URL` - points at `127.0.0.1:5441/taller_demo`, with the
  container's password.
- `TALLER_JWT_SECRET` - a random secret of at least 32 characters, unique to
  this deployment. Changing it logs every tester out.
- `TALLER_COOKIE_SECURE=true` - the public URL is HTTPS (TLS ends at
  Cloudflare).
- `TALLER_PREVIEW_ALLOWED_HOSTS=inventario-taller.danielbanariba.com` - read
  by `web/vite.config.ts`; without it `vite preview` answers the tunnel's
  requests with 403.
- `VITE_DEMO_PHONE` and `VITE_DEMO_PASSWORD` - the shared demo account (see
  below). Read by `npm run build`, not by the units.

Process environment variables win over the `api/.env` file that
`taller/shared/config.py` anchors to, and the worktree has no `api/.env`, so
this file is the only source of configuration.

## Demo account

Testers do not need to register: the login form of this build comes
prefilled with one shared account, and a notice above it says so. They
open the link and tap "Iniciar sesión". Registering their own workshop
still works.

| Phone | Password | Workshop | Owner |
| --- | --- | --- | --- |
| `9999-9999` | `demo1234` | Taller Demo | Demo |

- **Security:** Vite compiles every `VITE_*` value into the public JS
  bundle, so anyone can read these credentials. Set `VITE_DEMO_*` only when
  building this demo, never for a real deployment. Without them the login
  form is empty and shows no notice.
- **Shared data:** every tester sees and edits the same inventory.
- **Shared lockout:** five wrong passwords in a row lock the phone for 15
  minutes, for every tester at once. Login still works the moment the lock
  expires.

`seed-demo-account.sh` registers the account (or logs in if it already
exists) and creates eight sample parts, five customers, six vehicles and
(from phase 2) six work orders with their lines, driven through the status
lifecycle step by step, through the API. Three of the parts start at or
below their minimum stock so the low-stock alert shows. Every id is
deterministic, so rerunning it never duplicates anything, and it leaves
rows that testers edited alone. Run it after the first deploy, or after
wiping the demo database, once the public URL answers:

Seeded customers and vehicles (all fictional; the phone numbers are
patterned test data and **must never be messaged**):

| Customer | Phone | Vehicle(s) |
| --- | --- | --- |
| María Hernández | `9000-0001` (mobile) | Toyota Corolla 2012, plate `DEM0001` |
| José Núñez | `3000-0002` (mobile) | Honda CG 150 2019, plate `DEM0002`; Bajaj Pulsar, unplated |
| Carlos Mejía | `2200-0003` (landline) | Nissan Frontier 2015, plate `DEM0003` |
| Ana Castillo | none | Suzuki AX100, unplated |
| Luis Zelaya | `8000-0005` (mobile) | Hyundai Accent 2010, plate `DEM0004` |

The seed submits the vehicle plates raw (`DEM-0001`, `DEM 0002`, `dem0003`,
`DEM0004`) to exercise the API's plate normalization; they all land
normalized as shown above.

Seeded work orders, one per vehicle except the Corolla (two, so its detail
screen always has more than one entry in its service history):

| Order | Vehicle | Status | Lines |
| --- | --- | --- | --- |
| #1 | Toyota Corolla | `in_progress` | Labor + 1 `pastillas-freno` (stock drops from 2 to 1, so the in-progress consumption is visible) |
| #2 | Honda CG 150 | `quote` | Labor + 1 `cadena-moto-428` + 1 external part |
| #3 | Nissan Frontier | `completed` | Labor + 2 `aceite-20w50` + 1 `filtro-aceite` |
| #4 | Hyundai Accent | `approved` | Labor only |
| #5 | Toyota Corolla | `delivered` | Labor only |
| #6 | Bajaj Pulsar | `cancelled` (from `quote`) | None |

Each order is driven through `POST /api/work-orders`, `POST
.../lines` and `PUT .../status` one transition edge at a time (never a
direct jump), the same way a real mechanic would use the app. A seeded
`in_progress`/`completed` order's parts have already consumed stock, so the
item detail screens for `pastillas-freno`, `aceite-20w50` and
`filtro-aceite` show a movement linked back to the order that caused it.

```sh
bash -c 'set -a; . ~/.config/taller-mecanico/demo.env; set +a; \
  /home/banar/Desktop/taller-mecanico-worktrees/demo/deploy/demo/seed-demo-account.sh'
```

It talks to the public URL by default; pass another base URL as the first
argument. The session cookie is `Secure`, so that URL must be HTTPS.

## Deploying an update

Run from any shell; every path is absolute. Replace `origin/main` with the
commit or branch to deploy.

```sh
git -C /home/banar/Desktop/taller-mecanico fetch origin
git -C /home/banar/Desktop/taller-mecanico-worktrees/demo checkout --detach origin/main

cd /home/banar/Desktop/taller-mecanico-worktrees/demo/api
uv sync --frozen
uv run --frozen --env-file ~/.config/taller-mecanico/demo.env alembic upgrade head

cd /home/banar/Desktop/taller-mecanico-worktrees/demo/web
npm ci
# demo.env must be loaded, or the build ships without the demo account
bash -c 'set -a; . ~/.config/taller-mecanico/demo.env; set +a; npm run build'

systemctl --user restart taller-demo-api.service taller-demo-web.service
curl -s https://inventario-taller.danielbanariba.com/api/health
```

A new build changes the service worker, so testers get the new version on
their next visit (`registerType: "autoUpdate"`).

## Stopping and starting

```sh
# Take the site offline (the tunnel then answers 502 for the hostname)
systemctl --user stop taller-demo-web.service taller-demo-api.service
# ...and keep it off across reboots
systemctl --user disable taller-demo-web.service taller-demo-api.service
docker stop taller-demo-db

# Bring it back
docker start taller-demo-db
systemctl --user enable --now taller-demo-api.service taller-demo-web.service
```

Unpublishing the hostname for good also means removing the two entries from
`~/.cloudflared/ceiba-demos.yml`, restarting `ceiba-tunnel.service`, and
deleting the `inventario-taller` DNS record in the Cloudflare dashboard
(`cloudflared` cannot delete DNS routes).

## Logs

```sh
journalctl --user -u taller-demo-api.service -f
journalctl --user -u taller-demo-web.service -f
journalctl --user -u ceiba-tunnel.service -f
docker logs -f taller-demo-db
```

## The demo database is not the dev database

The demo data lives only in the `taller-demo-db` container and its
`taller-demo-pgdata` volume. It is separate from the `db` service in
`docker-compose.yml` (port 5440, databases `taller`/`taller_test`):
`docker compose down -v` in the repo does not touch it, and nothing here
touches the dev database. Conversely, `docker rm -v taller-demo-db` or
`docker volume rm taller-demo-pgdata` deletes every tester's data with no
undo. Take a dump first if it matters:

```sh
docker exec taller-demo-db pg_dump -U taller taller_demo > taller_demo.sql
```

## First-time setup (reference)

1. `git worktree add --detach /home/banar/Desktop/taller-mecanico-worktrees/demo <commit>`.
2. Start the database container (random password, bound to `127.0.0.1:5441`,
   `--restart unless-stopped`, volume `taller-demo-pgdata`) and wait for
   `pg_isready`.
3. Write `~/.config/taller-mecanico/demo.env` as described above.
4. Run the update steps above (sync, migrate, build).
5. Install the units: copy `taller-demo-api.service` and
   `taller-demo-web.service` into `~/.config/systemd/user/`, replace
   `__DEMO_WORKTREE__` and `__NODE_BIN__` (for example with `sd`), then
   `systemctl --user daemon-reload` and
   `systemctl --user enable --now taller-demo-api.service taller-demo-web.service`.
   If node is upgraded through nvm, update `__NODE_BIN__` in the installed
   web unit and reload.
6. Back up `~/.cloudflared/ceiba-demos.yml`, add the entries from
   `cloudflared-ingress.yml` before the catch-all, run
   `cloudflared tunnel --config ~/.cloudflared/ceiba-demos.yml ingress validate`,
   restart `ceiba-tunnel.service`, then
   `cloudflared tunnel route dns <tunnel-uuid> inventario-taller.danielbanariba.com`.
7. Once the public URL answers, run `seed-demo-account.sh` (see
   "Demo account").
