"""
PayGuard Agent
Handles queries related to wallets, transactions, and payment methods.
"""

from typing import Dict, Any
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.llm_client import OpenRouterLLM
from .base_agent import BaseAgent


class PayGuardAgent(BaseAgent):
    """Agent for PayGuard database operations."""
    
    def __init__(self, db_path: str = "db/payguard.db"):
        """Initialize PayGuard agent."""
        super().__init__(db_path, "PayGuard")
        # Initialize OpenRouter LLM
        self.llm = OpenRouterLLM(temperature=0.1)
    
    def process_task(self, task: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a task and return structured JSON response.
        
        Args:
            task: Natural language task description
            filters: Optional filters (e.g., {"UserID": 1, "OrderID": 2, "WalletID": 3})
            
        Returns:
            Structured JSON response
        """
        start_time = time.time()
        
        try:
            # Get schema information
            schema = self.get_schema()
            
            # Build prompt for LLM to generate SQL
            prompt = f"""You are a SQL expert for the PayGuard database.

Database Schema:
{schema}

IMPORTANT: Only use columns that exist in the schema above. Do NOT invent column names.

Available tables and their columns:
- Wallets: WalletID, UserID, Balance, Currency
- Transactions: TransactionID, WalletID, OrderID, Amount, Type, Timestamp
- PaymentMethods: MethodID, WalletID, Provider, ExpiryDate

CRITICAL: Transaction Type values are case-sensitive: "Purchase" and "Refund" (capitalized). Use exact case matching.

Task: {task}

{f"Additional filters: {filters}" if filters else ""}

Generate a SQL SELECT query to answer this task. Only return the SQL query, nothing else.
- Use ONLY columns that exist in the schema
- For Transaction Type: Use "Refund" (capitalized) not "refund"
- Do not use JOINs unless absolutely necessary
- Use simple SELECT statements
- Be specific with WHERE clauses based on the task description
- CRITICAL: Do NOT use parameterized queries (with ? placeholders). Always use direct values in WHERE clauses like: WHERE OrderID = 1, NOT WHERE OrderID = ?

SQL Query:"""
            
            # Get SQL from LLM
            sql_query = self.llm.invoke(prompt).strip()
            
            # Clean up SQL query (remove markdown code blocks if present)
            if sql_query.startswith("```"):
                sql_query = sql_query.split("```")[1]
                if sql_query.startswith("sql"):
                    sql_query = sql_query[3:]
                sql_query = sql_query.strip()
            
            # Remove trailing semicolon if present
            sql_query = sql_query.rstrip().rstrip(';').strip()
            
            # Validate query: reject parameterized queries (with ? placeholders)
            if "?" in sql_query:
                execution_time = (time.time() - start_time) * 1000
                return self.format_error(f"Invalid SQL query: Parameterized queries (with ?) are not supported. Please use direct values in WHERE clauses.")
            
            # Apply filters if provided
            if filters:
                # Check if WHERE clause already exists
                query_upper = sql_query.upper()
                has_where = "WHERE" in query_upper
                
                # Find WHERE position to check existing conditions
                existing_columns = set()
                if has_where:
                    where_pos = query_upper.find("WHERE")
                    where_clause = sql_query[where_pos + 5:].strip()
                    # Extract column names from existing WHERE clause
                    import re
                    pattern = r'(\w+)\s*[=<>!]'
                    matches = re.findall(pattern, where_clause, re.IGNORECASE)
                    existing_columns = {col.upper() for col in matches}
                
                # Build new filter clauses, skipping columns that already exist
                new_where_clauses = []
                for key, value in filters.items():
                    # Skip if this column already has a condition
                    if key.upper() in existing_columns:
                        continue
                    # Handle list values (for multiple OrderIDs) using IN clause
                    if isinstance(value, list) and len(value) > 0:
                        if all(isinstance(v, (int, float)) for v in value):
                            # Numeric list - use IN clause
                            value_str = ",".join(str(v) for v in value)
                            new_where_clauses.append(f"{key} IN ({value_str})")
                        elif all(isinstance(v, str) for v in value):
                            # String list - use IN clause with quotes
                            value_str = ",".join(f"'{v}'" for v in value)
                            new_where_clauses.append(f"{key} IN ({value_str})")
                        else:
                            # Mixed types - use first value as fallback
                            new_where_clauses.append(f"{key} = {value[0]}")
                    elif isinstance(value, str):
                        new_where_clauses.append(f"{key} = '{value}'")
                    else:
                        new_where_clauses.append(f"{key} = {value}")
                
                # Add new filters if any
                if new_where_clauses:
                    if has_where:
                        sql_query += " AND " + " AND ".join(new_where_clauses)
                    else:
                        sql_query += " WHERE " + " AND ".join(new_where_clauses)
            
            # Execute query with error handling and case-insensitive Type fix
            try:
                rows = self.execute_query(sql_query)
            except Exception as e:
                error_msg = str(e)
                # If error is about invalid column, try to provide helpful error
                if "no such column" in error_msg.lower():
                    execution_time = (time.time() - start_time) * 1000
                    return self.format_error(f"Invalid column in query. Available columns: Wallets (WalletID, UserID, Balance, Currency), Transactions (TransactionID, WalletID, OrderID, Amount, Type, Timestamp), PaymentMethods (MethodID, WalletID, Provider, ExpiryDate). Error: {error_msg}")
                else:
                    raise
            
            # If no rows found and query mentions refund, try case-insensitive Type matching
            if not rows and ("refund" in task.lower() or "Type" in sql_query):
                # Try with capitalized "Refund" or "Purchase"
                import re
                if re.search(r"Type\s*=\s*['\"]refund['\"]", sql_query, re.IGNORECASE):
                    try:
                        fixed_query = re.sub(r"Type\s*=\s*['\"]refund['\"]", "Type = 'Refund'", sql_query, flags=re.IGNORECASE)
                        rows = self.execute_query(fixed_query)
                        sql_query = fixed_query  # Update the query for logging
                    except:
                        pass  # If fix doesn't work, use original empty result
            
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return self.format_response(sql_query, rows, execution_time)
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return self.format_error(str(e))
