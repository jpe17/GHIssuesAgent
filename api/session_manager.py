"""Session management for Devin API interactions."""

import asyncio
import aiohttp
from typing import Dict
from .config import DEVIN_API_BASE


async def create_devin_session(session: aiohttp.ClientSession, prompt: str, repo_url: str = None) -> str:
    """Create a new Devin session and return the session ID."""
    payload = {"prompt": prompt}
    if repo_url:
        payload["repository_url"] = repo_url
    
    async with session.post(f"{DEVIN_API_BASE}/sessions", json=payload) as response:
        session_data = await response.json()
        session_id = session_data["session_id"]
        print(f"Created session {session_id}")
        print(f"URL: {session_data['url']}")
        return session_id


async def wait_for_session_completion(session: aiohttp.ClientSession, session_id: str, timeout: int = 300) -> Dict:
    """Wait for a Devin session to complete and return the results."""
    backoff = 1
    start_time = asyncio.get_event_loop().time()
    
    print("Polling for results...")
    while True:
        # Check timeout
        if asyncio.get_event_loop().time() - start_time > timeout:
            raise Exception(f"Session {session_id} timed out after {timeout} seconds")
        
        async with session.get(f"{DEVIN_API_BASE}/session/{session_id}") as response:
            response_json = await response.json()
            
            if response_json["status_enum"] in ["blocked", "stopped"]:
                print(f"Session {session_id} completed with status: {response_json['status_enum']}")
                return response_json
            
            print(f"Session {session_id} status: {response_json['status_enum']}")
        
        await asyncio.sleep(min(backoff, 30))
        backoff *= 2 