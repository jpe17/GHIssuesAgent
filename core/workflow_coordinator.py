"""Simple workflow coordinator."""

from agents.agent1_issue_fetcher import IssueFetcherAgent
from agents.agent2_feasibility_analyzer import FeasibilityAnalyzerAgent
from agents.agent3_plan import PlanAgent
from agents.agent4_executor import ExecutorAgent


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
        
        # Step 4: Create implementation plan
        print("📁 Creating implementation plan...")
        agent3 = PlanAgent()
        plan = agent3.review_files_and_plan(selected_issue, repo_url)
        
        print(f"📝 Plan: {len(plan.get('action_plan', []))} steps")
        
        # Step 5: Execute changes
        print("🚀 Implementing changes...")
        agent4 = ExecutorAgent()
        implementation = agent4.execute_and_push(plan, repo_url)
        
        print(f"✅ Implementation complete: {implementation.get('status', 'unknown')}")
        
        return {
            "status": "completed",
            "selected_issue": selected_issue,
            "analysis": analysis,
            "plan": plan,
            "implementation": implementation
        } 