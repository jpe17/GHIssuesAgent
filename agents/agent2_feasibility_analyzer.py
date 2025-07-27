"""Agent 2: Calculates feasibility and complexity scores for GitHub issues."""

import json
import os
from typing import Dict, List
from core.session_manager import create_devin_session, wait_for_session_completion, upload_file
from utils.utils import get_cache_key, download_json_attachments
from utils.config import FULL_ANALYSIS_TIMEOUT


class FeasibilityAnalyzerAgent:
    """Agent 2: Analyzes issue feasibility and complexity."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def analyze_issue_feasibility(self, issue: Dict, repo_url: str) -> Dict:
        """Analyze a single issue for feasibility and complexity."""
        issue_number = issue.get("number", "unknown")
        print(f"Agent 2: Analyzing feasibility for issue #{issue_number}")
        
        # Check cache first
        cache_file = os.path.join(self.cache_dir, f"feasibility_{get_cache_key(repo_url)}_{issue_number}.json")
        if os.path.exists(cache_file):
            print(f"Found cached analysis for issue #{issue_number}")
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        # Upload issue file and get URL
        file_url = self._upload_issue_file(repo_url, issue_number)
        
        # Analyze with Devin
        prompt = f"""
        Analyze this GitHub issue for feasibility and complexity.
        
        Repository: {repo_url}
        Issue file: {file_url}
        
        IMPORTANT: 
        1. Complete the task fully - do not wait for further instructions
        2. Mark the task as complete when done
        3. Save the analysis as JSON attachment named "analysis.json"
        
        Provide a comprehensive analysis as JSON:
        
        1. **Feasibility Score**: 0-100 (how likely this can be implemented)
        2. **Complexity Score**: 0-100 (how complex the implementation would be)
        3. **Scope Assessment**: 
           - size: Small/Medium/Large
           - impact: Local/Module-wide/System-wide
        4. **Technical Analysis**:
           - estimated_files: List of files that might need changes
           - dependencies: Dependencies that might be affected
           - risks: Potential risks or challenges
        5. **Effort Estimation**:
           - hours: Estimated hours for implementation
           - testing: Testing requirements
           - documentation: Documentation needs
        6. **Confidence**: 0-100 based on clarity and feasibility
        
        Return as JSON with keys: feasibility_score, complexity_score, scope_assessment, 
        technical_analysis, effort_estimation, confidence
        
        Save the analysis as "analysis.json" attachment and mark the task as done.
        """
        
        session_id = create_devin_session(prompt, repo_url)
        result = wait_for_session_completion(session_id, timeout=FULL_ANALYSIS_TIMEOUT, show_live=False)
        
        # Extract analysis data using utils
        message_attachments = result.get("message_attachments", [])
        downloaded_files = download_json_attachments(message_attachments, "analysis")
        
        if not downloaded_files:
            raise ValueError("No analysis JSON file found in Devin session result")
        
        analysis_data = downloaded_files[0]["data"]
        
        # Add issue metadata
        analysis_data.update({
            "issue_number": issue_number,
            "issue_title": issue.get("title", ""),
            "repo_url": repo_url,
            "analysis_method": "feasibility_analysis"
        })
        
        # Cache the results
        with open(cache_file, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        print(f"Cached feasibility analysis for issue #{issue_number}")
        
        return analysis_data
    
    def _upload_issue_file(self, repo_url: str, issue_number: str) -> str:
        """Upload issue file and return URL."""
        from utils.utils import get_issue_file_path
        issue_file_path = get_issue_file_path(self.cache_dir, repo_url, issue_number)
        
        if not os.path.exists(issue_file_path):
            raise FileNotFoundError(f"Issue file not found: {issue_file_path}")
        
        file_url = upload_file(issue_file_path)
        print(f"Uploaded issue file: {file_url}")
        return file_url
    
    def analyze_multiple_issues(self, issues: List[Dict], repo_url: str) -> List[Dict]:
        """Analyze multiple issues and return sorted by feasibility."""
        print(f"Agent 2: Analyzing {len(issues)} issues for feasibility")
        
        results = []
        for issue in issues:
            analysis = self.analyze_issue_feasibility(issue, repo_url)
            results.append(analysis)
        
        # Sort by feasibility score (highest first)
        results.sort(key=lambda x: x.get("feasibility_score", 0), reverse=True)
        
        return results 