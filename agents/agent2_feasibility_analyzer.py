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
        # Defensive programming: ensure issue is a dict
        if isinstance(issue, str):
            print(f"❌ Error: Expected dict but got string: {issue}")
            return {"error": "Invalid issue format"}
        
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
        GOAL: Analyze GitHub issue for feasibility and complexity.

        INSTRUCTIONS:
        • Evaluate implementation feasibility (0-100)
        • Assess complexity (0-100) 
        • Identify scope, files, risks, dependencies
        • Save as "analysis.json" attachment

        RESTRICTIONS:
        • DO NOT write, modify, or create any code files
        • DO NOT execute any commands or scripts
        • DO NOT make any changes to the repository
        • ONLY analyze and create assessment document
        • Focus on analysis, not implementation

        OUTPUT FORMAT:
        JSON with keys:
        {{
            "feasibility_score": <0-100>,
            "complexity_score": <0-100>,
            "scope_assessment": {{
                "size": "Small/Medium/Large",
                "impact": "Minimal/Module-wide/System-wide"
            }},
            "technical_analysis": {{
                "estimated_files": ["file1.py", "file2.py"],
                "dependencies": ["dep1", "dep2"],
                "risks": ["risk1", "risk2"]
            }},
            "confidence": <0-100>
        }}

        INPUT: Repository: {repo_url} | Issue: {issue_data}
        """
        
        session_id = create_devin_session(prompt, repo_url)
        result = wait_for_session_completion(session_id, timeout=FULL_ANALYSIS_TIMEOUT, show_live=False)
        analysis_data = extract_json_from_session(result, "analysis")
        
        # Add issue metadata and cache
        analysis_data.update({
            "issue_number": issue.get("number"),
            "issue_title": issue.get("title"),
        })
        
        # Cache the result
        cache_file = get_cache_file_path(self.cache_dir, repo_url, "feasibility", issue_number)
        save_to_cache(cache_file, analysis_data)
        print(f"Cached feasibility analysis for issue #{issue_number}")
        
        return analysis_data 