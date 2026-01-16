"""
Test script for ShopCore Agent
Validates that the agent can independently query its database.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.shopcore_agent import ShopCoreAgent


def test_shopcore_agent():
    """Test ShopCore agent with various queries."""
    print("Testing ShopCore Agent")
    print("=" * 50)
    
    agent = ShopCoreAgent()
    
    # Test 1: Simple query
    print("\nTest 1: Find all premium users")
    result = agent.process_task("Find all users with premium status")
    print(f"Query: {result.get('query_executed', 'N/A')}")
    print(f"Rows returned: {result.get('metadata', {}).get('row_count', 0)}")
    if result.get('rows'):
        print(f"Sample result: {result['rows'][0] if result['rows'] else 'None'}")
    
    # Test 2: Query with filters
    print("\nTest 2: Find orders for UserID 1")
    result = agent.process_task("Find all orders", filters={"UserID": 1})
    print(f"Query: {result.get('query_executed', 'N/A')}")
    print(f"Rows returned: {result.get('metadata', {}).get('row_count', 0)}")
    
    # Test 3: Product search
    print("\nTest 3: Find Gaming Monitor product")
    result = agent.process_task("Find product named Gaming Monitor")
    print(f"Query: {result.get('query_executed', 'N/A')}")
    print(f"Rows returned: {result.get('metadata', {}).get('row_count', 0)}")
    if result.get('rows'):
        print(f"Result: {result['rows'][0]}")
    
    # Test 4: Order search by product name
    print("\nTest 4: Find orders for Gaming Monitor")
    result = agent.process_task("Find orders for product Gaming Monitor")
    print(f"Query: {result.get('query_executed', 'N/A')}")
    print(f"Rows returned: {result.get('metadata', {}).get('row_count', 0)}")
    if result.get('rows'):
        print(f"Sample result: {result['rows'][0] if result['rows'] else 'None'}")
    
    print("\n" + "=" * 50)
    print("ShopCore Agent tests completed!")
    return 0


if __name__ == "__main__":
    sys.exit(test_shopcore_agent())
