"""
Omni-Retail Multi-Agent Orchestrator
Main entry point for the system.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize databases on startup
from db.init_databases import main as init_db

from agents.langgraph_orchestrator import LangGraphOrchestrator


def main():
    """Main entry point."""
    print("Omni-Retail Multi-Agent Orchestrator")
    print("=" * 50)
    
    # Initialize databases
    print("\nInitializing databases...")
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Database initialization error: {e}")
        print("Continuing with existing databases...")
    
    # Initialize orchestrator
    print("\nInitializing orchestrator...")
    orchestrator = LangGraphOrchestrator()
    
    print("\n" + "=" * 50)
    print("System ready! You can now ask questions.")
    print("Type 'exit' or 'quit' to stop.")
    print("=" * 50)
    
    # Interactive loop
    while True:
        try:
            query = input("\n[You] ").strip()
            
            if query.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye!")
                break
            
            if not query:
                continue
            
            print("\n[Orchestrator] Processing your query...")
            result = orchestrator.process_query(query)
            
            print(f"\n[Orchestrator] {result.get('response', 'No response generated')}")
            print(f"\n[System] Execution time: {result.get('total_execution_time_ms', 0):.2f}ms")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n[Error] {str(e)}")
            import traceback
            traceback.print_exc()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
