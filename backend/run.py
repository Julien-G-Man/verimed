import os

import uvicorn

if __name__ == "__main__":
    # Keep local development bound to loopback by default to avoid LAN exposure.
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    reload_enabled = os.getenv("API_RELOAD", "true").lower() == "true"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload_enabled,
    )