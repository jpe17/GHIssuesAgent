"""Utility functions for data processing and file operations."""

import json
import os
from typing import Dict, List, Optional, Union


def get_cache_key(repo_url: str) -> str:
    """Generate consistent cache key from repo URL."""
    return repo_url.replace("https://github.com/", "").replace("/", "_")


def get_issue_file_path(cache_dir: str, repo_url: str, issue_id: str) -> str:
    """Generate the file path for a specific issue in cache."""
    repo_key = get_cache_key(repo_url)
    return os.path.join(cache_dir, "issues", repo_key, f"issue_{issue_id}.json")


def check_cache(cache_file: str) -> Optional[Dict]:
    """Check if cached data exists and return it if found."""
    # Skip cache checking in Vercel environment
    if os.getenv('VERCEL') == '1':
        return None
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
    return None


def save_to_cache(cache_file: str, data: Dict) -> None:
    """Save data to cache file."""
    # Skip caching in Vercel environment
    if os.getenv('VERCEL') == '1':
        return
    
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

def get_cache_file_path(cache_dir: str, repo_url: str, analysis_type: str, issue_number: str) -> str:
    """Generate cache file path for analysis results."""
    repo_key = get_cache_key(repo_url)
    return os.path.join(cache_dir, f"{analysis_type}_{repo_key}_{issue_number}.json")