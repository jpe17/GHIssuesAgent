"""Agent 3: Reviews files, determines action plan, and executes changes."""

import json
import os
from typing import Dict
from core.session_manager import create_devin_session, wait_for_session_completion, send_session_message
from utils.utils import upload_issue_file, download_json_attachments
from utils.config import FULL_ANALYSIS_TIMEOUT
from utils.utils import get_issue_file_path


class FileReviewerAgent:
    """Agent 3: Reviews files, creates action plan, and executes changes."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self._current_session_id = None
    
    def cancel(self):
        """Cancel the current operation by sending a cancellation message to Devin."""
        if self._current_session_id:
            from utils.utils import send_cancel_message
            send_cancel_message(self._current_session_id)
    
    def plan(self, issue: Dict, repo_url: str) -> Dict:
        """Step 1: Create a plan and STOP."""
        issue_number = issue.get("number", "unknown")
        print(f"Step 1: Creating plan for issue #{issue_number}")
        
        # Upload issue file and get URL
        file_url = upload_issue_file(self.cache_dir, repo_url, issue_number)
        
        # Create session with file URL in prompt
        prompt = f"""
        Create an implementation plan for this issue.
        
        Repository: {repo_url}
        Issue file: {file_url}
        
        Save plan as "plan.json" with this format:
        {{
            "summary": "Brief overview",
            "files_to_modify": [{{"file": "path", "changes": "description"}}],
            "implementation_steps": [{{"step": 1, "description": "what to do"}}]
        }}
        
        DO NOT implement anything. Only create the plan document.
        """
        
        self._current_session_id = create_devin_session(prompt, repo_url)
        result = wait_for_session_completion(self._current_session_id, timeout=FULL_ANALYSIS_TIMEOUT, show_live=False)
        
        # Extract plan data from message content
        from utils.utils import extract_json_from_message_content
        messages = result.get("messages", [])
        plan_data = None
        
        for msg in messages:
            if msg.get("type") == "devin_message":
                content = msg.get("message", "")
                plan_data = extract_json_from_message_content(content)
                if plan_data:
                    print("Found plan in message content")
                    break
        
        if not plan_data:
            raise ValueError("No plan JSON found in Devin session result")
        
        # Display plan
        print("\n=== PLAN ===")
        if "action_plan" in plan_data:
            for i, step in enumerate(plan_data["action_plan"], 1):
                print(f"{i}. {step.get('description', 'No description')}")
        else:
            print(json.dumps(plan_data, indent=2))
        
        return plan_data
    

    
    def execute(self, plan_data: Dict, repo_url: str) -> Dict:
        """Step 2: Execute the plan and STOP."""
        print("\nStep 2: Executing plan...")
        
        if not self._current_session_id:
            raise ValueError("No active session. Run plan() first.")
        
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
        downloaded_files = download_json_attachments(message_attachments, "execution")
        
        if not downloaded_files:
            raise ValueError("No execution JSON file found in session result")
        
        execution_data = downloaded_files[0]["data"]
        
        # Display results
        print("\n=== EXECUTION RESULTS ===")
        print(f"Status: {execution_data.get('status', 'unknown')}")
        print(f"Branch: {execution_data.get('new_branch', 'unknown')}")
        print(f"Commit: {execution_data.get('commit_message', 'unknown')}")
        
        if "changes_made" in execution_data:
            print("\nChanges made:")
            for change in execution_data["changes_made"]:
                print(f"• {change.get('file', 'unknown')}: {change.get('changes', 'unknown')}")
        
        return execution_data
    
    def push(self, execution_data: Dict, repo_url: str) -> Dict:
        """Step 3: Push to GitHub."""
        print("\nStep 3: Pushing to GitHub...")
        
        if not self._current_session_id:
            raise ValueError("No active session. Run plan() and execute() first.")
        
        push_message = f"""
        PUSH: The user approved the changes. Push to GitHub now.
        
        Execution data: {json.dumps(execution_data)}
        
        You must:
        1. Push the branch to GitHub
        2. Create a pull request if appropriate
        3. Save push results as JSON attachment named "push.json"
        4. STOP
        
        The push results should include:
        - status: "completed" or "failed"
        - push_url: URL of the pushed branch/PR
        - branch_name: name of the pushed branch
        - summary: summary of what was pushed
        
        Save as "push.json" attachment, then STOP.
        """
        
        success = send_session_message(self._current_session_id, push_message)
        if not success:
            raise ValueError("Failed to send push command")
        
        result = wait_for_session_completion(self._current_session_id, timeout=FULL_ANALYSIS_TIMEOUT, show_live=False)
        
        # Extract push results
        message_attachments = result.get("message_attachments", [])
        downloaded_files = download_json_attachments(message_attachments, "push")
        
        if not downloaded_files:
            raise ValueError("No push JSON file found in session result")
        
        push_data = downloaded_files[0]["data"]
        
        # Display results
        print("\n=== PUSH RESULTS ===")
        print(f"Status: {push_data.get('status', 'unknown')}")
        if push_data.get('status') == 'completed':
            print(f"URL: {push_data.get('push_url', 'unknown')}")
            print("Successfully pushed to GitHub!")
        else:
            print(f"Push failed: {push_data.get('reason', 'unknown')}")
        
        return push_data 