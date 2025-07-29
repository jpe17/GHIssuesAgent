"""Agent 4: Executes approved plans and pushes changes to GitHub."""

import json
from typing import Dict
from core.session_manager import create_devin_session, wait_for_execution_completion, extract_pr_url_from_session
from utils.config import EXECUTION_TIMEOUT


class ExecutorAgent:
    """Agent 4: Executes approved plans and pushes changes to GitHub."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
    
    def execute_and_push(self, plan_data: Dict, repo_url: str) -> Dict:
        """Execute the plan and immediately push to GitHub."""
        print("\nAgent 4: Executing plan and pushing to GitHub...")
        
        execution_prompt = f"""
        GOAL: Execute approved plan and create GitHub pull request.

        INSTRUCTIONS:
        • Implement all planned changes
        • Create new branch and commit changes
        • Push to GitHub and create pull request
        • Work efficiently without overthinking

        OUTPUT FORMAT:
        Final message: "PR is ready for review: https://github.com/owner/repo/pull/X"

        INPUT: Repository: {repo_url} | Plan: {plan_data}
        """
        
        session_id = create_devin_session(execution_prompt, repo_url)
        result = wait_for_execution_completion(session_id, timeout=EXECUTION_TIMEOUT, show_live=True)
        pr_url = extract_pr_url_from_session(result)
        
        return {
            "status": "success" if pr_url else "failed",
            "session_result": result,
            "pr_url": pr_url
        } 