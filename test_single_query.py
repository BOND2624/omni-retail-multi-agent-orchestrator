"""
Run a single test query (Test 2: Premium user complete history)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.langgraph_orchestrator import LangGraphOrchestrator
from db.init_databases import main as init_databases
import time

# Mock user input callback for testing
def mock_user_input(prompt):
    """Mock user input - extract values from prompt or use defaults."""
    prompt_lower = prompt.lower()
    
    # Extract Email if mentioned
    if "email" in prompt_lower:
        if "alice" in prompt_lower:
            return "alice@example.com"
        elif "premium" in prompt_lower:
            return "alice@example.com"  # Alice is premium
        else:
            return "alice@example.com"
    
    return "alice@example.com"  # Default fallback


def main():
    """Run Test 2 only."""
    print("="*70)
    print("Test 2: Premium user complete history (Email provided)")
    print("="*70)
    
    # Initialize databases
    print("\nInitializing databases...")
    init_databases()
    print("Databases initialized.\n")
    
    # Create orchestrator with mock input
    orchestrator = LangGraphOrchestrator(user_input_callback=mock_user_input)
    
    # Test 2 query
    query = "I'm a premium user with email alice@example.com. Show me my last order, how I paid for it, and if I left a satisfaction rating."
    expected_agents = ["ShopCore", "PayGuard", "CareDesk"]
    
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print(f"{'='*70}\n")
    
    start_time = time.time()
    try:
        result = orchestrator.process_query(query)
        elapsed = (time.time() - start_time) * 1000
        
        # Check results
        success = True
        issues = []
        
        # Check if expected agents were used
        parsed = result.get("parsed_query", {})
        actual_agents = parsed.get("agents", [])
        missing_agents = set(expected_agents) - set(actual_agents)
        if missing_agents:
            success = False
            issues.append(f"Missing agents: {missing_agents}")
        
        # Check for errors
        if result.get("error"):
            success = False
            issues.append(f"Error: {result.get('error')}")
        
        # Check execution results
        exec_results = result.get("execution_results", {})
        agent_results = exec_results.get("results", {})
        
        for agent_name, agent_result in agent_results.items():
            if agent_result.get("error"):
                success = False
                issues.append(f"{agent_name} error: {agent_result.get('error')}")
        
        # Check if response exists
        if not result.get("response"):
            success = False
            issues.append("No response generated")
        
        # Print summary
        status = "[PASS]" if success else "[FAIL]"
        print(f"\n{status} - Execution time: {elapsed:.2f}ms")
        
        if issues:
            print("Issues found:")
            for issue in issues:
                print(f"  - {issue}")
        
        # Print agent results summary
        print("\nAgent Results:")
        for agent_name, agent_result in agent_results.items():
            row_count = agent_result.get("metadata", {}).get("row_count", 0)
            error = agent_result.get("error")
            if not error and row_count > 0:
                status_icon = "[OK]"
            elif not error:
                status_icon = "[WARN]"
            else:
                status_icon = "[ERROR]"
            print(f"  {status_icon} {agent_name}: {row_count} rows" + (f" - {error}" if error else ""))
        
        print("\n" + "="*70)
        print("Full Response:")
        print("="*70)
        print(result.get('response', 'N/A'))
        print("="*70)
        
        return 0 if success else 1
        
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        print(f"\n[FAIL] - Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
