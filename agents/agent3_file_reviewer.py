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
        issue_number = issue_data.get("issue_number", "unknown")
        print(f"Agent 3: Creating plan for issue #{issue_number}")
        
        # Prepare issue data for analysis
        issue_info = {
            "number": issue_number,
            "title": issue_data.get("issue_title"),
            "url": issue_data.get("issue_url"),
            "feasibility_score": issue_data.get("feasibility_score"),
            "complexity_score": issue_data.get("complexity_score"),
            "scope_assessment": issue_data.get("scope_assessment"),
            "technical_analysis": issue_data.get("technical_analysis")
        }
        
        # Create session with issue data in prompt
        prompt = f"""
        Create an implementation plan for this issue.
        
        Repository: {repo_url}
        Issue Info: {json.dumps(issue_info, indent=2)}
        
        Analyze the repository and create a detailed implementation plan.
        
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
        
        DO NOT implement anything. Only create the plan document.
        """
        
        self._current_session_id = create_devin_session(prompt, repo_url)
        result = wait_for_session_completion(self._current_session_id, timeout=FULL_ANALYSIS_TIMEOUT, show_live=False)
        
        # Extract plan data from attachments
        message_attachments = result.get("message_attachments", [])
        downloaded_files = download_json_attachments(message_attachments, "plan")
        
        if not downloaded_files:
            # Try to extract from message content as fallback
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
        else:
            plan_data = downloaded_files[0]["data"]
        
        # Display plan
        print("\n=== IMPLEMENTATION PLAN ===")
        if "action_plan" in plan_data:
            for i, step in enumerate(plan_data["action_plan"], 1):
                print(f"{i}. {step.get('description', 'No description')}")
                if step.get('files'):
                    print(f"   Files: {', '.join(step['files'])}")
        else:
            print(json.dumps(plan_data, indent=2))
        
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