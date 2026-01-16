"""
Test script for Orchestrator
Validates orchestration logic with intelligent query parsing and missing info detection.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.orchestrator import Orchestrator


def test_orchestrator():
    """Test orchestrator with queries that require missing info."""
    print("Testing Orchestrator - Intelligent Query Processing")
    print("=" * 50)
    
    orchestrator = Orchestrator()
    
    # Test 1: Product query without OrderID (should ask for OrderID)
    print("\n" + "=" * 50)
    print("Test 1: Product query without OrderID")
    print("=" * 50)
    query1 = "I ordered a Gaming Monitor last week, but it hasn't arrived"
    print(f"\nQuery: {query1}")
    print("\n[Note: This should ask for OrderID]")
    
    # For testing, provide a mock input function that provides OrderID
    test_inputs = ["1"]  # OrderID = 1
    input_index = [0]
    
    def mock_input(prompt):
        if input_index[0] < len(test_inputs):
            value = test_inputs[input_index[0]]
            input_index[0] += 1
            print(f"{prompt}{value}")
            return value
        # If we run out of inputs, return empty to trigger skip after max retries
        return ""
    
    orchestrator.user_input_callback = mock_input
    
    result1 = orchestrator.process_query(query1)
    
    print(f"\nParsed Query:")
    print(f"  Agents: {result1['parsed_query'].get('agents', [])}")
    print(f"  Intent: {result1['parsed_query'].get('intent', 'N/A')}")
    print(f"  Entities: {result1['parsed_query'].get('entities', {})}")
    
    print(f"\nExecution Plan:")
    for step in result1['execution_plan']:
        print(f"  Step {step['step_id']}: {step['agent']} - {step['goal']}")
        if step.get('filters'):
            print(f"    Filters: {step['filters']}")
    
    print(f"\nExecution Results:")
    for log_entry in result1['execution_results']['execution_log']:
        print(f"  {log_entry['agent']}: {log_entry['row_count']} rows, {log_entry['execution_time_ms']:.2f}ms")
    
    print(f"\nFinal Response:")
    print(f"  {result1['response'][:200]}...")
    
    # Test 2: Premium user query without email (should ask for email)
    print("\n" + "=" * 50)
    print("Test 2: Premium user query without email")
    print("=" * 50)
    query2 = "I'm a premium user. Show my last order"
    print(f"\nQuery: {query2}")
    print("\n[Note: This should ask for Email first, then maybe OrderID]")
    
    # Reset for new test
    test_inputs2 = ["alice@example.com", "1"]  # Email, then OrderID if needed
    input_index[0] = 0
    
    def mock_input2(prompt):
        if input_index[0] < len(test_inputs2):
            value = test_inputs2[input_index[0]]
            input_index[0] += 1
            print(f"{prompt}{value}")
            return value
        # If we run out of inputs, return empty to trigger skip after max retries
        return ""
    
    orchestrator.user_input_callback = mock_input2
    
    result2 = orchestrator.process_query(query2)
    
    print(f"\nParsed Query:")
    print(f"  Agents: {result2['parsed_query'].get('agents', [])}")
    print(f"  Entities: {result2['parsed_query'].get('entities', {})}")
    
    print("\n" + "=" * 50)
    print("[OK] Orchestrator tests completed!")
    return 0


if __name__ == "__main__":
    sys.exit(test_orchestrator())
