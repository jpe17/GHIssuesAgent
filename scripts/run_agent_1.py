#!/usr/bin/env python3
"""Agent 1: Fetch GitHub issues."""

import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent1_issue_fetcher import IssueFetcherAgent


def main():
    """Run Agent 1 to fetch issues."""
    # Get repo URL
    repo_url = sys.argv[1] if len(sys.argv) > 1 else input("Repo URL: ").strip()
    if not repo_url:
        print("No repo URL")
        return
    
    # Fetch issues
    print(f"Fetching issues from {repo_url}...")
    agent = IssueFetcherAgent()
    issues = agent.fetch_and_cache_issues(repo_url)
    
    if issues:
        print(f"Found {len(issues)} issues")
        for issue in issues[:5]:  # Show first 5
            print(f"#{issue['number']}: {issue['title']}")
    else:
        print("No issues found")


if __name__ == "__main__":
    main() 