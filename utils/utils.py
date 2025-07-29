"""Utility functions for attachment handling and JSON extraction."""

import requests
import json
import os
import re
from typing import Dict, List, Optional
from utils.config import DEVIN_API_KEY, DEVIN_API_BASE


def get_cache_key(repo_url: str) -> str:
    """Generate consistent cache key from repo URL."""
    return repo_url.replace("https://github.com/", "").replace("/", "_")


def get_issue_file_path(cache_dir: str, repo_url: str, issue_id: int) -> str:
    """Generate the file path for a specific issue in cache."""
    repo_key = get_cache_key(repo_url)
    return os.path.join(cache_dir, "issues", repo_key, f"issue_{issue_id}.json")


def download_json_attachments(message_attachments: List[Dict], name_filter: str = None) -> List[Dict]:
    """Download JSON files from message attachments and return list of file info.
    
    Args:
        message_attachments: List of attachment dictionaries
        name_filter: Optional prefix filter for attachment names
    
    Returns:
        List[Dict] of file info with name, data, uuid. Empty list if no files found.
    """
    
    downloaded_files = []
    
    for attachment in message_attachments:
        name = attachment.get("name", "")
        if name_filter and not name.startswith(name_filter):
            continue
        if not name.lower().endswith('.json'):
            continue
            
        # Download attachment content
        download_url = f"{DEVIN_API_BASE}/attachments/{attachment['uuid']}/{name}"
        headers = {"Authorization": f"Bearer {DEVIN_API_KEY}"}
        
        try:
            response = requests.get(download_url, headers=headers, allow_redirects=True)
            response.raise_for_status()
            content = response.content.decode('utf-8')
            data = json.loads(content)
            
            downloaded_files.append({
                "name": name,
                "data": data,
                "uuid": attachment.get("uuid")
            })
                
        except (requests.exceptions.RequestException, json.JSONDecodeError):
            continue
    
    return downloaded_files


def _parse_attachment_url(url: str) -> Optional[Dict]:
    """Parse attachment URL and return uuid, filename, and url."""
    match = re.search(r'/attachments/([^/]+)/([^/]+)$', url)
    if match:
        return {
            "uuid": match.group(1),
            "name": match.group(2),
            "url": url
        }
    return None


def extract_attachment_urls_from_messages(messages: List[Dict]) -> List[Dict]:
    """Extract attachment URLs from Devin messages."""
    attachments = []
    
    for msg in messages:
        if msg.get("type") == "devin_message":
            content = msg.get("message", "")
            if "ATTACHMENT:" in content:
                matches = re.findall(r'ATTACHMENT:"([^"]+)"', content)
                for url in matches:
                    attachment = _parse_attachment_url(url)
                    if attachment:
                        attachments.append(attachment)
    
    return attachments


def extract_attachments_from_session_data(session_data: Dict) -> List[Dict]:
    """Extract all attachments from session data (messages + structured_output)."""
    attachments = []
    seen_uuids = set()
    
    # Extract from messages
    messages = session_data.get("messages", [])
    message_attachments = extract_attachment_urls_from_messages(messages)
    for attachment in message_attachments:
        if attachment["uuid"] not in seen_uuids:
            attachments.append(attachment)
            seen_uuids.add(attachment["uuid"])
    
    # Extract from structured_output
    structured_output = session_data.get("structured_output", {})
    if structured_output and "attachments" in structured_output:
        for url in structured_output["attachments"]:
            attachment = _parse_attachment_url(url)
            if attachment and attachment["uuid"] not in seen_uuids:
                attachments.append(attachment)
                seen_uuids.add(attachment["uuid"])
    
    return attachments








def extract_pr_url_from_session(session_result: Dict) -> Optional[str]:
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


def cancel_session(session_id: str, max_attempts: int = 30) -> bool:
    """Cancel a Devin session by sending a cancellation message.
    
    Args:
        session_id: The session ID to cancel
        max_attempts: Maximum number of attempts to send the message (default: 30)
    
    Returns:
        bool: True if cancellation message was sent successfully, False otherwise
    """
    from core.session_manager import send_session_message
    import time
    
    print(f"Sending cancellation message to Devin session {session_id}...")
    
    # Keep trying to send the cancellation message
    for attempt in range(max_attempts):
        try:
            success = send_session_message(
                session_id, 
                "STOP: The user has cancelled this operation. Please stop what you are doing and mark the task as cancelled."
            )
            if success:
                print(f"Cancellation message sent successfully on attempt {attempt + 1}")
                return True
            else:
                print(f"Attempt {attempt + 1}: Session not ready yet, retrying in 10 seconds...")
                time.sleep(10)
                
        except Exception as e:
            print(f"Attempt {attempt + 1}: Error, retrying in 10 seconds...")
            time.sleep(10)
    
    print("Could not send cancellation message after maximum attempts - session may have completed")
    return False 