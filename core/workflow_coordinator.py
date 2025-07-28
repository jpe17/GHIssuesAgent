"""Simple workflow coordinator."""

from agents.agent1_issue_fetcher import IssueFetcherAgent
from agents.agent2_feasibility_analyzer import FeasibilityAnalyzerAgent
from agents.agent3_file_reviewer import FileReviewerAgent


class WorkflowCoordinator:
    """Simple workflow coordinator."""
    
    def run_full_workflow(self, repo_url: str, issue_number: int = None) -> dict:
        """Run the simple workflow: Agent 1 -> Agent 2 -> Agent 3."""
        
        # Step 1: Get issues
        print("🔄 Fetching issues...")
        agent1 = IssueFetcherAgent()
        issues = agent1.fetch_and_cache_issues(repo_url)
        if not issues:
            return {"error": "No issues found"}
        
        # Step 2: Select issue (use provided number or first issue)
        if issue_number:
            selected_issue = next((issue for issue in issues if issue.get('number') == issue_number), issues[0])
        else:
            selected_issue = issues[0]
        
        print(f"📋 Selected issue: #{selected_issue.get('number')}: {selected_issue.get('title')}")
        
        # Step 3: Analyze feasibility
        print("🔍 Analyzing feasibility...")
        agent2 = FeasibilityAnalyzerAgent()
        analysis = agent2.analyze_issue_feasibility(selected_issue, repo_url)
        
        print(f"📊 Feasibility: {analysis.get('feasibility_score', 0)}/100")
        
        # Step 4: Review files and plan
        print("📁 Reviewing files...")
        agent3 = FileReviewerAgent()
        review = agent3.review_files_and_plan(analysis, repo_url)
        
        print(f"📝 Plan: {len(review.get('action_plan', []))} steps")
        
        # Step 5: Execute changes
        print("🚀 Executing changes...")
        execution = agent3.execute_changes(review, repo_url)
        
        print(f"✅ Execution complete: {execution.get('status', 'unknown')}")
        
        return {
            "status": "completed",
            "selected_issue": selected_issue,
            "analysis": analysis,
            "review": review,
            "execution": execution
        } 