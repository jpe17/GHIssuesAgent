"""Agent 4: Executes approved plans and pushes changes to GitHub."""

import json
from typing import Dict
from core.session_manager import create_devin_session, wait_for_session_completion
from utils.config import FULL_ANALYSIS_TIMEOUT


class ExecutorAgent:
    """Agent 4: Executes approved plans and pushes changes to GitHub."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self._current_session_id = None
    
    def execute_and_push(self, plan_data: Dict, repo_url: str) -> Dict:
        """Execute the plan and immediately push to GitHub."""
        print("\nAgent 4: Executing plan and pushing to GitHub...")
        
        # Create a completely new session for execution to avoid context contamination
        execution_prompt = f"""
        EXECUTE_AND_PUSH: Implement the approved plan and push to GitHub.
        
        Repository: {repo_url}
        Approved Plan: {json.dumps(plan_data, indent=2)}
        
        You must:
        1. Implement all the planned changes according to the plan
        2. Create a new branch for the changes
        3. Commit the changes with a descriptive message
        4. Push the branch to GitHub
        5. Create a pull request
        6. Report completion
        
        Start implementing immediately - the plan has been pre-approved.
        """
        
        # Create fresh session for execution
        execution_session_id = create_devin_session(execution_prompt, repo_url)
        result = wait_for_session_completion(execution_session_id, timeout=FULL_ANALYSIS_TIMEOUT, show_live=False)
        
        # Return success status based on session completion
        return {
            "status": "success" if result.get("status_enum") == "completed" else "failed",
            "session_result": result
        } 