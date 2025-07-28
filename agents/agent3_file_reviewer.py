"""Agent 3: Reviews files, determines action plan, and executes changes."""

import json
import os
from typing import Dict
from core.session_manager import create_devin_session, wait_for_session_completion, send_session_message
from utils.utils import download_json_attachments
from utils.config import FULL_ANALYSIS_TIMEOUT


class FileReviewerAgent:
    """Agent 3: Reviews files, creates action plan, and executes changes."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self._current_session_id = None
    
    def review_files_and_plan(self, issue_data: Dict, repo_url: str) -> Dict:
        """Review files and create an implementation plan."""
        issue_number = issue_data.get("number", "unknown")
        print(f"Agent 3: Creating plan for issue #{issue_number}")
        
        # Prepare issue data for analysis (using original issue fields)
        issue_info = {
            "number": issue_data.get("number"),
            "title": issue_data.get("title"),
            "body": issue_data.get("body"),
            "url": issue_data.get("html_url"),
            "labels": [label.get("name") for label in issue_data.get("labels", [])],
            "state": issue_data.get("state"),
            "created_at": issue_data.get("created_at"),
            "updated_at": issue_data.get("updated_at")
        }
        
        # Create session with issue data in prompt
        prompt = f"""
        Create an implementation plan for this GitHub issue.
        
        Repository: {repo_url}
        Issue Info: {json.dumps(issue_info, indent=2)}
        
        TASK: Analyze the repository and create a detailed implementation plan.
        
        Save plan as "plan.json" with this format:
        {{
            "summary": "Brief overview of the implementation",
            "action_plan": [
                {{"step": 1, "description": "what to do", "files": ["file1.py", "file2.py"]}},
                {{"step": 2, "description": "what to do next", "files": ["file3.py"]}}
            ],
            "estimated_effort": "Small/Medium/Large",
            "risks": ["risk1", "risk2"],
            "dependencies": ["dep1", "dep2"]
        }}
        
        Save the plan as "plan.json" attachment and mark the task as done.
        """
        
        self._current_session_id = create_devin_session(prompt, repo_url)
        result = wait_for_session_completion(self._current_session_id, timeout=FULL_ANALYSIS_TIMEOUT, show_live=False)
        
        # Extract plan data from attachments
        message_attachments = result.get("message_attachments", [])
        plan_data = download_json_attachments(message_attachments, "plan")
        
        if not plan_data:
            raise ValueError("No plan JSON file found in Devin session result")
        
        return plan_data
    
    def execute_changes(self, plan_data: Dict, repo_url: str, user_approval: bool = True) -> Dict:
        """Execute the implementation plan."""
        print("\nAgent 3: Executing implementation plan...")
        
        if not self._current_session_id:
            raise ValueError("No active session. Run review_files_and_plan() first.")
        
        execution_message = f"""
        EXECUTE: The user approved the plan. Make the changes now.
        
        Plan data: {json.dumps(plan_data)}
        
        You must:
        1. Implement all the planned changes
        2. Create a new branch for the changes
        3. Commit the changes with a descriptive message
        4. Save execution results as JSON attachment named "execution.json"
        5. STOP - do not push to GitHub
        
        The execution results should include:
        - status: "changes_made"
        - changes_made: list of files changed
        - new_branch: branch name created
        - commit_message: commit message used
        - summary: summary of what was accomplished
        
        Save as "execution.json" attachment, then STOP. Do not push.
        """
        
        success = send_session_message(self._current_session_id, execution_message)
        if not success:
            raise ValueError("Failed to send execution command")
        
        result = wait_for_session_completion(self._current_session_id, timeout=FULL_ANALYSIS_TIMEOUT, show_live=False)
        
        # Extract execution results
        message_attachments = result.get("message_attachments", [])
        execution_data = download_json_attachments(message_attachments, "execution")
        
        if not execution_data:
            raise ValueError("No execution JSON file found in session result")
        
        return execution_data
    
    def push(self, execution_data: Dict, repo_url: str) -> Dict:
        """Push the changes to GitHub and create a pull request."""
        print("\nAgent 3: Pushing changes to GitHub...")
        
        if not self._current_session_id:
            raise ValueError("No active session. Run review_files_and_plan() first.")
        
        push_message = f"""
        PUSH: The user approved the execution. Push the changes to GitHub now.
        
        Execution data: {json.dumps(execution_data)}
        
        You must:
        1. Push the current branch to GitHub
        2. Create a pull request with a descriptive title and description
        3. Save push results as JSON attachment named "push.json"
        4. STOP
        
        The push results should include:
        - status: "success" or "failed"
        - pr_url: URL of the created pull request
        - branch_name: name of the pushed branch
        - reason: error message if failed
        
        Save as "push.json" attachment, then STOP.
        """
        
        success = send_session_message(self._current_session_id, push_message)
        if not success:
            raise ValueError("Failed to send push command")
        
        result = wait_for_session_completion(self._current_session_id, timeout=FULL_ANALYSIS_TIMEOUT, show_live=False)
        
        # Extract push results
        message_attachments = result.get("message_attachments", [])
        push_data = download_json_attachments(message_attachments, "push")
        
        if not push_data:
            raise ValueError("No push JSON file found in session result")
        
        return push_data 