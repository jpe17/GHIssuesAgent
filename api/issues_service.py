"""Service for fetching GitHub issues using Devin API."""

import aiohttp
from typing import List, Dict
from .session_manager import create_devin_session, wait_for_session_completion
from .config import ISSUES_FETCH_TIMEOUT


async def get_github_issues(session: aiohttp.ClientSession, repo_url: str) -> List[Dict]:
    """Get GitHub issues using Devin sessions - just the issues, no repository analysis."""
    prompt = f"""
    Please fetch all open issues from the GitHub repository {repo_url}.
    
    Return ONLY the issues as a JSON array with each issue containing:
    - number: issue number
    - title: issue title
    - body: full issue body/description
    - created_at: creation date
    - labels: array of label names
    
    Format as: [{{"number": 1, "title": "...", "body": "...", "created_at": "...", "labels": [...]}}]
    
    Focus only on fetching the issues, don't analyze the repository or code.
    """
    
    session_id = await create_devin_session(session, prompt, repo_url)
    result = await wait_for_session_completion(session, session_id, timeout=ISSUES_FETCH_TIMEOUT)
    
    # Extract structured output
    structured_output = result.get("structured_output", {})
    return structured_output.get("issues", []) 