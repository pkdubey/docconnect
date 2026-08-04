import os
import uvicorn

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docconnect_backend.settings.development')
    uvicorn.run(
        "fastapi_app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
