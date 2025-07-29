"""Simple FastAPI routes for GitHub Issues Agent frontend."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import json
import os
import sys
import time

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent1_issue_fetcher import IssueFetcherAgent
from agents.agent2_feasibility_analyzer import FeasibilityAnalyzerAgent
from agents.agent3_plan import PlanAgent
from agents.agent4_executor import ExecutorAgent
from utils.utils import get_issue_file_path

router = APIRouter()

# Simple request models
class RepoRequest(BaseModel):
    repo_url: str

class IssueRequest(BaseModel):
    repo_url: str
    issue_id: str

@router.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main frontend page."""
    with open("app/static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@router.post("/api/fetch-issues")
async def fetch_issues(request: RepoRequest):
    """Fetch issues from a repository."""
    try:
        # Check if cache exists
        repo_key = request.repo_url.replace("https://github.com/", "").replace("/", "_")
        cache_dir = os.path.join("cache", "issues", repo_key)
        
        if not os.path.exists(cache_dir) or len(os.listdir(cache_dir)) == 0:
            # Fetch issues if needed
            agent1 = IssueFetcherAgent()
            issues = agent1.fetch_and_cache_issues(request.repo_url)
            if not issues:
                raise HTTPException(status_code=400, detail="Failed to fetch issues")
        else:
            print("✅ Using cached issues")
        
        # Load and return issues
        issues = []
        for filename in os.listdir(cache_dir):
            if filename.endswith('.json'):
                issue_id = filename.replace('.json', '').replace('issue_', '')
                file_path = os.path.join(cache_dir, filename)
                with open(file_path, 'r') as f:
                    issue_data = json.load(f)
                    issues.append({
                        "id": issue_id,
                        "title": issue_data.get('title', 'No title'),
                        "state": issue_data.get('state', 'unknown'),
                        "body": issue_data.get('body', ''),
                        "created_at": issue_data.get('created_at', ''),
                        "updated_at": issue_data.get('updated_at', '')
                    })
        
        # Sort by issue number
        issues.sort(key=lambda x: int(x["id"]))
        
        return {"issues": issues}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/analyze-issue")
async def analyze_issue(request: IssueRequest):
    """Analyze a specific issue with agents 2 and 3."""
    try:
        # Load issue
        issue_file_path = get_issue_file_path("cache", request.repo_url, request.issue_id)
        if not os.path.exists(issue_file_path):
            raise HTTPException(status_code=404, detail="Issue not found")
        
        with open(issue_file_path, 'r') as f:
            issue = json.load(f)
        
        # Run analysis directly (no background tasks)
        print(f"Starting analysis for issue #{request.issue_id}")
        
        # Run Agent 2 (Feasibility Analysis)
        agent2 = FeasibilityAnalyzerAgent()
        analysis = agent2.analyze_issue_feasibility(issue, request.repo_url)
        
        # Run Agent 3 (Planning)
        agent3 = PlanAgent()
        plan = agent3.review_files_and_plan(issue, request.repo_url)
        
        return {
            "status": "completed",
            "analysis": analysis,
            "plan": plan
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/execute")
async def execute_changes(request: IssueRequest):
    """Execute the plan and push changes."""
    try:
        # Load issue
        issue_file_path = get_issue_file_path("cache", request.repo_url, request.issue_id)
        if not os.path.exists(issue_file_path):
            raise HTTPException(status_code=404, detail="Issue not found")
        
        with open(issue_file_path, 'r') as f:
            issue = json.load(f)
        
        # Run analysis first to get the plan
        print(f"Getting plan for issue #{request.issue_id}")
        agent3 = PlanAgent()
        plan = agent3.review_files_and_plan(issue, request.repo_url)
        
        if not plan:
            raise HTTPException(status_code=400, detail="No plan available")
        
        # Execute the plan
        print(f"Executing plan for issue #{request.issue_id}")
        agent4 = ExecutorAgent()
        push_result = agent4.execute_and_push(plan, request.repo_url)
        
        return {
            "status": "completed",
            "result": push_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Dependency for Devin session (placeholder)
def get_devin_session():
    """Get the Devin API session."""
    return None 