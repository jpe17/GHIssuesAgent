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