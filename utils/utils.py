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


def download_attachment(uuid: str, name: str) -> Optional[str]:
    """Download an attachment from Devin."""
    download_url = f"{DEVIN_API_BASE}/attachments/{uuid}/{name}"
    headers = {"Authorization": f"Bearer {DEVIN_API_KEY}"}
    
    try:
        response = requests.get(download_url, headers=headers, allow_redirects=True)
        response.raise_for_status()
        content = response.content
        return content.decode('utf-8')
    except requests.exceptions.RequestException:
        return None


def download_json_attachments(message_attachments: List[Dict], name_filter: str = None) -> List[Dict]:
    """Download JSON files from message attachments and return parsed data."""
    results = []
    
    for attachment in message_attachments:
        name = attachment.get("name", "")
        if name_filter and not name.startswith(name_filter):
            continue
        if not name.lower().endswith('.json'):
            continue
            
        content = download_attachment(attachment["uuid"], name)
        if content:
            try:
                data = json.loads(content)
                results.append({"name": name, "data": data})
            except json.JSONDecodeError:
                continue
    
    return results


def extract_attachment_urls_from_messages(messages: List[Dict]) -> List[Dict]:
    """Extract attachment URLs from Devin messages."""
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
                        filename = match.group(2)
                        attachments.append({
                            "uuid": uuid,
                            "name": filename,
                            "url": url
                        })
    
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
            match = re.search(r'/attachments/([^/]+)/([^/]+)$', url)
            if match:
                uuid = match.group(1)
                filename = match.group(2)
                if uuid not in seen_uuids:
                    attachments.append({
                        "uuid": uuid,
                        "name": filename,
                        "url": url
                    })
                    seen_uuids.add(uuid)
    
    return attachments


def extract_json_from_attachments(attachments: List[Dict]) -> Optional[Dict]:
    """Extract JSON data from Devin session attachments."""
    for attachment in attachments:
        uuid = attachment.get("uuid")
        name = attachment.get("name")
        
        if not uuid or not name or not name.lower().endswith('.json'):
            continue
            
        content = download_attachment(uuid, name)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                continue
    
    return None


def extract_json_from_message_content(content: str) -> Optional[Dict]:
    """Extract JSON data from message content using regex."""
    try:
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except (json.JSONDecodeError, AttributeError):
        pass
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