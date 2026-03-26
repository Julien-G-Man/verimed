import os

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT") or os.getenv("API_PORT", "8000"))
    default_host = "0.0.0.0" if os.getenv("PORT") else "127.0.0.1"
    host = os.getenv("API_HOST", default_host)
    reload_enabled = os.getenv("API_RELOAD", "true").lower() == "true"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload_enabled,
    )