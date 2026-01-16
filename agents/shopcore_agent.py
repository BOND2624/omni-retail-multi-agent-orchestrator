"""
ShopCore Agent
Handles queries related to users, products, and orders.
"""

from typing import Dict, Any
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.llm_client import OpenRouterLLM
from .base_agent import BaseAgent


class ShopCoreAgent(BaseAgent):
    """Agent for ShopCore database operations."""
    
    def __init__(self, db_path: str = "db/shopcore.db"):
        """Initialize ShopCore agent."""
        super().__init__(db_path, "ShopCore")
        # Initialize OpenRouter LLM
        self.llm = OpenRouterLLM(temperature=0.1)
    
    def process_task(self, task: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a task and return structured JSON response.
        
        Args:
            task: Natural language task description
            filters: Optional filters (e.g., {"UserID": 1, "ProductID": 2})
            
        Returns:
            Structured JSON response
        """
        start_time = time.time()
        
        try:
            # Get schema information
            schema = self.get_schema()
            
            # Build prompt for LLM to generate SQL
            prompt = f"""You are a SQL expert for the ShopCore database.

Database Schema:
{schema}

CRITICAL RULES - READ CAREFULLY:
1. Orders table columns: OrderID, UserID, ProductID, OrderDate, Status
2. Orders table does NOT have: Tracking, TrackingNumber, or any tracking-related columns
3. If task mentions "tracking" or "track", use the "Status" column from Orders table
4. Only use columns that are explicitly listed in the schema above
5. Do NOT invent or assume column names
6. Order Status values are case-sensitive and capitalized: "Delivered", "In Transit", "Processing", "Returned". Always use exact case matching.
7. IMPORTANT: When task mentions "email" or "Email", use the Email column in the Users table, NOT UserID. Example: "Find user with email alice@example.com" should use "WHERE Email = 'alice@example.com'", NOT "WHERE UserID = 'alice@example.com'"
8. CRITICAL: Products table does NOT have UserID column. If task asks for "last order" or "orders", query the Orders table, NOT Products table.
9. CRITICAL: Do NOT use parameterized queries (with ? placeholders). Always use direct values in WHERE clauses like: WHERE UserID = 1, NOT WHERE UserID = ?

Available tables and their exact columns:
- Users: UserID, Name, Email, PremiumStatus
- Products: ProductID, Name, Category, Price (NO UserID column!)
- Orders: OrderID, UserID, ProductID, OrderDate, Status (NO Tracking column!)

Task: {task}

{f"Additional filters: {filters}" if filters else ""}

Generate a SQL SELECT query to answer this task. Only return the SQL query, nothing else.
- Use ONLY the columns listed above
- For Orders table: Use "Status" column, NEVER "Tracking"
- For "last order" queries: Query Orders table, NOT Products table
- Do not use JOINs unless absolutely necessary
- Use simple SELECT statements
- Be specific with WHERE clauses based on the task description
- IMPORTANT: If task asks to "find user with email X", use: SELECT UserID FROM Users WHERE Email = 'X'
- NEVER use UserID in WHERE clause when searching by email - use Email column instead
- NEVER use parameterized queries (?) - always use direct values

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
            
            # Validate query: ensure UserID is only used in tables that have it
            query_upper = sql_query.upper()
            if "USERID" in query_upper:
                # Check if query references tables that don't have UserID
                if "FROM PRODUCTS" in query_upper and "USERID" in query_upper:
                    # Products table doesn't have UserID - this is an error
                    execution_time = (time.time() - start_time) * 1000
                    return self.format_error(f"Invalid SQL query: Products table does not have UserID column. Use Orders table to find orders by UserID.")
            
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
                    # Extract column names from existing WHERE clause (simple extraction)
                    # Look for patterns like "ColumnName = " or "ColumnName="
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
                    if isinstance(value, str):
                        new_where_clauses.append(f"{key} = '{value}'")
                    else:
                        new_where_clauses.append(f"{key} = {value}")
                
                # Add new filters if any
                if new_where_clauses:
                    if has_where:
                        sql_query += " AND " + " AND ".join(new_where_clauses)
                    else:
                        sql_query += " WHERE " + " AND ".join(new_where_clauses)
            
            # Execute query with error handling and retry
            try:
                rows = self.execute_query(sql_query)
            except Exception as e:
                error_msg = str(e)
                # If error is about invalid column, try to fix common mistakes
                if "no such column" in error_msg.lower():
                    fixed = False
                    # Common fix 1: Replace "Tracking" with "Status" for Orders table
                    if "Tracking" in sql_query and "Orders" in sql_query:
                        sql_query = sql_query.replace("Tracking", "Status").replace("tracking", "Status")
                        fixed = True
                    # Common fix 2: If query uses UserID with email value, replace with Email column
                    elif "UserID" in sql_query and ("email" in task.lower() or "@" in sql_query):
                        import re
                        # Pattern: WHERE UserID = 'email@example.com' or WHERE UserID='email@example.com'
                        pattern = r"WHERE\s+UserID\s*=\s*['\"]([^'\"]+@[^'\"]+)['\"]"
                        if re.search(pattern, sql_query, re.IGNORECASE):
                            sql_query = re.sub(pattern, r"WHERE Email = '\1'", sql_query, flags=re.IGNORECASE)
                            fixed = True
                    # Common fix 3: If UserID is used in Products table query, suggest using Orders table
                    elif "UserID" in error_msg and "Products" in sql_query:
                        # Try to rewrite query to use Orders table instead
                        import re
                        # If query is SELECT * FROM Products WHERE UserID = X, suggest using Orders
                        if re.search(r"FROM\s+Products", sql_query, re.IGNORECASE):
                            execution_time = (time.time() - start_time) * 1000
                            return self.format_error(f"Products table does not have UserID column. For order queries, use Orders table. Error: {error_msg}")
                    
                    if fixed:
                        try:
                            rows = self.execute_query(sql_query)
                        except Exception as fix_e:
                            execution_time = (time.time() - start_time) * 1000
                            return self.format_error(f"SQL error after fix attempt: {error_msg}. Original query: {sql_query}")
                    else:
                        execution_time = (time.time() - start_time) * 1000
                        # Provide more context about the error
                        if "UserID" in error_msg:
                            return self.format_error(f"SQL error: {error_msg}. Note: UserID exists in Users and Orders tables, but NOT in Products table. Query: {sql_query[:200]}")
                        return self.format_error(f"SQL error: {error_msg}. Query: {sql_query[:200]}")
                else:
                    raise
            
            # If no rows found and query mentions status with lowercase, try case-insensitive Status matching
            if not rows and "status" in task.lower() and "Status" in sql_query:
                import re
                # Try with capitalized status values
                status_fixes = [
                    (r"Status\s*=\s*['\"]in transit['\"]", "Status = 'In Transit'"),
                    (r"Status\s*=\s*['\"]delivered['\"]", "Status = 'Delivered'"),
                    (r"Status\s*=\s*['\"]processing['\"]", "Status = 'Processing'"),
                    (r"Status\s*=\s*['\"]returned['\"]", "Status = 'Returned'"),
                ]
                for pattern, replacement in status_fixes:
                    if re.search(pattern, sql_query, re.IGNORECASE):
                        try:
                            fixed_query = re.sub(pattern, replacement, sql_query, flags=re.IGNORECASE)
                            rows = self.execute_query(fixed_query)
                            sql_query = fixed_query
                            break
                        except:
                            pass
            
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return self.format_response(sql_query, rows, execution_time)
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return self.format_error(str(e))
