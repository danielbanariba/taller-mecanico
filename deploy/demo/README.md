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

Process environment variables win over the `api/.env` file that
`taller/shared/config.py` anchors to, and the worktree has no `api/.env`, so
this file is the only source of configuration.

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
npm run build

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
