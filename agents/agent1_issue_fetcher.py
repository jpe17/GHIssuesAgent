"""Agent 1: Fetches GitHub issues and stores them in cache."""

import os
from typing import List, Dict
from utils.utils import get_cache_key, save_to_cache, check_cache, safe_makedirs
from core.session_manager import create_devin_session, wait_for_session_completion, extract_json_from_session
from utils.config import ISSUES_FETCH_TIMEOUT


class IssueFetcherAgent:
    """Agent 1: Fetches and caches GitHub issues."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        safe_makedirs(cache_dir)
        self.issues_dir = os.path.join(cache_dir, "issues")
        safe_makedirs(self.issues_dir)
    
    def fetch_and_cache_issues(self, repo_url: str) -> List[Dict]:
        """Fetch GitHub issues and store them in cache."""
        # Check cache first
        repo_key = get_cache_key(repo_url)
        cache_file = os.path.join(self.issues_dir, f"{repo_key}_issues.json")
        cached_issues = check_cache(cache_file)
        if cached_issues:
            print("✅ Using cached issues")
            return cached_issues
        
        # Fetch fresh issues if no cache
        prompt = f"""Fetch all open issues from {repo_url}. 
        Create one JSON file per issue named issue_1.json, issue_2.json, etc. 
        Each file should contain: {{"number": 1, "title": "...", "body": "...", "created_at": "...", "labels": [...]}}. 
        Save all files as attachments."""
        
        session_id = create_devin_session(prompt, repo_url)
        result = wait_for_session_completion(session_id, timeout=ISSUES_FETCH_TIMEOUT)
        
        # Download and save issue files
        repo_key = get_cache_key(repo_url)
        repo_issues_dir = os.path.join(self.issues_dir, repo_key)
        safe_makedirs(repo_issues_dir)
        
        downloaded_files = extract_json_from_session(result, "issue_", return_single=False)
        
        issues = []
        for file_info in downloaded_files:
            if isinstance(file_info, dict) and "name" in file_info and "data" in file_info:
                file_path = os.path.join(repo_issues_dir, file_info["name"])
                save_to_cache(file_path, file_info["data"])
                issues.append(file_info["data"])
        
        # Save to cache
        save_to_cache(cache_file, issues)
        
        return issues
    