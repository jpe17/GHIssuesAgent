"""Agent 1: Fetches GitHub issues and stores them in cache."""

import json
import os
from typing import List, Dict
from core.session_manager import create_devin_session, wait_for_session_completion
from utils.utils import get_cache_key, download_json_attachments
from utils.config import ISSUES_FETCH_TIMEOUT


class IssueFetcherAgent:
    """Agent 1: Fetches and caches GitHub issues."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        # Create issues subdirectory
        self.issues_dir = os.path.join(cache_dir, "issues")
        os.makedirs(self.issues_dir, exist_ok=True)
    
    def fetch_and_cache_issues(self, repo_url: str) -> List[Dict]:
        """Fetch GitHub issues and store them in cache."""
        print(f"Agent 1: Fetching issues from {repo_url}")
        
        # 1. Prompt
        prompt = f"""Fetch all open issues from {repo_url}. Create one JSON file per issue named issue_1.json, issue_2.json, etc. Each file should contain: {{"number": 1, "title": "...", "body": "...", "created_at": "...", "labels": [...]}}. Save all files as attachments."""
        
        session_id = create_devin_session(prompt, repo_url)
        result = wait_for_session_completion(session_id, timeout=ISSUES_FETCH_TIMEOUT)
        
        # 2. Download each file to the right folder
        repo_key = get_cache_key(repo_url)
        repo_issues_dir = os.path.join(self.issues_dir, repo_key)
        os.makedirs(repo_issues_dir, exist_ok=True)
        
        message_attachments = result.get("message_attachments", [])
        
        # Download all issue files
        downloaded_files = download_json_attachments(message_attachments, "issue_")
        
        issues = []
        for file_info in downloaded_files:
            # Save to file
            file_path = os.path.join(repo_issues_dir, file_info["name"])
            with open(file_path, 'w') as f:
                json.dump(file_info["data"], f, indent=2)
            issues.append(file_info["data"])
        
        print(f"Downloaded {len(issues)} issue files")
        return issues
    