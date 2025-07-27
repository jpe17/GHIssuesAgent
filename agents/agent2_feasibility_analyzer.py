"""Agent 2: Calculates feasibility and complexity scores for GitHub issues."""

import json
import os
import re
from typing import Dict, List
from core.session_manager import create_devin_session, wait_for_session_completion
from utils.utils import extract_json_from_attachments, extract_json_from_message_content, get_cache_key
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
        
        # Analyze with Devin
        prompt = f"""
        Analyze this GitHub issue for feasibility and complexity:
        
        Repository: {repo_url}
        Issue #{issue_number}:
        Title: {issue.get('title', 'No title')}
        Body: {issue.get('body', 'No description')}
        Labels: {issue.get('labels', [])}
        
        IMPORTANT: 
        1. Complete the task fully - do not wait for further instructions
        2. Mark the task as complete when done
        3. Save results as JSON attachment if possible
        
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
        Complete the task and mark as done.
        """
        
        session_id = create_devin_session(prompt, repo_url)
        result = wait_for_session_completion(session_id, timeout=FULL_ANALYSIS_TIMEOUT)
        
        # Extract analysis data
        analysis_data = self._extract_analysis_data(result)
        
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
    
    def analyze_multiple_issues(self, issues: List[Dict], repo_url: str) -> List[Dict]:
        """Analyze multiple issues and return sorted by feasibility."""
        print(f"Agent 2: Analyzing {len(issues)} issues for feasibility")
        
        results = []
        for issue in issues:
            try:
                analysis = self.analyze_issue_feasibility(issue, repo_url)
                results.append(analysis)
            except Exception as e:
                print(f"Error analyzing issue #{issue.get('number', 'unknown')}: {e}")
                # Add fallback analysis
                results.append({
                    "issue_number": issue.get("number", "unknown"),
                    "issue_title": issue.get("title", ""),
                    "feasibility_score": 0,
                    "complexity_score": 100,
                    "confidence": 0,
                    "error": str(e)
                })
        
        # Sort by feasibility score (highest first)
        results.sort(key=lambda x: x.get("feasibility_score", 0), reverse=True)
        
        return results
    
    def _extract_analysis_data(self, result: Dict) -> Dict:
        """Extract analysis data from Devin session result."""
        # Try attachments first (same as Agent 1)
        attachments = result.get("attachments", [])
        print(f"Found {len(attachments)} attachments")
        if attachments:
            json_data = extract_json_from_attachments(attachments)
            if json_data and isinstance(json_data, dict):
                print("Extracted JSON from attachments")
                return json_data
        
        # Try message attachments (same as Agent 1)
        message_attachments = result.get("message_attachments", [])
        print(f"Found {len(message_attachments)} message attachments")
        if message_attachments:
            json_data = extract_json_from_attachments(message_attachments)
            if json_data and isinstance(json_data, dict):
                print("Extracted JSON from message attachments")
                return json_data
        
        # Try to parse the analysis from the message text
        messages = result.get("messages", [])
        for message in reversed(messages):
            if message.get("type") == "devin_message":
                content = message.get("message", "")
                # Look for feasibility score in the text
                if "Feasibility Score:" in content:
                    try:
                        # Extract scores from text
                        feasibility_match = re.search(r'Feasibility Score:\s*(\d+)', content)
                        complexity_match = re.search(r'Complexity Score:\s*(\d+)', content)
                        hours_match = re.search(r'Estimated Effort:\s*(\d+)', content)
                        
                        if feasibility_match and complexity_match:
                            return {
                                "feasibility_score": int(feasibility_match.group(1)),
                                "complexity_score": int(complexity_match.group(1)),
                                "confidence": 80,  # High confidence if we found scores
                                "scope_assessment": {"size": "Small", "impact": "Local"},
                                "technical_analysis": {"estimated_files": [], "dependencies": [], "risks": []},
                                "effort_estimation": {
                                    "hours": int(hours_match.group(1)) if hours_match else 8,
                                    "testing": "Basic",
                                    "documentation": "Minimal"
                                }
                            }
                    except:
                        pass
        
        # Return default analysis if nothing found
        return {
            "feasibility_score": 50,
            "complexity_score": 50,
            "confidence": 0,
            "scope_assessment": {"size": "Medium", "impact": "Local"},
            "technical_analysis": {"estimated_files": [], "dependencies": [], "risks": []},
            "effort_estimation": {"hours": 8, "testing": "Basic", "documentation": "Minimal"}
        } 