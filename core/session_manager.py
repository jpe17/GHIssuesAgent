"""Session management for Devin API."""

import time
import requests
from utils.config import DEVIN_API_BASE, DEVIN_API_KEY
from utils.utils import extract_attachment_urls_from_messages


def create_devin_session(prompt: str, repo_url: str = None) -> str:
    """Create a Devin session and return session ID."""
    payload = {"prompt": prompt}
    if repo_url:
        payload["repository_url"] = repo_url
    
    headers = {"Authorization": f"Bearer {DEVIN_API_KEY}"}
    
    try:
        response = requests.post(f"{DEVIN_API_BASE}/sessions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["session_id"]
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to create session: {e}")


def send_session_message(session_id: str, message: str) -> bool:
    """Send a message to an active Devin session."""
    headers = {"Authorization": f"Bearer {DEVIN_API_KEY}"}
    
    try:
        response = requests.post(
            f"{DEVIN_API_BASE}/session/{session_id}/message",
            headers=headers,
            json={"message": message}
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        # Don't print verbose error details
        return False


def wait_for_session_completion(session_id: str, timeout: int = 300) -> dict:
    """Wait for session to complete and return result."""
    start_time = time.time()
    headers = {"Authorization": f"Bearer {DEVIN_API_KEY}"}
    
    while True:
        if time.time() - start_time > timeout:
            return {"error": "timeout"}
        
        try:
            response = requests.get(f"{DEVIN_API_BASE}/session/{session_id}", headers=headers)
            response.raise_for_status()
            data = response.json()
            status = data.get("status_enum")
            
            if status in ["completed", "failed", "stopped", "blocked"]:
                # Extract message attachments
                messages = data.get("messages", [])
                message_attachments = extract_attachment_urls_from_messages(messages)
                if message_attachments:
                    data["message_attachments"] = message_attachments
                return data
        except requests.exceptions.RequestException as e:
            print(f"Error checking session status: {e}")
        
        time.sleep(5) 