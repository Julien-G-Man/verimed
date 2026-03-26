import os

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT") or os.getenv("API_PORT", "8000"))
    
    # When PORT is present (Render production), force 0.0.0.0 regardless of .env
    # Otherwise use .env or default to localhost for local dev
    if os.getenv("PORT"):
        host = "0.0.0.0"
        reload_enabled = False
    else:
        host = os.getenv("API_HOST", "127.0.0.1")
        reload_enabled = os.getenv("API_RELOAD", "true").lower() == "true"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload_enabled,
    )