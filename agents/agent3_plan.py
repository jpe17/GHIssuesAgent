"""Agent 3: Creates implementation plans for GitHub issues."""

import json
from typing import Dict
from utils.utils import (
    check_cache, save_to_cache, prepare_issue_data, 
    get_cache_file_path
)
from core.session_manager import create_devin_session, wait_for_session_completion, extract_json_from_session


class PlanAgent:
    """Agent 3: Creates implementation plans for GitHub issues."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self._current_session_id = None
        self._plan_data = None
    
    def review_files_and_plan(self, issue_data: Dict, repo_url: str) -> Dict:
        """Review files and create an implementation plan."""
        issue_number = issue_data.get("number", "unknown")
        print(f"Agent 3: Creating plan for issue #{issue_number}")
        
        # Check cache first
        cache_file = get_cache_file_path(self.cache_dir, repo_url, "plan", issue_number)
        cached_result = check_cache(cache_file)
        if cached_result:
            print(f"Found cached plan for issue #{issue_number}")
            self._plan_data = cached_result
            return cached_result
        
        # Create session with issue data in prompt
        issue_info = prepare_issue_data(issue_data)
        prompt = f"""
        GOAL: Create implementation plan for GitHub issue.

        INSTRUCTIONS:
        • Analyze repository structure and issue requirements
        • Create step-by-step implementation plan
        • Identify files to modify and estimate effort
        • Save as "plan.json" attachment

        RESTRICTIONS:
        • DO NOT write, modify, or create any code files
        • DO NOT execute any commands or scripts
        • DO NOT make any changes to the repository
        • ONLY analyze and create a plan document
        • Focus on planning, not implementation

        OUTPUT FORMAT:
        {{
            "summary": "Brief overview of the implementation approach",
            "action_plan": [
                {{"step": 1, "description": "what to do", "files": ["file1.py", "file2.py"]}},
                {{"step": 2, "description": "what to do next", "files": ["file3.py"]}}
            ],
            "estimated_effort": "Small/Medium/Large",
            "risks": ["risk1", "risk2"],
            "dependencies": ["dep1", "dep2"]
        }}

        INPUT: Repository: {repo_url} | Issue: {issue_info}
        """
        
        session_id = create_devin_session(prompt, repo_url)
        result = wait_for_session_completion(session_id, show_live=False)
        plan_data = extract_json_from_session(result, "plan")
        
        # Add issue metadata and cache
        plan_data.update({
            "issue_number": issue_data.get("number"),
            "issue_title": issue_data.get("title"),
        })
        
        # Cache the result
        cache_file = get_cache_file_path(self.cache_dir, repo_url, "plan", issue_number)
        save_to_cache(cache_file, plan_data)
        print(f"Cached plan for issue #{issue_number}")
        
        self._plan_data = plan_data
        return plan_data
    
    def get_stored_plan(self) -> Dict:
        """Get the stored plan data from the last planning session."""
        return self._plan_data