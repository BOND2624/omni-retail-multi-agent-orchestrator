"""
Base Agent Interface
All sub-agents must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import sqlite3
import json
import time
from pathlib import Path


class BaseAgent(ABC):
    """Base class for all sub-agents."""
    
    def __init__(self, db_path: str, agent_name: str):
        """
        Initialize the agent.
        
        Args:
            db_path: Path to the SQLite database
            agent_name: Name of the agent (e.g., "ShopCore")
        """
        self.db_path = Path(db_path)
        self.agent_name = agent_name
        self.llm = None  # Will be set by subclasses
    
    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """
        Execute a SQL query safely and return results.
        
        Args:
            sql: SQL query string
            
        Returns:
            List of dictionaries representing rows
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql)
            rows = cursor.fetchall()
            # Convert rows to dictionaries
            result = [dict(row) for row in rows]
            conn.close()
            return result
        except sqlite3.Error as e:
            conn.close()
            raise Exception(f"SQL execution error: {str(e)}")
    
    def get_schema(self) -> str:
        """
        Get the database schema as a string with detailed column information.
        
        Returns:
            Schema description
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        schema_info = []
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            # Format: column_name (type, nullable, default, pk)
            col_info = []
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = "NOT NULL" if col[3] else "NULL"
                pk = "PRIMARY KEY" if col[5] else ""
                col_info.append(f"{col_name} ({col_type}, {not_null}{', ' + pk if pk else ''})")
            schema_info.append(f"Table {table_name}:\n  Columns: {', '.join([c.split('(')[0].strip() for c in col_info])}\n  Details: {'; '.join(col_info)}")
        
        conn.close()
        return "\n\n".join(schema_info)
    
    @abstractmethod
    def process_task(self, task: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a task and return structured JSON response.
        
        Args:
            task: Natural language task description
            filters: Optional filters to apply
            
        Returns:
            Structured JSON response with query_executed, rows, and metadata
        """
        pass
    
    def format_response(self, query: str, rows: List[Dict[str, Any]], 
                       execution_time_ms: float) -> Dict[str, Any]:
        """
        Format the response according to the contract.
        
        Args:
            query: SQL query that was executed
            rows: Query results
            execution_time_ms: Execution time in milliseconds
            
        Returns:
            Formatted response dictionary
        """
        return {
            "agent": self.agent_name,
            "query_executed": query,
            "rows": rows,
            "metadata": {
                "row_count": len(rows),
                "execution_time_ms": round(execution_time_ms, 2)
            }
        }
    
    def format_error(self, error_message: str) -> Dict[str, Any]:
        """
        Format an error response.
        
        Args:
            error_message: Error message
            
        Returns:
            Formatted error response
        """
        return {
            "agent": self.agent_name,
            "error": error_message
        }
