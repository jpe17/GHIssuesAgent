"""High-level business workflows for GitHub Issues processing."""

import json
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor

from agents.agent1_issue_fetcher import IssueFetcherAgent
from agents.agent2_feasibility_analyzer import FeasibilityAnalyzerAgent
from agents.agent3_plan import PlanAgent
from agents.agent4_executor import ExecutorAgent
from core.session_manager import safe_devin_api_call
from utils.utils import load_issue, get_cache_file_path, check_cache


def fetch_repository_issues(repo_url: str) -> List[Dict]:
    """Fetch and cache issues from a repository."""
    agent = IssueFetcherAgent()
    issues_data = safe_devin_api_call(agent.fetch_and_cache_issues, repo_url)
    
    # Convert to frontend format
    issues = [{
        "id": str(issue_data.get('number', '')),
        "title": issue_data.get('title', 'No title'),
        "state": issue_data.get('state', 'open'),
        "body": issue_data.get('body', ''),
        "created_at": issue_data.get('created_at', ''),
        "updated_at": issue_data.get('updated_at', '')
    } for issue_data in issues_data]
    
    issues.sort(key=lambda x: int(x["id"]))
    return issues


def process_issue_parallel(repo_url: str, issue_id: str) -> Dict:
    """Run feasibility and planning in parallel for one issue."""
    try:
        issue = load_issue(repo_url, issue_id)
        
        def run_feasibility():
            cache_path = get_cache_file_path("cache", repo_url, "feasibility", issue_id)
            if check_cache(cache_path):
                with open(cache_path, 'r') as f:
                    return json.load(f)
            agent = FeasibilityAnalyzerAgent()
            return safe_devin_api_call(agent.analyze_issue_feasibility, issue, repo_url)
        
        def run_planning():
            cache_path = get_cache_file_path("cache", repo_url, "plan", issue_id)
            if check_cache(cache_path):
                with open(cache_path, 'r') as f:
                    return json.load(f)
            agent = PlanAgent()
            return safe_devin_api_call(agent.review_files_and_plan, issue, repo_url)
        
        # Run both in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            feasibility_future = executor.submit(run_feasibility)
            plan_future = executor.submit(run_planning)
            
            analysis = feasibility_future.result()
            plan = plan_future.result()
        
        return {
            "issue_id": issue_id,
            "status": "completed",
            "analysis": analysis,
            "plan": plan
        }
        
    except FileNotFoundError:
        return {"issue_id": issue_id, "error": "Issue not found"}
    except Exception as e:
        return {"issue_id": issue_id, "error": str(e)}


def execute_issue_plan(repo_url: str, issue_id: str) -> Dict:
    """Execute the plan for an issue and create PR."""
    try:
        issue = load_issue(repo_url, issue_id)
        
        # Get the plan first
        plan_agent = PlanAgent()
        plan = safe_devin_api_call(plan_agent.review_files_and_plan, issue, repo_url)
        
        if not plan:
            return {"issue_id": issue_id, "error": "No plan available"}
        
        # Execute the plan
        executor_agent = ExecutorAgent()
        result = safe_devin_api_call(executor_agent.execute_and_push, plan, repo_url)
        
        return {
            "issue_id": issue_id,
            "status": "completed",
            "result": result,
            "pr_url": result.get("pr_url") if result else None
        }
        
    except FileNotFoundError:
        return {"issue_id": issue_id, "error": "Issue not found"}
    except Exception as e:
        return {"issue_id": issue_id, "error": str(e)} 