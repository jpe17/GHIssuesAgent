"""Simple FastAPI routes for GitHub Issues Agent frontend."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent1_issue_fetcher import IssueFetcherAgent
from agents.agent2_feasibility_analyzer import FeasibilityAnalyzerAgent
from agents.agent3_plan import PlanAgent
from agents.agent4_executor import ExecutorAgent
from utils.utils import get_issue_file_path

router = APIRouter()

# Request models
class RepoRequest(BaseModel):
    repo_url: str

class IssueRequest(BaseModel):
    repo_url: str
    issue_id: str

class MultiIssueRequest(BaseModel):
    repo_url: str
    issue_ids: list[str]

@router.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main frontend page."""
    with open("app/static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@router.post("/api/fetch-issues")
async def fetch_issues(request: RepoRequest):
    """Fetch issues from a repository."""
    try:
        print(f"🔄 Fetching issues from: {request.repo_url}")
        
        agent = IssueFetcherAgent()
        issues_data = agent.fetch_and_cache_issues(request.repo_url)
        
        # Convert to frontend format
        issues = []
        for issue_data in issues_data:
            issues.append({
                "id": str(issue_data.get('number', '')),
                "title": issue_data.get('title', 'No title'),
                "state": issue_data.get('state', 'open'),
                "body": issue_data.get('body', ''),
                "created_at": issue_data.get('created_at', ''),
                "updated_at": issue_data.get('updated_at', '')
            })
        
        issues.sort(key=lambda x: int(x["id"]))
        print(f"✅ Fetched {len(issues)} issues")
        return {"issues": issues}
            
    except Exception as e:
        print(f"❌ Error fetching issues: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch issues: {str(e)}")

def analyze_single_issue(repo_url: str, issue_id: str, delay_seconds: float = 0) -> dict:
    """Analyze a single issue with proper rate limiting."""
    try:
        # Initial delay before any API calls
        if delay_seconds > 0:
            print(f"⏱️  Initial delay: waiting {delay_seconds}s for issue #{issue_id}")
            time.sleep(delay_seconds)
        
        # Check cache status
        from utils.utils import get_cache_file_path, check_cache
        feasibility_cache = get_cache_file_path("cache", repo_url, "feasibility", issue_id)
        plan_cache = get_cache_file_path("cache", repo_url, "plan", issue_id)
        
        feasibility_cached = check_cache(feasibility_cache)
        plan_cached = check_cache(plan_cache)
        
        print(f"🎯 Analyzing issue #{issue_id} (feasibility_cached: {feasibility_cached}, plan_cached: {plan_cached})")
        
        # Load issue
        issue_file_path = get_issue_file_path("cache", repo_url, issue_id)
        if not os.path.exists(issue_file_path):
            return {"issue_id": issue_id, "error": "Issue not found"}
        
        with open(issue_file_path, 'r') as f:
            issue = json.load(f)
        
        # Run Agent 2 & 3 in parallel with staggered start
        print(f"🚀 Running Agent 2 & 3 in parallel for issue #{issue_id}")
        
        def run_agent2():
            if not feasibility_cached:
                time.sleep(2.0)  # 2 second delay before Agent 2
            agent2 = FeasibilityAnalyzerAgent()
            return agent2.analyze_issue_feasibility(issue, repo_url)
        
        def run_agent3():
            if not plan_cached:
                time.sleep(4.0)  # 4 second delay before Agent 3 (2s after Agent 2)
            agent3 = PlanAgent()
            return agent3.review_files_and_plan(issue, repo_url)
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_agent2 = executor.submit(run_agent2)
            future_agent3 = executor.submit(run_agent3)
            
            analysis = future_agent2.result()
            plan = future_agent3.result()
        
        print(f"✅ Analysis completed for issue #{issue_id}")
        
        return {
            "issue_id": issue_id,
            "status": "completed",
            "analysis": analysis,
            "plan": plan
        }
        
    except Exception as e:
        print(f"❌ Analysis failed for issue #{issue_id}: {str(e)}")
        return {"issue_id": issue_id, "error": str(e)}

@router.post("/api/analyze-issue")
async def analyze_issue(request: IssueRequest):
    """Analyze a specific issue."""
    try:
        result = analyze_single_issue(request.repo_url, request.issue_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/analyze-multiple-issues")
async def analyze_multiple_issues(request: MultiIssueRequest):
    """Analyze multiple issues with conservative rate limiting."""
    try:
        print(f"🔍 Analyzing {len(request.issue_ids)} issues with conservative rate limiting")
        
        # Single worker to ensure semaphore works properly
        # Process issues in parallel with staggered timing
        max_workers = len(request.issue_ids)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i, issue_id in enumerate(request.issue_ids):
                # 2 second delay between issues
                delay = i * 2.0
                future = executor.submit(analyze_single_issue, request.repo_url, issue_id, delay)
                futures.append(future)
            
            results = [future.result() for future in futures]
        
        print(f"✅ Completed analysis of {len(results)} issues")
        return {"results": results}
        
    except Exception as e:
        print(f"❌ Multiple analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def execute_single_issue(repo_url: str, issue_id: str, delay_seconds: float = 0) -> dict:
    """Execute a single issue with proper rate limiting."""
    try:
        # Initial delay before any API calls
        if delay_seconds > 0:
            print(f"⏱️  Initial delay: waiting {delay_seconds}s for execution of issue #{issue_id}")
            time.sleep(delay_seconds)
            
        print(f"🚀 Executing issue #{issue_id}")
        
        # Load issue
        issue_file_path = get_issue_file_path("cache", repo_url, issue_id)
        if not os.path.exists(issue_file_path):
            return {"issue_id": issue_id, "error": "Issue not found"}
        
        with open(issue_file_path, 'r') as f:
            issue = json.load(f)
        
        # Get plan
        agent3 = PlanAgent()
        plan = agent3.review_files_and_plan(issue, repo_url)
        
        if not plan:
            return {"issue_id": issue_id, "error": "No plan available"}
        
        # Execute the plan
        agent4 = ExecutorAgent()
        push_result = agent4.execute_and_push(plan, repo_url)
        
        print(f"✅ Execution completed for issue #{issue_id}")
        
        return {
            "issue_id": issue_id,
            "status": "completed",
            "result": push_result,
            "pr_url": push_result.get("pr_url") if push_result else None
        }
        
    except Exception as e:
        print(f"❌ Execution failed for issue #{issue_id}: {str(e)}")
        return {"issue_id": issue_id, "error": str(e)}

@router.post("/api/execute")
async def execute_changes(request: IssueRequest):
    """Execute the plan and push changes."""
    try:
        result = execute_single_issue(request.repo_url, request.issue_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        print(f"❌ Execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/execute-multiple-issues")
async def execute_multiple_issues(request: MultiIssueRequest):
    """Execute multiple issues with rate limiting."""
    try:
        print(f"🚀 Executing {len(request.issue_ids)} issues with rate limiting")
        
        # Process issues in parallel with staggered timing
        max_workers = len(request.issue_ids)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i, issue_id in enumerate(request.issue_ids):
                # 2 second delay between issues
                delay = i * 2.0
                future = executor.submit(execute_single_issue, request.repo_url, issue_id, delay)
                futures.append(future)
            
            results = [future.result() for future in futures]
        
        print(f"✅ Completed execution of {len(results)} issues")
        return {"results": results}
        
    except Exception as e:
        print(f"❌ Multiple execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
