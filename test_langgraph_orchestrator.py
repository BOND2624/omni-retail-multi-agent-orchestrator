"""
Test script for LangGraph Orchestrator
Validates LangGraph-based orchestration with state management.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.langgraph_orchestrator import LangGraphOrchestrator


def test_langgraph_orchestrator():
    """Test LangGraph orchestrator."""
    print("Testing LangGraph Orchestrator")
    print("=" * 50)
    
    orchestrator = LangGraphOrchestrator()
    
    # Test query
    query = "I ordered a Gaming Monitor last week, but it hasn't arrived"
    print(f"\nQuery: {query}")
    print("\n[Note: This should ask for OrderID]")
    
    # Mock input function
    test_inputs = ["1"]  # OrderID = 1
    input_index = [0]
    
    def mock_input(prompt):
        if input_index[0] < len(test_inputs):
            value = test_inputs[input_index[0]]
            input_index[0] += 1
            print(f"{prompt}{value}")
            return value
        return ""
    
    orchestrator.user_input_callback = mock_input
    
    print("\nProcessing with LangGraph...")
    result = orchestrator.process_query(query)
    
    print(f"\nParsed Query:")
    print(f"  Agents: {result['parsed_query'].get('agents', [])}")
    print(f"  Intent: {result['parsed_query'].get('intent', 'N/A')}")
    print(f"  Entities: {result['parsed_query'].get('entities', {})}")
    
    print(f"\nExecution Plan:")
    for step in result['execution_plan']:
        print(f"  Step {step['step_id']}: {step['agent']} - {step['goal']}")
        if step.get('filters'):
            print(f"    Filters: {step['filters']}")
    
    print(f"\nExecution Results:")
    for log_entry in result['execution_results']['execution_log']:
        print(f"  {log_entry['agent']}: {log_entry['row_count']} rows, {log_entry['execution_time_ms']:.2f}ms")
        if log_entry.get('error'):
            print(f"    ERROR: {log_entry['error']}")
    
    print(f"\nFinal Response:")
    print(f"  {result['response'][:300]}...")
    
    print(f"\nTotal Time: {result['total_execution_time_ms']:.2f}ms")
    
    print("\n" + "=" * 50)
    print("[OK] LangGraph Orchestrator test completed!")
    return 0


if __name__ == "__main__":
    sys.exit(test_langgraph_orchestrator())
