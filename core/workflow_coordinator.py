"""Simple workflow coordinator."""

from agents.agent1_issue_fetcher import IssueFetcherAgent
from agents.agent2_feasibility_analyzer import FeasibilityAnalyzerAgent
from agents.agent3_file_reviewer import FileReviewerAgent


class WorkflowCoordinator:
    """Simple workflow coordinator."""
    
    def run_full_workflow(self, repo_url: str, user_input: str = "") -> dict:
        """Run the simple workflow: Agent 1 -> Agent 2 -> User picks -> Agent 3."""
        
        # Step 1: Get issues
        print("Fetching issues...")
        agent1 = IssueFetcherAgent()
        issues = agent1.fetch_and_cache_issues(repo_url)
        if not issues:
            return {"error": "No issues found"}
        
        # Step 2: Analyze all issues
        print("Analyzing feasibility...")
        agent2 = FeasibilityAnalyzerAgent()
        results = agent2.analyze_multiple_issues(issues, repo_url)
        
        # Show top 5 issues
        print("\nTop issues:")
        for i, result in enumerate(results[:5]):
            print(f"{i+1}. #{result.get('issue_number')}: {result.get('issue_title')}")
            print(f"   Score: {result.get('feasibility_score', 0)}/100")
        
        # Step 3: User picks issue
        choice = input("\nPick issue (1-5): ").strip()
        if not choice.isdigit() or int(choice) < 1 or int(choice) > 5:
            return {"error": "Invalid choice"}
        
        selected = results[int(choice) - 1]
        print(f"Selected: #{selected.get('issue_number')}")
        
        # Step 4: Review files and plan
        print("Reviewing files...")
        agent3 = FileReviewerAgent()
        review = agent3.review_files_and_plan(selected, repo_url)
        
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
            "selected_issue": selected,
            "execution": result
        } 