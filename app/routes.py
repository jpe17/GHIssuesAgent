"""Simple FastAPI routes for GitHub Issues Agent frontend with simplified rate limiting."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import json
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent1_issue_fetcher import IssueFetcherAgent
from agents.agent2_feasibility_analyzer import FeasibilityAnalyzerAgent
from agents.agent3_plan import PlanAgent
from agents.agent4_executor import ExecutorAgent
from utils.utils import get_issue_file_path

router = APIRouter()

# Rate limiting for Devin API calls
import asyncio
from collections import deque
from datetime import datetime, timedelta

# Track Devin API calls for rate limiting
devin_api_calls = deque()
devin_api_lock = threading.Lock()
MAX_DEVIN_CALLS_PER_MINUTE = 10 

# Global thread pool for individual issue processing
individual_issue_executor = ThreadPoolExecutor(max_workers=6, thread_name_prefix="issue_worker")

# Request models
class RepoRequest(BaseModel):
    repo_url: str

class IssueRequest(BaseModel):
    repo_url: str
    issue_id: str

class MultiIssueRequest(BaseModel):
    repo_url: str
    issue_ids: list[str]

def safe_devin_api_call(func, *args, **kwargs):
    """Make a Devin API call with smart rate limiting."""
    with devin_api_lock:
        # Clean old calls (older than 1 minute)
        now = datetime.now()
        while devin_api_calls and (now - devin_api_calls[0]) > timedelta(minutes=1):
            devin_api_calls.popleft()
        
        # Check if we're at rate limit
        if len(devin_api_calls) >= MAX_DEVIN_CALLS_PER_MINUTE:
            # Wait until we can make another call
            oldest_call = devin_api_calls[0]
            wait_time = 60 - (now - oldest_call).total_seconds()
            if wait_time > 0:
                print(f"⚠️  Rate limit reached, waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
        
        # Record this call
        devin_api_calls.append(now)
    
    # Now make the actual API call
    for attempt in range(3):
        try:
            print(f"🔄 Making Devin API call (attempt {attempt + 1}/3)")
            result = func(*args, **kwargs)
            print(f"✅ Devin API call successful")
            return result
        except Exception as e:
            if "429" in str(e) or "Too Many Requests" in str(e) or "devin.ai" in str(e):
                wait_time = 15 * (attempt + 1)  # 15s, 30s, 45s
                print(f"⚠️  Devin API rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                if attempt == 2:  # Last attempt
                    raise Exception(f"Devin API rate limited after 3 attempts: {str(e)}")
            else:
                raise
        

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
        issues_data = safe_devin_api_call(agent.fetch_and_cache_issues, request.repo_url)
        
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
        print(f"✅ Fetched {len(issues)} issues")
        return {"issues": issues}
            
    except Exception as e:
        print(f"❌ Error fetching issues: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch issues: {str(e)}")

def process_issue(repo_url: str, issue_id: str, is_execution: bool = False):
    """Process a single issue (analysis or execution)."""
    try:
        print(f"🎯 Processing issue #{issue_id} ({'execution' if is_execution else 'analysis'})")
        
        # Load issue
        issue_file_path = get_issue_file_path("cache", repo_url, issue_id)
        if not os.path.exists(issue_file_path):
            return {"issue_id": issue_id, "error": "Issue not found"}
        
        with open(issue_file_path, 'r') as f:
            issue = json.load(f)
        
        if is_execution:
            # Execution flow - both agents use Devin API
            agent3 = PlanAgent()
            plan = safe_devin_api_call(agent3.review_files_and_plan, issue, repo_url)
            
            if not plan:
                return {"issue_id": issue_id, "error": "No plan available"}
            
            agent4 = ExecutorAgent()
            result = safe_devin_api_call(agent4.execute_and_push, plan, repo_url)
            
            return {
                "issue_id": issue_id,
                "status": "completed",
                "result": result,
                "pr_url": result.get("pr_url") if result else None
            }
        else:
            # Analysis flow - both agents use Devin API
            from utils.utils import get_cache_file_path, check_cache
            
            feasibility_cache = get_cache_file_path("cache", repo_url, "feasibility", issue_id)
            plan_cache = get_cache_file_path("cache", repo_url, "plan", issue_id)
            
            analysis = None
            plan = None
            
            # Run feasibility analysis and plan generation in parallel
            def run_feasibility():
                if check_cache(feasibility_cache):
                    print(f"✅ Using cached feasibility for issue #{issue_id}")
                    with open(feasibility_cache, 'r') as f:
                        return json.load(f)
                else:
                    print(f"🔄 Running Agent 2 (feasibility) for issue #{issue_id}")
                    agent2 = FeasibilityAnalyzerAgent()
                    return safe_devin_api_call(agent2.analyze_issue_feasibility, issue, repo_url)
            
            def run_plan():
                if check_cache(plan_cache):
                    print(f"✅ Using cached plan for issue #{issue_id}")
                    with open(plan_cache, 'r') as f:
                        return json.load(f)
                else:
                    print(f"🔄 Running Agent 3 (planning) for issue #{issue_id}")
                    agent3 = PlanAgent()
                    return safe_devin_api_call(agent3.review_files_and_plan, issue, repo_url)
            
            # Execute both in parallel
            with ThreadPoolExecutor(max_workers=2) as executor:
                feasibility_future = executor.submit(run_feasibility)
                plan_future = executor.submit(run_plan)
                
                analysis = feasibility_future.result()
                plan = plan_future.result()
            
            return {
                "issue_id": issue_id,
                "status": "completed",
                "analysis": analysis,
                "plan": plan
            }
            
    except Exception as e:
        print(f"❌ Processing failed for issue #{issue_id}: {str(e)}")
        return {"issue_id": issue_id, "error": str(e)}

@router.post("/api/analyze-issue")
async def analyze_issue(request: IssueRequest):
    """Analyze a specific issue."""
    result = process_issue(request.repo_url, request.issue_id, is_execution=False)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/api/analyze-multiple-issues")
async def analyze_multiple_issues(request: MultiIssueRequest):
    """Analyze multiple issues with parallelization."""
    print(f"🔍 Analyzing {len(request.issue_ids)} issues")
    
    # Use more workers for better parallelization
    with ThreadPoolExecutor(max_workers=min(5, len(request.issue_ids))) as executor:
        results = list(executor.map(lambda issue_id: process_issue(request.repo_url, issue_id, is_execution=False), request.issue_ids))
    
    print(f"✅ Completed analysis of {len(results)} issues")
    return {"results": results}

@router.post("/api/execute")
async def execute_changes(request: IssueRequest):
    """Execute the plan and push changes."""
    result = process_issue(request.repo_url, request.issue_id, is_execution=True)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/api/execute-multiple-issues")
async def execute_multiple_issues(request: MultiIssueRequest):
    """Execute multiple issues with parallelization."""
    print(f"🚀 Executing {len(request.issue_ids)} issues")
    
    # Use more workers for better parallelization
    with ThreadPoolExecutor(max_workers=min(3, len(request.issue_ids))) as executor:
        results = list(executor.map(lambda issue_id: process_issue(request.repo_url, issue_id, is_execution=True), request.issue_ids))
    
    print(f"✅ Completed execution of {len(results)} issues")
    return {"results": results}