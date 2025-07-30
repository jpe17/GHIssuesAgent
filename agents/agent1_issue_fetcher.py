"""Agent 1: Fetches GitHub issues and stores them in cache."""

import os
from typing import List, Dict
from utils.utils import get_cache_key, save_to_cache, check_cache, makedir
from core.session_manager import create_devin_session, wait_for_session_completion, extract_json_from_session
from utils.config import ISSUES_FETCH_TIMEOUT


class IssueFetcherAgent:
    """Agent 1: Fetches and caches GitHub issues."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        makedir(cache_dir)
        self.issues_dir = os.path.join(cache_dir, "issues")
        makedir(self.issues_dir)
    
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
        prompt = f"""
        GOAL: Fetch all open GitHub issues and save as individual JSON files.

        INSTRUCTIONS:
        • Retrieve all open issues from {repo_url}
        • Create files: issue_1.json, issue_2.json, etc.
        • Save all files as attachments

        OUTPUT FORMAT:
        Each JSON file should contain:
        {{
            "number": <issue_number>,
            "title": "<issue_title>",
            "body": "<issue_description>",
            "created_at": "<creation_date>",
            "labels": ["label1", "label2", ...]
        }}
        """
        
        session_id = create_devin_session(prompt, repo_url)
        result = wait_for_session_completion(session_id, timeout=ISSUES_FETCH_TIMEOUT)
        
        # Download and save issue files
        repo_key = get_cache_key(repo_url)
        repo_issues_dir = os.path.join(self.issues_dir, repo_key)
        makedir(repo_issues_dir)
        
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
    