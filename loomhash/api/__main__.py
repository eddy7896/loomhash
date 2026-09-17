"""Manual local run: `python -m loomhash.api`.

Uses the default InMemoryStorageBackend -- data is lost on restart. This
is for local smoke-testing the routes only, not a deployment entrypoint.
Caddy (reverse proxy, per system.md) and a real StorageBackend wiring are
separate, not-yet-approved deployment concerns.
"""

import uvicorn

from .app import create_app

if __name__ == "__main__":
    uvicorn.run(create_app(), host="127.0.0.1", port=8000)
