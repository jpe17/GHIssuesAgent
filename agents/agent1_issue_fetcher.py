"""Agent 1: Fetches GitHub issues and stores them in cache."""

import json
import os
from typing import List, Dict
from core.session_manager import create_devin_session, wait_for_session_completion
from utils.utils import extract_json_from_attachments, get_cache_key
from utils.config import ISSUES_FETCH_TIMEOUT


class IssueFetcherAgent:
    """Agent 1: Fetches and caches GitHub issues."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def fetch_and_cache_issues(self, repo_url: str) -> List[Dict]:
        """Fetch GitHub issues and store them in cache."""
        print(f"Agent 1: Fetching issues from {repo_url}")
        
        # Check cache first
        cache_file = os.path.join(self.cache_dir, f"issues_{self._get_repo_key(repo_url)}.json")
        if os.path.exists(cache_file):
            print(f"Found cached issues, loading from {cache_file}")
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        # Fetch from GitHub via Devin
        prompt = f"""Fetch all open issues from {repo_url}. Save as issues.json attachment with format: [{{"number": 1, "title": "...", "body": "...", "created_at": "...", "labels": [...]}}]. Ensure each issue has: number, title, body, created_at, labels fields."""
        
        session_id = create_devin_session(prompt, repo_url)
        result = wait_for_session_completion(session_id, timeout=ISSUES_FETCH_TIMEOUT)
        
        # Extract issues from attachments
        issues = self._extract_issues_from_result(result)
        
        # Validate and normalize issue format
        if issues:
            normalized_issues = []
            for issue in issues:
                normalized_issue = {
                    "number": issue.get("number"),
                    "title": issue.get("title", ""),
                    "body": issue.get("body", ""),
                    "created_at": issue.get("created_at", ""),
                    "labels": issue.get("labels", [])
                }
                if normalized_issue["number"]:  # Only include issues with a number
                    normalized_issues.append(normalized_issue)
            
            issues = normalized_issues
            
            # Cache the results
            with open(cache_file, 'w') as f:
                json.dump(issues, f, indent=2)
            print(f"Cached {len(issues)} issues to {cache_file}")
        
        return issues
    
    def _extract_issues_from_result(self, result: Dict) -> List[Dict]:
        """Extract issues from Devin session result."""
        # Try attachments first
        attachments = result.get("attachments", [])
        if attachments:
            json_data = extract_json_from_attachments(attachments)
            if json_data:
                if isinstance(json_data, list):
                    return json_data
                elif isinstance(json_data, dict) and "issues" in json_data:
                    return json_data["issues"]
        
        # Try message attachments
        message_attachments = result.get("message_attachments", [])
        if message_attachments:
            json_data = extract_json_from_attachments(message_attachments)
            if json_data:
                if isinstance(json_data, list):
                    return json_data
                elif isinstance(json_data, dict) and "issues" in json_data:
                    return json_data["issues"]
        
        print("No structured issues data found in response")
        return []
    
    def _get_repo_key(self, repo_url: str) -> str:
        """Generate a cache key from repo URL."""
        return get_cache_key(repo_url)
    
    def get_cached_issues(self, repo_url: str) -> List[Dict]:
        """Get cached issues for a repository."""
        cache_file = os.path.join(self.cache_dir, f"issues_{self._get_repo_key(repo_url)}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
        return []
    
    def get_single_issue(self, repo_url: str, issue_number: int) -> Dict:
        """Get a single issue by number from cache."""
        issues = self.get_cached_issues(repo_url)
        for issue in issues:
            if issue.get('number') == issue_number:
                return issue
        return None 