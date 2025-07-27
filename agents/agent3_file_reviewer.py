"""Agent 3: Reviews files, determines action plan, and executes changes."""

import json
import os
import requests
from typing import Dict, List, Optional
from core.session_manager import create_devin_session, wait_for_session_completion, send_session_message
from utils.utils import get_cache_key, download_json_attachments
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
        
        # Check cache first for the plan
        cache_file = os.path.join(self.cache_dir, f"file_review_{get_cache_key(repo_url)}_{issue_number}.json")
        if os.path.exists(cache_file):
            print(f"Found cached file review for issue #{issue_number}")
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        # Upload issue file and get URL
        file_url = self._upload_issue_file(repo_url, issue_number)
        
        # Review files with Devin
        prompt = f"""
        Review the repository {repo_url} and analyze this issue.
        
        Issue file: {file_url}
        User Input: {user_input if user_input else "No additional input provided"}
        
        Analyze the repository structure and create a detailed implementation plan.
        
        You must:
        1. Review relevant files (HTML, CSS, JS)
        2. Create a step-by-step implementation plan
        3. Save the plan as JSON attachment named "review.json"
        4. STOP - do not execute anything
        
        Return as JSON with this exact structure:
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
        
        Create the plan, save as "review.json" attachment, then STOP. Do not execute.
        """
        
        self._current_session_id = create_devin_session(prompt, repo_url)
        result = wait_for_session_completion(self._current_session_id, timeout=FULL_ANALYSIS_TIMEOUT, show_live=False)
        
        # Extract review data using utils
        message_attachments = result.get("message_attachments", [])
        downloaded_files = download_json_attachments(message_attachments, "review")
        
        if not downloaded_files:
            raise ValueError("No review JSON file found in Devin session result")
        
        review_data = downloaded_files[0]["data"]
        
        # Add metadata
        review_data.update({
            "issue_number": issue_number,
            "issue_title": issue.get("title", ""),
            "repo_url": repo_url,
            "user_input": user_input,
            "review_method": "file_review"
        })
        
        # Cache the extracted results
        with open(cache_file, 'w') as f:
            json.dump(review_data, f, indent=2)
        print(f"Cached file review for issue #{issue_number}")
        
        return review_data
    
    def _upload_issue_file(self, repo_url: str, issue_number: str) -> str:
        """Upload issue file and return URL."""
        from utils.utils import get_issue_file_path
        issue_file_path = get_issue_file_path(self.cache_dir, repo_url, issue_number)
        
        if not os.path.exists(issue_file_path):
            raise FileNotFoundError(f"Issue file not found: {issue_file_path}")
        
        from core.session_manager import upload_file
        file_url = upload_file(issue_file_path)
        print(f"Uploaded issue file: {file_url}")
        return file_url
    
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
        
        # Send execution message to the existing session
        if self._current_session_id:
            execution_message = f"""
            EXECUTE: The user approved the plan. Make the changes now.
            
            Save the execution results as JSON attachment named "execution.json" with:
            - status: "changes_made"
            - changes_made: list of files changed
            - new_branch: branch name created
            - commit_message: commit message
            - summary: summary of what was accomplished
            
            STOP before pushing to GitHub.
            """
            
            success = send_session_message(self._current_session_id, execution_message)
            if success:
                print("Sent execution command to Devin session")
                # Wait for completion
                result = wait_for_session_completion(self._current_session_id, timeout=FULL_ANALYSIS_TIMEOUT, show_live=False)
                
                # Extract execution results using utils
                message_attachments = result.get("message_attachments", [])
                downloaded_files = download_json_attachments(message_attachments, "execution")
                
                if not downloaded_files:
                    raise ValueError("No execution JSON file found in Devin session result")
                
                execution_data = downloaded_files[0]["data"]
                
                # Add metadata
                execution_data.update({
                    "issue_number": issue_number,
                    "repo_url": repo_url,
                    "execution_method": "file_changes"
                })
                
                return execution_data
            else:
                print("Failed to send execution command")
                return {
                    "status": "failed",
                    "reason": "Could not send execution command",
                    "changes_made": [],
                    "new_branch": "unknown",
                    "commit_message": "Failed to execute",
                    "summary": "Execution failed"
                }
        else:
            print("No active session found for execution")
            return {
                "status": "failed",
                "reason": "No active session",
                "changes_made": [],
                "new_branch": "unknown",
                "commit_message": "No session",
                "summary": "No active session found"
            }
    
    def push_to_github(self, execution_data: Dict, repo_url: str, user_approval: bool = False) -> Dict:
        """Phase 3: Push changes to GitHub (if user approved)."""
        if not user_approval:
            print("User did not approve push to GitHub. Changes remain local.")
            return {
                "status": "cancelled",
                "reason": "User did not approve push to GitHub",
                "changes": execution_data.get("changes_made", [])
            }
        
        issue_number = execution_data.get("issue_number", "unknown")
        print(f"Agent 3: Pushing changes to GitHub for issue #{issue_number}")
        
        # Send push message to the existing session
        if self._current_session_id:
            push_message = f"""
            PUSH: The user approved pushing to GitHub. Push the changes now.
            
            Save the push results as JSON attachment named "push.json" with:
            - status: "completed"
            - push_url: URL of the pushed branch/PR
            - summary: summary of what was pushed
            """
            
            success = send_session_message(self._current_session_id, push_message)
            if success:
                print("Sent push command to Devin session")
                # Wait for completion
                result = wait_for_session_completion(self._current_session_id, timeout=FULL_ANALYSIS_TIMEOUT, show_live=False)
                self._current_session_id = None
                
                # Extract push results using utils
                message_attachments = result.get("message_attachments", [])
                downloaded_files = download_json_attachments(message_attachments, "push")
                
                if not downloaded_files:
                    raise ValueError("No push JSON file found in Devin session result")
                
                push_data = downloaded_files[0]["data"]
                
                # Add metadata
                push_data.update({
                    "issue_number": issue_number,
                    "repo_url": repo_url,
                    "push_method": "github_push"
                })
                
                return push_data
            else:
                print("Failed to send push command")
                return {
                    "status": "failed",
                    "reason": "Could not send push command",
                    "push_url": "unknown",
                    "summary": "Push failed"
                }
        else:
            print("No active session found for push")
            return {
                "status": "failed",
                "reason": "No active session",
                "push_url": "unknown",
                "summary": "No active session found"
            } 