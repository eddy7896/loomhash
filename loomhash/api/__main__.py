"""Manual local run: `python -m loomhash.api`.

Uses the default InMemoryStorageBackend -- data is lost on restart. This
is for local smoke-testing the routes (including the edge/applet/ manual
test page, see edge/README.md) only, not a deployment entrypoint. Caddy
(reverse proxy, per system.md) and a real StorageBackend wiring are
separate, not-yet-approved deployment concerns.

enable_dev_cors=True here is safe only because this entrypoint is for
local manual testing -- see create_app()'s docstring.

A dev API key is auto-generated and printed to stdout so the developer
can immediately use it in curl/applet calls without extra setup.
"""

import uvicorn

from loomhash.auth import InMemoryAPIKeyStore, generate_api_key
from .app import create_app

if __name__ == "__main__":
    key_store = InMemoryAPIKeyStore()
    raw_key, api_key_record = generate_api_key()
    key_store.store(api_key_record)

    print()
    print("=" * 60)
    print("  Dev API key (valid for this process only):")
    print(f"  {raw_key}")
    print("=" * 60)
    print()

    from loomhash.storage.admin import InMemoryAdminStore
    admin_store = InMemoryAdminStore()

    uvicorn.run(
        create_app(key_store=key_store, admin_store=admin_store, enable_dev_cors=True),
        host="127.0.0.1",
        port=8000,
    )
