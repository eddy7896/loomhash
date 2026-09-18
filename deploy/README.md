# Postgres + Redis on the VPS (Docker)

Standalone infra for the storage module's real adapters (`loomhash/storage/postgres.py`,
`redis_cache.py`, `combined.py`), which until now have only been tested against
`InMemoryStorageBackend` — see docs/verification-checklist.md and
docs/agents/storage.md for the exact gap this closes.

Both services are bound to `127.0.0.1` on the VPS only — not reachable from
outside the VPS. That's deliberate: an unauthenticated or network-exposed
Postgres/Redis is a common breach vector. Both also require a password
regardless (defense in depth). Reach them from elsewhere via an SSH tunnel,
never by opening the ports.

## 1. On the VPS: install Docker

If Docker isn't already installed, follow Docker's official install guide
for your VPS's OS (e.g. `curl -fsSL https://get.docker.com | sh` on most
Debian/Ubuntu VPS images — but check Docker's current docs rather than
trusting this blindly, install steps do change). This repo doesn't install
Docker for you.

## 2. Get the repo onto the VPS

```sh
git clone https://github.com/eddy7896/loomhash.git
cd loomhash/deploy
```

## 3. Configure secrets

```sh
cp .env.example .env
```

Edit `.env` and set real, strong passwords for `POSTGRES_PASSWORD` and
`REDIS_PASSWORD` (e.g. generate each with `openssl rand -base64 32`).
`.env` is gitignored — never commit it.

## 4. Start the containers

```sh
docker compose up -d
docker compose ps
```

Both should show as healthy within ~10-15 seconds (healthchecks are
configured in docker-compose.yml).

## 5. Reach them from your dev machine via an SSH tunnel

From your dev machine (not the VPS):

```sh
ssh -N -L 5432:127.0.0.1:5432 -L 6379:127.0.0.1:6379 <your-user>@<vps-host>
```

Leave that running in its own terminal — it forwards your dev machine's
localhost:5432/6379 to the VPS's loopback-only ports. Now `127.0.0.1:5432`
and `127.0.0.1:6379` on your dev machine reach the real, VPS-hosted services.

## 6. Verify the real adapters actually work

From your dev machine, in the repo root, with the tunnel from step 5 still open:

```sh
POSTGRES_CONNINFO="postgresql://loomhash:<POSTGRES_PASSWORD>@127.0.0.1:5432/loomhash" \
REDIS_PASSWORD="<REDIS_PASSWORD>" \
python scripts/verify_live_storage.py
```

(Substitute the real passwords from your `.env`.) This creates the
`enrollments` table if it doesn't exist yet, then does a real
enroll → get (through the write-through cache) → delete round-trip against
both live services. If it prints "All checks passed," update
docs/verification-checklist.md's ENR-05/AUT-02/REV-01 rows to reflect that
the real Postgres/Redis adapters — not just the in-memory fake — are now
verified, and note the date and how it was run.

## 7. Pointing the actual API at these services

`loomhash.api.create_app()` defaults to `InMemoryStorageBackend`. To use the
real backend instead:

```python
from loomhash.storage.combined import PostgresRedisStorageBackend
from loomhash.storage.postgres import PostgresStorageBackend
from loomhash.storage.redis_cache import RedisEnrollmentCache
import redis

postgres = PostgresStorageBackend("postgresql://loomhash:<password>@127.0.0.1:5432/loomhash")
postgres.ensure_schema()
cache = RedisEnrollmentCache(redis.Redis(host="127.0.0.1", port=6379, password="<password>"))
storage = PostgresRedisStorageBackend(postgres, cache)

app = create_app(storage)  # instead of create_app()
```

There's no wired-up entrypoint for this yet (`loomhash/api/__main__.py` still
defaults to the in-memory backend for local smoke-testing) — wiring a real
deployment entrypoint (reading connection info from environment variables,
running behind Caddy per system.md) is a separate, not-yet-done step.

## Stopping / resetting

```sh
docker compose down       # stop, keep data
docker compose down -v    # stop and DELETE all data (both volumes)
```
