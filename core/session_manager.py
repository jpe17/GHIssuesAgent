"""Session management for Devin API."""

import time
import requests
import json
import re
import threading
from utils.config import (
    DEVIN_API_BASE, 
    DEVIN_API_KEY,
    FULL_ANALYSIS_TIMEOUT,
    EXECUTION_TIMEOUT,
    ISSUES_FETCH_TIMEOUT,
    MIN_SECONDS_BETWEEN_CALLS
)


def create_devin_session(prompt: str, repo_url: str = None) -> str:
    """Create a Devin session and return session ID."""
    def _create_session():
        payload = {"prompt": prompt}
        if repo_url:
            payload["repository_url"] = repo_url
        
        headers = {"Authorization": f"Bearer {DEVIN_API_KEY}"}
        
        response = requests.post(f"{DEVIN_API_BASE}/sessions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["session_id"]
    
    return safe_devin_api_call(_create_session, timeout=30)


def get_session_details(session_id: str) -> dict:
    """Get detailed information about a Devin session."""
    def _get_details():
        headers = {"Authorization": f"Bearer {DEVIN_API_KEY}"}
        response = requests.get(f"{DEVIN_API_BASE}/session/{session_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    
    try:
        return safe_devin_api_call(_get_details, timeout=30)
    except Exception:
        return {}


def display_live_messages(session_id: str, last_message_count: int = 0) -> int:
    """Display new messages from a Devin session and return the new message count."""
    session_data = get_session_details(session_id)
    messages = session_data.get("messages", [])
    
    if len(messages) > last_message_count:
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


def cancel_session(session_id: str, max_attempts: int = 30) -> bool:
    """Cancel a Devin session by sending a cancellation message."""
    for attempt in range(max_attempts):
        try:
            success = send_session_message(
                session_id, 
                "STOP: The user has cancelled this operation. Please stop what you are doing and mark the task as cancelled."
            )
            if success:
                return True
            else:
                time.sleep(10)
                
        except Exception:
            time.sleep(10)
    
    return False


def wait_for_session_completion(session_id: str, timeout: int = None, show_live: bool = False) -> dict:
    """Wait for session to complete and return result."""
    if timeout is None:
        timeout = FULL_ANALYSIS_TIMEOUT
    
    start_time = time.time()
    last_message_count = 0
    
    while time.time() - start_time < timeout:
        try:
            session_data = get_session_details(session_id)
            
            if show_live:
                last_message_count = display_live_messages(session_id, last_message_count)
            
            if session_data.get("status_enum") in ["completed", "failed", "stopped", "blocked"]:
                return session_data
                
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(10)
    
    return {"error": "timeout"}


def extract_pr_url_from_session(session_result: dict) -> str | None:
    """Extract pull request URL from session messages."""
    messages = session_result.get("messages", [])
    
    for message in messages:
        if message.get("type") == "devin_message":
            content = message.get("message", "")
            # Look for PR URL pattern
            pr_match = re.search(r'https://github\.com/[^/]+/[^/]+/pull/\d+', content)
            if pr_match:
                return pr_match.group(0)
    
    return None


def download_attachment(uuid: str, name: str) -> dict:
    """Download an attachment from Devin API."""
    url = f"{DEVIN_API_BASE}/attachments/{uuid}/{name}"
    headers = {"Authorization": f"Bearer {DEVIN_API_KEY}"}
    
    try:
        response = requests.get(url, headers=headers, allow_redirects=True)
        response.raise_for_status()
        
        content = response.content
        return json.loads(content)
    except Exception as e:
        print(f"❌ Error downloading attachment {name}: {str(e)}")
        raise


def extract_attachments_from_messages(messages: list) -> list:
    """Extract attachment information from session messages."""
    attachments = []
    
    for msg in messages:
        if msg.get("type") == "devin_message":
            content = msg.get("message", "")
            
            if "ATTACHMENT:" in content:
                matches = re.findall(r'ATTACHMENT:"([^"]+)"', content)
                
                for url in matches:
                    match = re.search(r'/attachments/([^/]+)/([^/]+)$', url)
                    if match:
                        uuid = match.group(1)
                        name = match.group(2)
                        attachments.append({
                            "uuid": uuid,
                            "name": name
                        })
    
    return attachments


def extract_json_from_session(result: dict, name_filter: str = None, return_single: bool = True) -> dict | list:
    """Extract and download JSON files from Devin session result."""
    if "error" in result:
        return {"error": result["error"]}
    
    attachments = []
    if "messages" in result:
        attachments = extract_attachments_from_messages(result["messages"])
    
    downloaded_files = []
    
    for attachment in attachments:
        name = attachment.get("name", "")
        uuid = attachment.get("uuid", "")
        
        if name_filter and not name.startswith(name_filter):
            continue
        
        if not name.lower().endswith('.json'):
            continue
            
        try:
            data = download_attachment(uuid, name)
            
            if return_single:
                return data
            else:
                downloaded_files.append({
                    "name": name,
                    "data": data,
                    "uuid": uuid
                })
        except Exception:
            continue
    
    if return_single and not downloaded_files:
        raise ValueError(f"No JSON files found matching filter: {name_filter}")
    
    return downloaded_files


def wait_for_execution_completion(session_id: str, timeout: int = None, show_live: bool = False) -> dict:
    """Wait for execution session to complete, stopping early if PR is detected."""
    if timeout is None:
        timeout = EXECUTION_TIMEOUT
    
    start_time = time.time()
    last_message_count = 0
    
    while time.time() - start_time < timeout:
        try:
            session_data = get_session_details(session_id)
            
            if show_live:
                last_message_count = display_live_messages(session_id, last_message_count)
            
            # Check if PR URL is found in messages (early termination)
            if extract_pr_url_from_session(session_data):
                return session_data
            
            if session_data.get("status_enum") in ["completed", "failed", "stopped", "blocked"]:
                return session_data
                
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(10)
    
    return {"error": "timeout"}


# Simple rate limiting for all Devin API calls
last_devin_api_call = 0
devin_api_lock = threading.Lock()

def safe_devin_api_call(func, *args, timeout=None, **kwargs):
    """Make a Devin API call with rate limiting and configurable timeout."""
    global last_devin_api_call
    
    # Apply rate limiting
    with devin_api_lock:
        now = time.time()
        time_since_last_call = now - last_devin_api_call
        
        if time_since_last_call < MIN_SECONDS_BETWEEN_CALLS:
            wait_time = MIN_SECONDS_BETWEEN_CALLS - time_since_last_call
            print(f"⚠️  Rate limiting: waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
        
        last_devin_api_call = time.time()
    
    # Determine appropriate timeout based on function name if not provided
    if timeout is None:
        func_name = func.__name__ if hasattr(func, '__name__') else str(func)
        if 'fetch' in func_name.lower() or 'issue' in func_name.lower():
            timeout = ISSUES_FETCH_TIMEOUT
        elif 'execute' in func_name.lower() or 'push' in func_name.lower():
            timeout = EXECUTION_TIMEOUT
        else:
            timeout = FULL_ANALYSIS_TIMEOUT
    
    print(f"🔄 Making Devin API call with {timeout}s timeout")
    
    # Make the actual API call with retry logic
    for attempt in range(3):
        try:
            print(f"🔄 Attempt {attempt + 1}/3")
            result = func(*args, **kwargs)
            print(f"✅ Devin API call successful")
            return result
        except Exception as e:
            if "429" in str(e) or "Too Many Requests" in str(e):
                wait_time = 15 * (attempt + 1)
                print(f"⚠️  API rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                if attempt == 2:
                    raise Exception(f"API rate limited after 3 attempts: {str(e)}")
            else:
                print(f"❌ API call failed: {str(e)}")
                if attempt == 2:
                    raise
                time.sleep(5)  # Brief pause before retry