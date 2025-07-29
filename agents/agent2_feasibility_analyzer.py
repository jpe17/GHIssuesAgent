"""Agent 2: Calculates feasibility and complexity scores for GitHub issues."""

from typing import Dict
from utils.utils import (
    check_cache, save_to_cache, prepare_issue_data, 
    get_cache_file_path
)
from core.session_manager import create_devin_session, wait_for_session_completion, extract_json_from_session
from utils.config import FULL_ANALYSIS_TIMEOUT


class FeasibilityAnalyzerAgent:
    """Agent 2: Analyzes issue feasibility and complexity."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
    
    def analyze_issue_feasibility(self, issue: Dict, repo_url: str) -> Dict:
        """Analyze a single issue for feasibility and complexity."""
        issue_number = issue.get("number", "unknown")
        print(f"Agent 2: Analyzing feasibility for issue #{issue_number}")
        
        # Check cache first
        cache_file = get_cache_file_path(self.cache_dir, repo_url, "feasibility", issue_number)
        cached_result = check_cache(cache_file)
        if cached_result:
            print(f"Found cached analysis for issue #{issue_number}")
            return cached_result
        
        # Analyze with Devin
        issue_data = prepare_issue_data(issue)
        prompt = f"""
        Analyze this GitHub issue for feasibility and complexity.
        
        Repository: {repo_url}
        Issue Data: {issue_data}
        
        IMPORTANT: 
        1. Complete the task fully - do not wait for further instructions
        2. Mark the task as complete when done
        3. Save the analysis as JSON attachment named "analysis.json"
        
        Provide a comprehensive analysis as JSON:
        
        1. **Feasibility Score**: 0-100 (how likely this can be implemented)
        2. **Complexity Score**: 0-100 (how complex the implementation would be)
        3. **Scope Assessment**: 
           - size: Small/Medium/Large
           - impact: Minimal/Module-wide/System-wide
        4. **Technical Analysis**:
           - estimated_files: List of files that might need changes
           - dependencies: Dependencies that might be affected
           - risks: Potential risks or challenges
        5. **Confidence**: 0-100 based on clarity and feasibility
        
        Return as JSON with keys: feasibility_score, complexity_score, scope_assessment, 
        technical_analysis, confidence
        
        Save the analysis as "analysis.json" attachment and mark the task as done.
        """
        
        session_id = create_devin_session(prompt, repo_url)
        result = wait_for_session_completion(session_id, timeout=FULL_ANALYSIS_TIMEOUT, show_live=False)
        analysis_data = extract_json_from_session(result, "analysis")
        
        # Add issue metadata and cache
        analysis_data.update({
            "issue_number": issue.get("number"),
            "issue_title": issue.get("title"),
        })
        
        save_to_cache(cache_file, analysis_data)
        print(f"Cached feasibility analysis for issue #{issue_number}")
        
        return analysis_data 