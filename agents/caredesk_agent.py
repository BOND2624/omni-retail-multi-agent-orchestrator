"""
CareDesk Agent
Handles queries related to tickets, messages, and satisfaction surveys.
"""

from typing import Dict, Any
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.llm_client import OpenRouterLLM
from .base_agent import BaseAgent


class CareDeskAgent(BaseAgent):
    """Agent for CareDesk database operations."""
    
    def __init__(self, db_path: str = "db/caredesk.db"):
        """Initialize CareDesk agent."""
        super().__init__(db_path, "CareDesk")
        # Initialize OpenRouter LLM
        self.llm = OpenRouterLLM(temperature=0.1)
    
    def process_task(self, task: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a task and return structured JSON response.
        
        Args:
            task: Natural language task description
            filters: Optional filters (e.g., {"UserID": 1, "TicketID": 2, "ReferenceID": 3})
            
        Returns:
            Structured JSON response
        """
        start_time = time.time()
        
        try:
            # Get schema information
            schema = self.get_schema()
            
            # Build prompt for LLM to generate SQL
            prompt = f"""You are a SQL expert for the CareDesk database.

Database Schema:
{schema}

IMPORTANT: Only use columns that exist in the schema above. Do NOT invent column names.

Available tables and their columns:
- Tickets: TicketID, UserID, ReferenceID, IssueType, Status, CreatedDate
- TicketMessages: MessageID, TicketID, Sender, Content, Timestamp
- SatisfactionSurveys: SurveyID, TicketID, Rating, Comments

CRITICAL: Ticket Status values are case-sensitive and capitalized: "Open" and "Closed" (with capital O and C). Always use exact case: 'Open' not 'open', 'Closed' not 'closed'.

Task: {task}

{f"CRITICAL - You MUST use these filters in your WHERE clause: {filters}" if filters else ""}

Generate a SQL SELECT query to answer this task. Only return the SQL query, nothing else.
- Use ONLY columns that exist in the schema
- CRITICAL: If filters include UserID, ALWAYS use it in WHERE clause: WHERE UserID = X (not just ReferenceID)
- CRITICAL: If task asks for "open tickets", "open support tickets", "any open tickets" → use: WHERE Status = 'Open' (capitalized)
- CRITICAL: If task asks for "closed tickets" → use: WHERE Status = 'Closed' (capitalized)
- CRITICAL: When querying for a specific user's tickets (e.g., "my tickets", "do I have tickets"), use UserID filter, not just ReferenceID
- CRITICAL: If both UserID and ReferenceID filters are provided, use BOTH in WHERE clause: WHERE UserID = X AND ReferenceID = Y
- CRITICAL: ReferenceID is an INTEGER column - use ReferenceID = 1 (not ReferenceID = '1')
- Do not use JOINs unless absolutely necessary (but SatisfactionSurveys JOIN is OK for satisfaction ratings)
- Use simple SELECT statements
- Be specific with WHERE clauses based on the task description
- Always apply ALL provided filters (UserID, ReferenceID, Status) in WHERE clause

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
            
            # Fix ReferenceID type: convert string ReferenceID to integer (e.g., ReferenceID = '1' → ReferenceID = 1)
            import re
            # Pattern to match ReferenceID = 'number' or ReferenceID = "number"
            pattern = r"ReferenceID\s*=\s*['\"](\d+)['\"]"
            sql_query = re.sub(pattern, r"ReferenceID = \1", sql_query, flags=re.IGNORECASE)
            
            # Validate query: reject parameterized queries (with ? placeholders)
            if "?" in sql_query:
                execution_time = (time.time() - start_time) * 1000
                return self.format_error(f"Invalid SQL query: Parameterized queries (with ?) are not supported. Please use direct values in WHERE clauses.")
            
            # Check if task asks for "open" tickets and add Status filter if not present
            task_lower = task.lower()
            is_open_tickets_query = any(phrase in task_lower for phrase in ["open tickets", "open support tickets", "any open tickets", "do i have open", "have any open"])
            is_closed_tickets_query = any(phrase in task_lower for phrase in ["closed tickets", "closed support tickets"])
            
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
                    # Handle list values (for multiple ReferenceIDs) using IN clause
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
                        # For ReferenceID, try to convert to int if it's numeric (to match database type)
                        if key == "ReferenceID" and value.isdigit():
                            new_where_clauses.append(f"{key} = {int(value)}")
                        else:
                            new_where_clauses.append(f"{key} = '{value}'")
                    else:
                        new_where_clauses.append(f"{key} = {value}")
                
                # Add Status filter if task asks for open/closed tickets and Status is not already in query
                if is_open_tickets_query and "STATUS" not in existing_columns and "Status" not in filters:
                    new_where_clauses.append("Status = 'Open'")
                elif is_closed_tickets_query and "STATUS" not in existing_columns and "Status" not in filters:
                    new_where_clauses.append("Status = 'Closed'")
                
                # Add new filters if any
                if new_where_clauses:
                    if has_where:
                        sql_query += " AND " + " AND ".join(new_where_clauses)
                    else:
                        sql_query += " WHERE " + " AND ".join(new_where_clauses)
            elif is_open_tickets_query or is_closed_tickets_query:
                # No filters provided, but task asks for open/closed tickets - add Status filter
                import re
                query_upper = sql_query.upper()
                has_where = "WHERE" in query_upper
                status_filter = "Status = 'Open'" if is_open_tickets_query else "Status = 'Closed'"
                if has_where:
                    sql_query += f" AND {status_filter}"
                else:
                    sql_query += f" WHERE {status_filter}"
            
            # Execute query with error handling
            try:
                rows = self.execute_query(sql_query)
            except Exception as e:
                error_msg = str(e)
                # If error is about invalid column, try to provide helpful error
                if "no such column" in error_msg.lower():
                    execution_time = (time.time() - start_time) * 1000
                    return self.format_error(f"Invalid column in query. Available columns: Tickets (TicketID, UserID, ReferenceID, IssueType, Status, CreatedDate), TicketMessages (MessageID, TicketID, Sender, Content, Timestamp), SatisfactionSurveys (SurveyID, TicketID, Rating, Comments). Error: {error_msg}")
                else:
                    raise
            
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return self.format_response(sql_query, rows, execution_time)
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return self.format_error(str(e))
