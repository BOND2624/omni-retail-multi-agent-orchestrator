"""
Comprehensive test suite for Omni-Retail Multi-Agent Orchestrator
Tests various query types based on actual seeded data.
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
    
    # Extract OrderID if mentioned
    if "order id" in prompt_lower or "orderid" in prompt_lower:
        if "order 1" in prompt_lower or "orderid 1" in prompt_lower:
            return "1"
        elif "order 3" in prompt_lower or "orderid 3" in prompt_lower:
            return "3"
        elif "order 4" in prompt_lower or "orderid 4" in prompt_lower:
            return "4"
        else:
            return "1"  # Default
    
    # Extract Email if mentioned
    if "email" in prompt_lower:
        if "alice" in prompt_lower:
            return "alice@example.com"
        elif "premium" in prompt_lower:
            return "alice@example.com"  # Alice is premium
        else:
            return "alice@example.com"
    
    return "1"  # Default fallback


def test_query(orchestrator, query, expected_agents=None, description=""):
    """Test a single query and return results."""
    print(f"\n{'='*70}")
    print(f"Test: {description}")
    print(f"Query: {query}")
    print(f"{'='*70}")
    
    start_time = time.time()
    try:
        result = orchestrator.process_query(query)
        elapsed = (time.time() - start_time) * 1000
        
        # Check results
        success = True
        issues = []
        
        # Check if expected agents were used
        if expected_agents:
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
        
        response_preview = result.get('response', 'N/A')
        if response_preview:
            # Remove any problematic Unicode characters for Windows console
            try:
                response_preview = response_preview[:200].encode('ascii', 'ignore').decode('ascii')
            except:
                response_preview = str(response_preview)[:200]
            print(f"\nResponse: {response_preview}...")
        else:
            print(f"\nResponse: N/A")
        
        return {
            "success": success,
            "issues": issues,
            "result": result,
            "elapsed_ms": elapsed
        }
        
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        print(f"\n[FAIL] - Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "issues": [f"Exception: {str(e)}"],
            "result": None,
            "elapsed_ms": elapsed
        }


def main():
    """Run comprehensive test suite."""
    print("="*70)
    print("Comprehensive Query Test Suite")
    print("="*70)
    
    # Initialize databases
    print("\nInitializing databases...")
    init_databases()
    print("Databases initialized.\n")
    
    # Create orchestrator with mock input
    orchestrator = LangGraphOrchestrator(user_input_callback=mock_user_input)
    
    # Test queries based on actual data
    test_cases = [
        {
            "query": "I ordered a Gaming Monitor last week (OrderID 1). Where is my package and do I have any open support tickets?",
            "expected_agents": ["ShopCore", "ShipStream", "CareDesk"],
            "description": "Order tracking with support tickets (OrderID provided)"
        },
        {
            "query": "I'm a premium user with email alice@example.com. Show me my last order, how I paid for it, and if I left a satisfaction rating.",
            "expected_agents": ["ShopCore", "PayGuard", "CareDesk"],
            "description": "Premium user complete history (Email provided)"
        },
        {
            "query": "I returned my Wireless Headphones (OrderID 4). Has my refund been processed and what's the status of the return shipment?",
            "expected_agents": ["ShopCore", "ShipStream", "PayGuard"],
            "description": "Returned order refund and shipment status (OrderID provided)"
        },
        {
            "query": "I ordered a Gaming Monitor last week, but it hasn't arrived.",
            "expected_agents": ["ShopCore", "ShipStream"],
            "description": "Order tracking without OrderID (should ask for it)"
        },
        {
            "query": "Show me all my orders that are currently in transit. I'm user ID 1.",
            "expected_agents": ["ShopCore", "ShipStream"],
            "description": "Multi-order tracking query (UserID provided)"
        },
        {
            "query": "What's the status of my order for the Gaming Monitor?",
            "expected_agents": ["ShopCore"],
            "description": "Simple order status query (should ask for OrderID)"
        },
        {
            "query": "I'm a premium user. Show my last order, where it is, how I paid, and whether I left a satisfaction rating.",
            "expected_agents": ["ShopCore", "ShipStream", "PayGuard", "CareDesk"],
            "description": "Premium user complete query (should ask for email)"
        },
        {
            "query": "Find all transactions for order 1",
            "expected_agents": ["PayGuard"],
            "description": "Simple transaction query"
        },
        {
            "query": "What products are available in the Electronics category?",
            "expected_agents": ["ShopCore"],
            "description": "Product catalog query"
        },
        {
            "query": "Show me all open support tickets for user 1",
            "expected_agents": ["CareDesk"],
            "description": "Support tickets query"
        }
    ]
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'#'*70}")
        print(f"TEST {i}/{len(test_cases)}")
        print(f"{'#'*70}")
        
        result = test_query(
            orchestrator,
            test_case["query"],
            test_case.get("expected_agents"),
            test_case["description"]
        )
        results.append({
            "test_num": i,
            "description": test_case["description"],
            "query": test_case["query"],
            **result
        })
        
        # Small delay between tests
        time.sleep(0.5)
    
    # Summary
    print("\n\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed
    
    print(f"\nTotal Tests: {total}")
    print(f"[PASS] Passed: {passed}")
    print(f"[FAIL] Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    if failed > 0:
        print("\nFailed Tests:")
        for r in results:
            if not r["success"]:
                print(f"\n  Test {r['test_num']}: {r['description']}")
                print(f"    Query: {r['query']}")
                print(f"    Issues: {', '.join(r['issues'])}")
    
    # Performance summary
    avg_time = sum(r["elapsed_ms"] for r in results) / total
    max_time = max(r["elapsed_ms"] for r in results)
    min_time = min(r["elapsed_ms"] for r in results)
    
    print(f"\nPerformance:")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  Min: {min_time:.2f}ms")
    print(f"  Max: {max_time:.2f}ms")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
