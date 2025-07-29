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


def _wait_for_session_with_custom_check(session_id: str, timeout: int, show_live: bool, custom_check=None) -> dict:
    """Helper function to wait for session completion with optional custom check."""
    start_time = time.time()
    last_message_count = 0
    
    while time.time() - start_time < timeout:
        try:
            session_data = get_session_details(session_id)
            
            # Show live messages
            if show_live:
                last_message_count = display_live_messages(session_id, last_message_count)
            
            # Run custom check if provided
            if custom_check and custom_check(session_data):
                return session_data
            
            # Check if session is done
            if session_data.get("status_enum") in ["completed", "failed", "stopped", "blocked"]:
                return session_data
                
        except requests.exceptions.RequestException:
            print("⚠️  API error, retrying...")
        
        time.sleep(30)
    
    return {"error": "timeout"}


def wait_for_session_completion(session_id: str, timeout: int = 300, show_live: bool = False) -> dict:
    """Wait for session to complete and return result."""
    return _wait_for_session_with_custom_check(session_id, timeout, show_live)


def wait_for_execution_completion(session_id: str, timeout: int = 300, show_live: bool = False) -> dict:
    """Wait for execution session to complete, stopping early if PR is detected."""
    def pr_check(session_data):
        from utils.utils import extract_pr_url_from_session
        if extract_pr_url_from_session(session_data):
            print(f"✅ PR detected - stopping early")
            return True
        return False
    
    return _wait_for_session_with_custom_check(session_id, timeout, show_live, pr_check)