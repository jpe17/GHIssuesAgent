"""Session management for Devin API."""

import time
import os
import requests
from utils.config import DEVIN_API_BASE, DEVIN_API_KEY
from utils.utils import extract_attachments_from_session_data


def create_devin_session(prompt: str, repo_url: str = None, file_url: str = None) -> str:
    """Create a Devin session and return session ID."""
    payload = {"prompt": prompt}
    if repo_url:
        payload["repository_url"] = repo_url
    if file_url:
        payload["file_url"] = file_url
    
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


def display_session_status(session_id: str) -> str:
    """Display current session status and return the status."""
    session_data = get_session_details(session_id)
    status = session_data.get("status_enum", "unknown")
    status_emoji = {
        "working": "🔄",
        "blocked": "⏸️",
        "completed": "✅",
        "failed": "❌",
        "stopped": "⏹️",
        "expired": "⏰",
        "finished": "✅"
    }
    emoji = status_emoji.get(status, "❓")
    print(f"{emoji} Session Status: {status}")
    return status


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
            
            # Format the message based on type
            if message_type == "devin_message":
                # Split long messages for better readability
                if len(content) > 200:
                    lines = content.split('\n')
                    print(f"🤖 Devin:")
                    for line in lines:
                        if line.strip():
                            print(f"   {line}")
                else:
                    print(f"🤖 Devin: {content}")
            elif message_type == "user_message":
                print(f"👤 User: {content}")
            elif message_type == "system_message":
                print(f"⚙️  System: {content}")
            else:
                print(f"❓ {message_type}: {content}")
        
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
    except requests.exceptions.RequestException as e:
        # Don't print verbose error details
        return False


def wait_for_session_completion(session_id: str, timeout: int = 300, show_live: bool = False) -> dict:
    """Wait for session to complete and return result."""
    start_time = time.time()
    headers = {"Authorization": f"Bearer {DEVIN_API_KEY}"}
    last_message_count = 0
    last_status = None
    
    while True:
        if time.time() - start_time > timeout:
            return {"error": "timeout"}
        
        try:
            response = requests.get(f"{DEVIN_API_BASE}/session/{session_id}", headers=headers)
            response.raise_for_status()
            data = response.json()
            status = data.get("status_enum")
            
            # Show status changes
            if status != last_status:
                if show_live:
                    display_session_status(session_id)
                last_status = status
            
            # Display live messages if requested
            if show_live:
                last_message_count = display_live_messages(session_id, last_message_count)
            
            if status in ["completed", "failed", "stopped", "blocked"]:
                # Extract all attachments from session data
                attachments = extract_attachments_from_session_data(data)
                if attachments:
                    data["message_attachments"] = attachments
                return data
        except requests.exceptions.RequestException as e:
            print(f"Error checking session status: {e}")
        
        time.sleep(5)