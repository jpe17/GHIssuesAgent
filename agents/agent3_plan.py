"""Agent 3: Creates implementation plans for GitHub issues."""

import json
import os
from typing import Dict
from core.session_manager import create_devin_session, wait_for_session_completion
from utils.utils import download_json_attachments, get_cache_key
from utils.config import FULL_ANALYSIS_TIMEOUT


class PlanAgent:
    """Agent 3: Creates implementation plans for GitHub issues."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self._current_session_id = None
        self._plan_data = None  # Store plan data between sessions
    
    def review_files_and_plan(self, issue_data: Dict, repo_url: str) -> Dict:
        """Review files and create an implementation plan."""
        issue_number = issue_data.get("number", "unknown")
        print(f"Agent 3: Creating plan for issue #{issue_number}")
        
        # Check cache first
        cache_file = os.path.join(self.cache_dir, f"plan_{get_cache_key(repo_url)}_{issue_number}.json")
        if os.path.exists(cache_file):
            print(f"Found cached plan for issue #{issue_number}")
            with open(cache_file, 'r') as f:
                plan_data = json.load(f)
                self._plan_data = plan_data
                return plan_data
        
        # Prepare issue data for analysis (only include non-null fields)
        issue_info = {
            "number": issue_data.get("number"),
            "title": issue_data.get("title"),
            "body": issue_data.get("body"),
            "labels": [label.get("name") for label in issue_data.get("labels", [])],
            "created_at": issue_data.get("created_at")
        }
        
        # Create session with issue data in prompt
        prompt = f"""
        TASK: Create a plan for this GitHub issue.
        
        CRITICAL INSTRUCTIONS:
        - ONLY analyze the repository and create a plan
        - DO NOT implement any code changes
        - DO NOT create any files
        - DO NOT modify any existing code
        - ONLY create the plan.json file and STOP
        - Wait for further instructions after creating the plan
        
        Your task is to:
        1. Analyze the repository structure
        2. Understand the issue requirements
        3. Create a detailed implementation plan
        4. Save the plan as "plan.json" attachment
        5. STOP and wait for user approval
        
        Plan format:
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
        DO NOT IMPLEMENT ANY CHANGES - ONLY CREATE THE PLAN AND STOP.
        
        Repository: {repo_url}
        Issue Info: {json.dumps(issue_info, indent=2)}
        """
        
        self._current_session_id = create_devin_session(prompt, repo_url)
        result = wait_for_session_completion(self._current_session_id, timeout=FULL_ANALYSIS_TIMEOUT, show_live=False)
        
        # Extract plan data from attachments
        message_attachments = result.get("message_attachments", [])
        plan_files = download_json_attachments(message_attachments, "plan")
        
        if not plan_files:
            raise ValueError("No plan JSON file found in Devin session result")
        
        plan_data = plan_files[0]["data"]  # Get first plan file
        
        # Add issue metadata to the result
        plan_data.update({
            "issue_number": issue_data.get("number"),
            "issue_title": issue_data.get("title"),
        })
        
        # Cache the results
        with open(cache_file, 'w') as f:
            json.dump(plan_data, f, indent=2)
        print(f"Cached plan for issue #{issue_number}")
        
        # Store plan data for later execution
        self._plan_data = plan_data
        return plan_data
    
    def get_stored_plan(self) -> Dict:
        """Get the stored plan data from the last planning session."""
        return self._plan_data