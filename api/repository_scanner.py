"""Service for scanning repositories to identify relevant files."""

import aiohttp
from typing import List, Dict
from .session_manager import create_devin_session, wait_for_session_completion
from .config import SCAN_TIMEOUT


async def scan_repository_for_relevant_files(session: aiohttp.ClientSession, repo_url: str, issue_content: str) -> List[str]:
    """Phase 1: Quick scan to identify files that might be relevant to the issue."""
    prompt = f"""
    Perform a quick scan of the repository {repo_url} to identify files that might be relevant to this issue:
    
    Issue: {issue_content}
    
    Scan strategy:
    1. Look at the first 10-20 lines of each file to understand its purpose
    2. Check file names, imports, and function signatures
    3. Identify files that are likely to be affected by this issue
    4. Focus on source code files (not docs, config, etc.)
    
    Return as JSON:
    {{
        "relevant_files": [
            {{
                "path": "file path",
                "relevance_score": 1-10,
                "reason": "why this file is relevant"
            }}
        ],
        "total_files_scanned": <number>,
        "scan_summary": "brief summary of what was found"
    }}
    
    Limit to top 10-15 most relevant files. Focus on files with relevance_score >= 7.
    """
    
    session_id = await create_devin_session(session, prompt, repo_url)
    result = await wait_for_session_completion(session, session_id, timeout=SCAN_TIMEOUT)
    
    structured_output = result.get("structured_output", {})
    relevant_files = structured_output.get("relevant_files", [])
    
    # Sort by relevance score and return top files
    sorted_files = sorted(relevant_files, key=lambda x: x.get("relevance_score", 0), reverse=True)
    top_files = [f["path"] for f in sorted_files[:10]]  # Top 10 most relevant
    
    print(f"Scan complete: {structured_output.get('total_files_scanned', 0)} files scanned")
    print(f"Found {len(top_files)} relevant files: {top_files}")
    
    return top_files 