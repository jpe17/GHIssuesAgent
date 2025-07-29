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
        EXECUTE_AND_PUSH: Implement the approved plan and push to GitHub.
        
        CRITICAL: Work efficiently and complete all steps quickly.
        
        You must:
        1. Implement all the planned changes according to the plan
        2. Create a new branch for the changes
        3. Commit the changes with a descriptive message
        4. Push the branch to GitHub
        5. Create a pull request
        6. Report completion with PR URL
        
        IMPORTANT: 
        - Focus on the core implementation, avoid unnecessary analysis
        - Use the plan as your guide - don't overthink
        - Work step by step without delays
        - Include PR URL in final message: "PR is ready for review: https://github.com/owner/repo/pull/X"
        
        Start implementing immediately - the plan has been pre-approved.
                
        Repository: {repo_url}
        Approved Plan: {plan_data}
        """
        
        session_id = create_devin_session(execution_prompt, repo_url)
        result = wait_for_execution_completion(session_id, timeout=EXECUTION_TIMEOUT, show_live=True)
        pr_url = extract_pr_url_from_session(result)
        
        return {
            "status": "success" if pr_url else "failed",
            "session_result": result,
            "pr_url": pr_url
        } 