"""Simple workflow coordinator."""

from agents.agent1_issue_fetcher import IssueFetcherAgent
from agents.agent2_feasibility_analyzer import FeasibilityAnalyzerAgent
from agents.agent3_file_reviewer import FileReviewerAgent


class WorkflowCoordinator:
    """Simple workflow coordinator."""
    
    def run_full_workflow(self, repo_url: str, user_input: str = "") -> dict:
        """Run the simple workflow: Agent 1 -> Agent 2 -> Agent 3."""
        
        # Step 1: Get issues
        print("Fetching issues...")
        agent1 = IssueFetcherAgent()
        issues = agent1.fetch_and_cache_issues(repo_url)
        if not issues:
            return {"error": "No issues found"}
        
        # Show available issues
        print("\nAvailable issues:")
        for i, issue in enumerate(issues[:10]):  # Show first 10
            print(f"{i+1}. #{issue.get('number')}: {issue.get('title')}")
        
        # Step 2: User picks issue
        choice = input("\nPick issue (1-10): ").strip()
        if not choice.isdigit() or int(choice) < 1 or int(choice) > min(10, len(issues)):
            return {"error": "Invalid choice"}
        
        selected_issue = issues[int(choice) - 1]
        print(f"Selected: #{selected_issue.get('number')}: {selected_issue.get('title')}")
        
        # Step 3: Analyze feasibility
        print("Analyzing feasibility...")
        agent2 = FeasibilityAnalyzerAgent()
        analysis = agent2.analyze_issue_feasibility(selected_issue, repo_url)
        
        # Show analysis
        print(f"\nFeasibility Score: {analysis.get('feasibility_score', 0)}/100")
        print(f"Complexity Score: {analysis.get('complexity_score', 0)}/100")
        print(f"Confidence: {analysis.get('confidence', 0)}/100")
        
        # Step 4: Review files and plan
        print("Reviewing files...")
        agent3 = FileReviewerAgent()
        review = agent3.review_files_and_plan(analysis, repo_url)
        
        # Show plan
        print("\nPlan:")
        for step in review.get("action_plan", []):
            print(f"• {step.get('description', 'No description')}")
        
        # Step 5: Execute?
        proceed = input("\nExecute? (y/n): ").strip().lower()
        if proceed != 'y':
            return {"status": "cancelled"}
        
        # Step 6: Execute
        print("Executing...")
        result = agent3.execute_changes(review, repo_url, user_approval=True)
        
        return {
            "status": "completed",
            "selected_issue": selected_issue,
            "analysis": analysis,
            "execution": result
        } 