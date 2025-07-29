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


def get_issue_file_path(cache_dir: str, repo_url: str, issue_id: str) -> str:
    """Generate the file path for a specific issue in cache."""
    repo_key = get_cache_key(repo_url)
    return os.path.join(cache_dir, "issues", repo_key, f"issue_{issue_id}.json")


def check_cache(cache_file: str) -> Optional[Dict]:
    """Check if cached data exists and return it if found."""
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
    return None


def save_to_cache(cache_file: str, data: Dict) -> None:
    """Save data to cache file."""
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(data, f, indent=2)


def prepare_issue_data(issue: Dict) -> Dict:
    """Prepare issue data for analysis by extracting non-null fields."""
    return {
        "number": issue.get("number"),
        "title": issue.get("title"),
        "body": issue.get("body"),
        "labels": [label.get("name") for label in issue.get("labels", [])],
        "created_at": issue.get("created_at")
    }


def run_devin_session(prompt: str, repo_url: str, timeout: int, show_live: bool = False) -> Dict:
    """Run a Devin session and return the result."""
    from core.session_manager import create_devin_session, wait_for_session_completion
    session_id = create_devin_session(prompt, repo_url)
    return wait_for_session_completion(session_id, timeout=timeout, show_live=show_live)


def run_devin_execution(prompt: str, repo_url: str, timeout: int, show_live: bool = False) -> Dict:
    """Run a Devin execution session and return the result."""
    from core.session_manager import create_devin_session, wait_for_execution_completion
    session_id = create_devin_session(prompt, repo_url)
    return wait_for_execution_completion(session_id, timeout=timeout, show_live=show_live)


def extract_analysis_from_session(result: Dict, analysis_type: str) -> Dict:
    """Extract analysis data from session result and add issue metadata."""
    attachments = extract_attachments_from_session_data(result)
    analysis_files = download_json_attachments(attachments, analysis_type)
    
    if not analysis_files:
        raise ValueError(f"No {analysis_type} JSON file found in Devin session result")
    
    return analysis_files[0]["data"]


def get_cache_file_path(cache_dir: str, repo_url: str, analysis_type: str, issue_number: str) -> str:
    """Generate cache file path for analysis results."""
    repo_key = get_cache_key(repo_url)
    return os.path.join(cache_dir, f"{analysis_type}_{repo_key}_{issue_number}.json")


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