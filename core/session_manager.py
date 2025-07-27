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


def upload_file(file_path: str) -> str:
    """Upload a file to Devin and return the file URL."""
    headers = {"Authorization": f"Bearer {DEVIN_API_KEY}"}
    
    # Debug info
    print(f"Uploading file: {file_path}")
    print(f"File size: {os.path.getsize(file_path)} bytes")
    print(f"API endpoint: {DEVIN_API_BASE}/attachments")
    
    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                f"{DEVIN_API_BASE}/attachments",
                headers=headers,
                files={"file": f}
            )
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            file_url = response.text
            print(f"Upload successful, URL: {file_url}")
            return file_url
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error Response: {e.response.text}")
        if e.response.status_code == 401:
            raise Exception(f"Unauthorized: Check your DEVIN_API_KEY. Status: {e.response.status_code}")
        elif e.response.status_code == 403:
            raise Exception(f"Forbidden: API key may not have upload permissions. Status: {e.response.status_code}")
        else:
            raise Exception(f"HTTP error uploading file {file_path}: {e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to upload file {file_path}: {e}")


def download_file_in_session(session_id: str, file_url: str) -> bool:
    """Download a file in a Devin session so it can be accessed."""
    headers = {"Authorization": f"Bearer {DEVIN_API_KEY}"}
    
    download_message = f"""
    Please download and read this file: {file_url}
    
    This file contains important information that you need to analyze.
    """
    
    try:
        response = requests.post(
            f"{DEVIN_API_BASE}/session/{session_id}/message",
            headers=headers,
            json={"message": download_message}
        )
        response.raise_for_status()
        print(f"Download message sent to session {session_id}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send download message: {e}")
        return False


def upload_file_to_session(session_id: str, file_path: str) -> bool:
    """Upload a file directly to a Devin session."""
    headers = {"Authorization": f"Bearer {DEVIN_API_KEY}"}
    
    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                f"{DEVIN_API_BASE}/session/{session_id}/upload",
                headers=headers,
                files={"file": f}
            )
            response.raise_for_status()
            print(f"File uploaded to session {session_id}")
            return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to upload file to session: {e}")
        return False


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