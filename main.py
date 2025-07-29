"""FastAPI application entry point for GitHub Issues Analyzer."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import router, get_devin_session
import aiohttp

app = FastAPI(
    title="GitHub Issues Analyzer", 
    description="Analyze GitHub issues with AI - Powered by Cognition AI",
    version="1.0.0"
)

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
    try:
        # Try to import Devin config
        from utils.config import DEVIN_API_KEY
        if DEVIN_API_KEY:
            devin_session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {DEVIN_API_KEY}"}
            )
            print("✅ Devin API session initialized")
            
            # Override the dependency to return our session
            app.dependency_overrides[get_devin_session] = lambda: devin_session
        else:
            print("⚠️  No Devin API key found. Set DEVIN_API_KEY environment variable to use AI features.")
    except ImportError:
        print("⚠️  Devin API modules not available")

@app.on_event("shutdown")
async def shutdown_event():
    """Close the aiohttp session."""
    global devin_session
    if devin_session:
        await devin_session.close()
        print("🔌 Devin API session closed")

# The app is already defined above as 'app'

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8844)
