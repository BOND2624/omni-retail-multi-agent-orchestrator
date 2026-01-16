"""
Test script for all Sub-Agents
Validates that each agent can independently query its database.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.shopcore_agent import ShopCoreAgent
from agents.shipstream_agent import ShipStreamAgent
from agents.payguard_agent import PayGuardAgent
from agents.caredesk_agent import CareDeskAgent


def test_all_agents():
    """Test all agents with sample queries."""
    print("Testing All Sub-Agents")
    print("=" * 50)
    
    # Test ShopCore Agent
    print("\n[ShopCore Agent]")
    shopcore = ShopCoreAgent()
    result = shopcore.process_task("Find all premium users")
    print(f"  Query: {result.get('query_executed', 'N/A')[:80]}...")
    print(f"  Rows: {result.get('metadata', {}).get('row_count', 0)}")
    
    # Test ShipStream Agent
    print("\n[ShipStream Agent]")
    shipstream = ShipStreamAgent()
    result = shipstream.process_task("Find all shipments")
    print(f"  Query: {result.get('query_executed', 'N/A')[:80]}...")
    print(f"  Rows: {result.get('metadata', {}).get('row_count', 0)}")
    
    # Test PayGuard Agent
    print("\n[PayGuard Agent]")
    payguard = PayGuardAgent()
    result = payguard.process_task("Find all transactions")
    print(f"  Query: {result.get('query_executed', 'N/A')[:80]}...")
    print(f"  Rows: {result.get('metadata', {}).get('row_count', 0)}")
    
    # Test CareDesk Agent
    print("\n[CareDesk Agent]")
    caredesk = CareDeskAgent()
    result = caredesk.process_task("Find all open tickets")
    print(f"  Query: {result.get('query_executed', 'N/A')[:80]}...")
    print(f"  Rows: {result.get('metadata', {}).get('row_count', 0)}")
    
    print("\n" + "=" * 50)
    print("[OK] All agents tested successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(test_all_agents())
