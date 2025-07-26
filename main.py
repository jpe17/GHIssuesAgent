"""FastAPI application entry point for GitHub Issues Analyzer."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import router, get_devin_session
from api.config import DEVIN_API_KEY
import aiohttp

app = FastAPI(title="GitHub Issues Analyzer", description="Analyze GitHub issues with Devin AI")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routes
app.include_router(router)

# Global session for Devin API calls
devin_session = None

@app.on_event("startup")
async def startup_event():
    """Initialize the aiohttp session for Devin API calls."""
    global devin_session
    devin_session = aiohttp.ClientSession(
        headers={"Authorization": f"Bearer {DEVIN_API_KEY}"}
    )
    
    # Override the dependency to return our session
    app.dependency_overrides[get_devin_session] = lambda: devin_session

@app.on_event("shutdown")
async def shutdown_event():
    """Close the aiohttp session."""
    global devin_session
    if devin_session:
        await devin_session.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
