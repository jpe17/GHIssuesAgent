"""Session management for Devin API."""

import time
import requests
from utils.config import DEVIN_API_BASE, DEVIN_API_KEY
from utils.utils import extract_attachments_from_session_data


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


def get_session_details(session_id: str) -> dict:
    """Get detailed information about a Devin session."""
    headers = {"Authorization": f"Bearer {DEVIN_API_KEY}"}
    
    try:
        response = requests.get(f"{DEVIN_API_BASE}/session/{session_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting session details: {e}")
        return {}


def display_live_messages(session_id: str, last_message_count: int = 0) -> int:
    """Display new messages from a Devin session and return the new message count."""
    session_data = get_session_details(session_id)
    messages = session_data.get("messages", [])
    
    if len(messages) > last_message_count:
        # Display new messages
        for i in range(last_message_count, len(messages)):
            message = messages[i]
            message_type = message.get("type", "unknown")
            content = message.get("message", "")
            
            if message_type == "devin_message":
                print(f"🤖 Devin: {content}")
            elif message_type == "user_message":
                print(f"👤 User: {content}")
            elif message_type == "system_message":
                print(f"⚙️  System: {content}")
        
        return len(messages)
    
    return last_message_count


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
    except requests.exceptions.RequestException:
        return False


def wait_for_session_completion(session_id: str, timeout: int = 300, show_live: bool = False) -> dict:
    """Wait for session to complete and return result."""
    start_time = time.time()
    last_message_count = 0
    consecutive_errors = 0
    max_consecutive_errors = 3
    
    while True:
        if time.time() - start_time > timeout:
            return {"error": "timeout"}
        
        try:
            session_data = get_session_details(session_id)
            status = session_data.get("status_enum")
            consecutive_errors = 0  # Reset error counter on success
            
            # Display live messages if requested
            if show_live:
                last_message_count = display_live_messages(session_id, last_message_count)
            
            if status in ["completed", "failed", "stopped", "blocked"]:
                # Extract attachments from session data
                attachments = extract_attachments_from_session_data(session_data)
                if attachments:
                    session_data["message_attachments"] = attachments
                return session_data
                
        except requests.exceptions.RequestException as e:
            consecutive_errors += 1
            print(f"Error checking session status (attempt {consecutive_errors}): {e}")
            
            # If we get too many consecutive errors, the session might be stuck
            if consecutive_errors >= max_consecutive_errors:
                print(f"⚠️  Too many consecutive errors ({consecutive_errors}). Session might still be running on frontend.")
                print(f"   Session ID: {session_id}")
                print(f"   You can check the session status manually on the Devin frontend.")
                return {"error": "api_errors", "session_id": session_id}
        
        # Increase sleep time on errors to reduce API pressure
        sleep_time = 10 if consecutive_errors > 0 else 5
        time.sleep(sleep_time)