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
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
    except (OSError, IOError):
        # Handle read-only filesystem errors gracefully
        return None
    return None


def save_to_cache(cache_file: str, data: Dict) -> None:
    """Save data to cache file."""
    try:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    except (OSError, IOError):
        # Handle read-only filesystem errors gracefully
        print(f"⚠️  Could not save to cache (read-only filesystem): {cache_file}")
        return


def safe_makedirs(path: str) -> bool:
    """Safely create directories, handling read-only filesystem."""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except (OSError, IOError):
        # Handle read-only filesystem errors gracefully
        print(f"⚠️  Could not create directory (read-only filesystem): {path}")
        return False


def prepare_issue_data(issue: Dict) -> Dict:
    """Prepare issue data for analysis by extracting non-null fields."""
    labels = issue.get("labels", [])
    # Handle both string labels and dict labels (GitHub API can return both formats)
    if labels and isinstance(labels[0], dict):
        labels = [label.get("name") for label in labels]
    
    return {
        "number": issue.get("number"),
        "title": issue.get("title"),
        "body": issue.get("body"),
        "labels": labels,
        "created_at": issue.get("created_at")
    }

def get_cache_file_path(cache_dir: str, repo_url: str, analysis_type: str, issue_number: str) -> str:
    """Generate cache file path for analysis results."""
    repo_key = get_cache_key(repo_url)
    return os.path.join(cache_dir, f"{analysis_type}_{repo_key}_{issue_number}.json")