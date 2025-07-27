"""Agent 3: Reviews files, determines action plan, and executes changes."""

import json
import os
import requests
from typing import Dict, List, Optional
from core.session_manager import create_devin_session, wait_for_session_completion, send_session_message
from utils.utils import extract_json_from_attachments, extract_json_from_message_content, get_cache_key
from utils.config import FULL_ANALYSIS_TIMEOUT, DEVIN_API_BASE, DEVIN_API_KEY
import time


class FileReviewerAgent:
    """Agent 3: Reviews files, creates action plan, and executes changes."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self._current_session_id = None
    
    def cancel(self):
        """Cancel the current operation by sending a cancellation message to Devin."""
        if self._current_session_id:
            print(f"Sending cancellation message to Devin session {self._current_session_id}...")
            
            # Keep trying to send the cancellation message every 10 seconds
            max_attempts = 30  # 5 minutes max
            for attempt in range(max_attempts):
                try:
                    # First check if the session is still active
                    headers = {"Authorization": f"Bearer {DEVIN_API_KEY}"}
                    response = requests.get(f"{DEVIN_API_BASE}/session/{self._current_session_id}", headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        status = data.get("status_enum")
                        if status in ["completed", "failed", "stopped", "blocked"]:
                            print(f"Session {self._current_session_id} is already {status}, no need to cancel")
                            return
                    
                    # Try to send cancellation message
                    success = send_session_message(
                        self._current_session_id, 
                        "STOP: The user has cancelled this operation. Please stop what you are doing and mark the task as cancelled."
                    )
                    if success:
                        print(f"Cancellation message sent successfully on attempt {attempt + 1}")
                        return
                    else:
                        print(f"Attempt {attempt + 1}: Session not ready yet, retrying in 10 seconds...")
                        time.sleep(10)
                        
                except Exception as e:
                    print(f"Attempt {attempt + 1}: Error, retrying in 10 seconds...")
                    time.sleep(10)
            
            print("Could not send cancellation message after 5 minutes - session may have completed")
    
    def review_files_and_plan(self, issue: Dict, repo_url: str, user_input: str = "") -> Dict:
        """Phase 1: Review relevant files and create action plan."""
        issue_number = issue.get("number", "unknown")
        print(f"Agent 3: Reviewing files for issue #{issue_number}")
        
        # Check cache first
        cache_file = os.path.join(self.cache_dir, f"file_review_{get_cache_key(repo_url)}_{issue_number}.json")
        if os.path.exists(cache_file):
            print(f"Found cached file review for issue #{issue_number}")
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        # Review files with Devin
        prompt = f"""
        Review the repository {repo_url} and analyze this issue:
        
        Issue #{issue_number}:
        Title: {issue.get('title', 'No title')}
        Body: {issue.get('body', 'No description')}
        
        User Input: {user_input if user_input else "No additional input provided"}
        
        IMPORTANT: 
        1. Complete the task fully - do not wait for further instructions
        2. Mark the task as complete when done
        3. Save results as JSON attachment if possible
        4. If you receive a message saying "STOP", immediately stop what you are doing and mark the task as cancelled
        
        Tasks:
        1. **File Review**: Identify and read all relevant files
        2. **Action Plan**: Create detailed step-by-step implementation plan
        3. **File Changes**: Specify exact changes needed for each file
        
        Return as JSON:
        {{
            "relevant_files": [
                {{
                    "path": "file path",
                    "content": "file content or summary",
                    "changes_needed": "what needs to be changed"
                }}
            ],
            "action_plan": [
                {{
                    "step": 1,
                    "description": "what to do",
                    "files": ["files to modify"],
                    "details": "specific changes"
                }}
            ],
            "estimated_effort": "hours",
            "risks": ["potential issues"],
            "testing_plan": "how to test changes"
        }}
        
        Complete the task and mark as done.
        """
        
        self._current_session_id = create_devin_session(prompt, repo_url)
        result = wait_for_session_completion(self._current_session_id, timeout=FULL_ANALYSIS_TIMEOUT)
        self._current_session_id = None
        
        # Extract review data
        review_data = self._extract_review_data(result)
        
        # Add metadata
        review_data.update({
            "issue_number": issue_number,
            "issue_title": issue.get("title", ""),
            "repo_url": repo_url,
            "user_input": user_input,
            "review_method": "file_review"
        })
        
        # Cache the results
        with open(cache_file, 'w') as f:
            json.dump(review_data, f, indent=2)
        print(f"Cached file review for issue #{issue_number}")
        
        return review_data
    
    def execute_changes(self, review_data: Dict, repo_url: str, user_approval: bool = False) -> Dict:
        """Phase 2: Execute the planned changes (if user approved)."""
        if not user_approval:
            print("User did not approve changes. Stopping execution.")
            return {
                "status": "cancelled",
                "reason": "User did not approve changes",
                "changes": []
            }
        
        issue_number = review_data.get("issue_number", "unknown")
        print(f"Agent 3: Executing changes for issue #{issue_number}")
        
        # Create execution prompt
        action_plan = review_data.get("action_plan", [])
        relevant_files = review_data.get("relevant_files", [])
        
        prompt = f"""
        Execute the following changes for issue #{issue_number} in repository {repo_url}:
        
        Action Plan:
        {json.dumps(action_plan, indent=2)}
        
        Relevant Files:
        {json.dumps(relevant_files, indent=2)}
        
        IMPORTANT: 
        1. Complete the task fully - do not wait for further instructions
        2. Mark the task as complete when done
        3. Save results as JSON attachment if possible
        4. Make the actual file changes in the repository
        5. Create a new branch for these changes
        6. If you receive a message saying "STOP", immediately stop what you are doing and mark the task as cancelled
        
        Execute the changes and return as JSON:
        {{
            "status": "completed",
            "changes_made": [
                {{
                    "file": "file path",
                    "changes": "description of changes",
                    "branch": "branch name created"
                }}
            ],
            "new_branch": "branch name",
            "commit_message": "commit message",
            "summary": "summary of what was accomplished"
        }}
        
        Complete the task and mark as done.
        """
        
        self._current_session_id = create_devin_session(prompt, repo_url)
        result = wait_for_session_completion(self._current_session_id, timeout=FULL_ANALYSIS_TIMEOUT)
        self._current_session_id = None
        
        # Extract execution results
        execution_data = self._extract_execution_data(result)
        
        # Add metadata
        execution_data.update({
            "issue_number": issue_number,
            "repo_url": repo_url,
            "execution_method": "file_changes"
        })
        
        # Cache execution results
        cache_file = os.path.join(self.cache_dir, f"execution_{get_cache_key(repo_url)}_{issue_number}.json")
        with open(cache_file, 'w') as f:
            json.dump(execution_data, f, indent=2)
        
        return execution_data
    
    def _extract_review_data(self, result: Dict) -> Dict:
        """Extract review data from Devin session result."""
        # First try to extract from attachments
        attachments = result.get("attachments", [])
        
        if attachments:
            json_data = extract_json_from_attachments(attachments)
            if json_data and isinstance(json_data, dict):
                return json_data
        
        # Fallback: try to extract from messages
        messages = result.get("messages", [])
        if len(messages) > 1:
            for message in reversed(messages):
                if message.get("type") == "devin_message":
                    content = message.get("message", "")
                    json_data = extract_json_from_message_content(content)
                    if json_data:
                        return json_data
        
        # Return default review data if nothing found
        return {
            "relevant_files": [],
            "action_plan": [],
            "estimated_effort": "Unknown",
            "risks": ["Unable to analyze files"],
            "testing_plan": "Manual testing required"
        }
    
    def _extract_execution_data(self, result: Dict) -> Dict:
        """Extract execution data from Devin session result."""
        # First try to extract from attachments
        attachments = result.get("attachments", [])
        
        if attachments:
            json_data = extract_json_from_attachments(attachments)
            if json_data and isinstance(json_data, dict):
                return json_data
        
        # Fallback: try to extract from messages
        messages = result.get("messages", [])
        if len(messages) > 1:
            for message in reversed(messages):
                if message.get("type") == "devin_message":
                    content = message.get("message", "")
                    json_data = extract_json_from_message_content(content)
                    if json_data:
                        return json_data
        
        # Return default execution data if nothing found
        return {
            "status": "unknown",
            "changes_made": [],
            "new_branch": "unknown",
            "commit_message": "Changes for issue",
            "summary": "Unable to determine execution status"
        } 