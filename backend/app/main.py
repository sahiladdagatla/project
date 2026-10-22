"""
FloodTwinAI Backend API Entry Point.

FastAPI application providing:
- Real-time routing across 4 policies
- Hydrodynamic flood simulation layers
- Hospital accessibility and critical road ranking
- Satellite flood segmentation
- Empirical research evaluation data
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from backend.app.api.routes import router

app = FastAPI(
    title="FloodTwinAI Backend API",
    description="An Urban Flood Digital Twin for Explainable Forecasting, Infrastructure Impact Analysis and Risk-Aware Routing",
    version="1.0.0"
)

# Enable CORS for local Vite React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Serve built frontend if available
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/")
    def root():
        return {
            "message": "Welcome to FloodTwinAI Digital Twin API",
            "documentation": "/docs",
            "status": "/api/status"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
