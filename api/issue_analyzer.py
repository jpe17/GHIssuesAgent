"""Service for analyzing GitHub issues using two-phase approach."""

import aiohttp
from typing import List, Dict
from .session_manager import create_devin_session, wait_for_session_completion
from .repository_scanner import scan_repository_for_relevant_files
from .config import TARGETED_ANALYSIS_TIMEOUT, FULL_ANALYSIS_TIMEOUT


async def analyze_issue_with_devin_context(session: aiohttp.ClientSession, issue_content: str, repo_url: str, issue_number: int) -> Dict:
    """Two-phase analysis: scan for relevant files, then deep analysis."""
    
    print(f"Starting two-phase analysis for issue #{issue_number}")
    
    # Phase 1: Quick scan to identify relevant files
    print("Phase 1: Scanning repository for relevant files...")
    try:
        relevant_files = await scan_repository_for_relevant_files(session, repo_url, issue_content)
        print(f"Identified {len(relevant_files)} relevant files")
    except Exception as e:
        print(f"Scan failed, falling back to full analysis: {e}")
        relevant_files = []
    
    # Phase 2: Deep analysis of relevant files
    print("Phase 2: Performing deep analysis...")
    
    if relevant_files:
        # Use targeted analysis with identified files
        prompt = f"""
        Analyze this GitHub issue with focused deep analysis of the most relevant files:
        
        Issue #{issue_number}:
        {issue_content}
        
        Relevant files identified: {', '.join(relevant_files)}
        
        Please perform a detailed analysis of these specific files and provide comprehensive insights as JSON:
        
        1. **Scope Assessment**: 
           - size: Small/Medium/Large
           - complexity: Low/Medium/High
           - impact: Local/Module-wide/System-wide
        
        2. **Confidence Score**: 0-100 based on clarity and feasibility
        
        3. **Technical Analysis**:
           - files_to_modify: Specific files that need changes (from the relevant files list)
           - dependencies: Dependencies that might be affected
           - risks: Potential risks or challenges
           - code_changes: Specific changes needed in each file
        
        4. **Effort Estimation**:
           - hours: Estimated hours for implementation
           - testing: Testing requirements
           - documentation: Documentation needs
        
        5. **Action Plan**: Step-by-step implementation approach
        
        6. **Related Considerations**: Similar issues, conflicts, performance implications
        
        IMPORTANT: Focus your analysis on the identified relevant files. Provide specific, actionable insights.
        Return as JSON with keys: scope_assessment, confidence_score, technical_analysis, effort_estimation, action_plan, related_considerations
        """
        timeout = TARGETED_ANALYSIS_TIMEOUT
    else:
        # Fallback to full repository analysis
        print("Using fallback: full repository analysis")
        prompt = f"""
        Analyze this GitHub issue in the context of the repository {repo_url}:
        
        Issue #{issue_number}:
        {issue_content}
        
        Please analyze the issue by examining the repository codebase and provide a comprehensive analysis as JSON:
        
        1. **Scope Assessment**: 
           - size: Small/Medium/Large
           - complexity: Low/Medium/High
           - impact: Local/Module-wide/System-wide
        
        2. **Confidence Score**: 0-100 based on clarity and feasibility
        
        3. **Technical Analysis**:
           - files: List of files that need to be modified
           - dependencies: Dependencies that might be affected
           - risks: Potential risks or challenges
        
        4. **Effort Estimation**:
           - hours: Estimated hours for implementation
           - testing: Testing requirements
           - documentation: Documentation needs
        
        5. **Action Plan**: Step-by-step implementation approach
        
        6. **Related Considerations**: Similar issues, conflicts, performance implications
        
        IMPORTANT: Analyze the actual codebase to understand the context and provide accurate assessments.
        Return as JSON with keys: scope_assessment, confidence_score, technical_analysis, effort_estimation, action_plan, related_considerations
        """
        timeout = FULL_ANALYSIS_TIMEOUT
    
    session_id = await create_devin_session(session, prompt, repo_url)
    result = await wait_for_session_completion(session, session_id, timeout=timeout)
    
    # Extract structured output
    structured_output = result.get("structured_output", {})
    
    return {
        "score": structured_output.get("confidence_score", 0),
        "action": structured_output.get("action_plan", "No action plan available"),
        "scope": structured_output.get("scope_assessment", {}),
        "technical_analysis": structured_output.get("technical_analysis", {}),
        "effort_estimation": structured_output.get("effort_estimation", {}),
        "related_considerations": structured_output.get("related_considerations", {}),
        "analysis_method": "targeted" if relevant_files else "full_repository",
        "files_analyzed": relevant_files if relevant_files else "full_repository"
    } 