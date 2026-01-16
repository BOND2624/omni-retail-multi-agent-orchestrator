"""
Orchestrator Agent
Coordinates sub-agents to answer complex queries requiring cross-domain data.
Intelligently identifies missing information and asks users before proceeding.
"""

from typing import Dict, Any, List, Optional, Callable
import json
import time
import re
from langchain_community.llms import Ollama

from .shopcore_agent import ShopCoreAgent
from .shipstream_agent import ShipStreamAgent
from .payguard_agent import PayGuardAgent
from .caredesk_agent import CareDeskAgent


class Orchestrator:
    """Main orchestrator that coordinates sub-agents."""
    
    def __init__(self, user_input_callback: Optional[Callable[[str], str]] = None):
        """
        Initialize orchestrator and sub-agents.
        
        Args:
            user_input_callback: Optional callback function to get user input.
                                If None, uses input() by default.
        """
        self.llm = Ollama(model="llama3:8b", temperature=0.1)
        self.agents = {
            "ShopCore": ShopCoreAgent(),
            "ShipStream": ShipStreamAgent(),
            "PayGuard": PayGuardAgent(),
            "CareDesk": CareDeskAgent()
        }
        self.conversation_history = []
        self.execution_state = {}
        self.user_input_callback = user_input_callback or input
    
    def identify_missing_info(self, query: str, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify what information is missing from the query.
        Prioritizes email for premium queries, and deduplicates OrderID requests.
        
        Args:
            query: User's query
            parsed_query: Parsed query result
            
        Returns:
            Dictionary with missing information requirements
        """
        missing_info = {
            "required_fields": [],
            "questions": [],
            "can_proceed": True
        }
        
        entities = parsed_query.get("entities", {})
        agents = parsed_query.get("agents", [])
        query_lower = query.lower()
        
        # Check for product-related queries
        has_product = entities.get("product_name") or any(word in query_lower for word in 
            ["product", "item", "monitor", "headphone", "keyboard", "mouse", "ordered"])
        
        # Check for premium user queries (PRIORITY - check this first)
        is_premium_query = any(word in query_lower for word in 
            ["premium", "premium user", "premium member", "premium status"])
        
        # Check if OrderID can be extracted from query
        order_id_match = re.search(r'order[_\s]*id[:\s]*(\d+)', query_lower)
        has_order_id_in_query = order_id_match is not None
        
        # Check if email can be extracted from query
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', query)
        has_email_in_query = email_match is not None
        
        # PRIORITY RULE 1: If premium user query but no email/user identifier, ask for email FIRST
        if is_premium_query and not entities.get("email") and not entities.get("user_id") and not has_email_in_query:
            missing_info["required_fields"].append("Email")
            missing_info["questions"].append({
                "field": "Email",
                "question": "To look up your premium account information, could you please provide your email address?",
                "reason": "Premium user queries require email to identify the account",
                "priority": 1  # Highest priority
            })
            missing_info["can_proceed"] = False
        
        # RULE 2: If product-related query OR tracking query OR payment query but no OrderID, ask for OrderID
        # (Combine all OrderID requirements to avoid duplicates)
        needs_order_id = False
        order_id_reason = ""
        
        if has_product and not entities.get("order_id") and not has_order_id_in_query:
            needs_order_id = True
            order_id_reason = "Product queries require OrderID to track shipments and payments"
        
        if "ShipStream" in agents and not entities.get("order_id") and not has_order_id_in_query:
            needs_order_id = True
            if not order_id_reason:
                order_id_reason = "Tracking queries require OrderID"
        
        if "PayGuard" in agents and not entities.get("order_id") and not has_order_id_in_query:
            needs_order_id = True
            if not order_id_reason:
                order_id_reason = "Payment queries require OrderID"
        
        # Only add OrderID question once, and only if not already asked for email (unless it's not a premium query)
        if needs_order_id and "OrderID" not in missing_info["required_fields"]:
            # For premium queries, we might need OrderID after getting email, but let's ask email first
            # For non-premium queries, ask OrderID directly
            if not is_premium_query or "Email" in missing_info["required_fields"]:
                missing_info["required_fields"].append("OrderID")
                missing_info["questions"].append({
                    "field": "OrderID",
                    "question": "To help you with your inquiry, could you please provide your Order ID?",
                    "reason": order_id_reason or "This query requires OrderID",
                    "priority": 2 if is_premium_query else 1
                })
                missing_info["can_proceed"] = False
        
        # Sort questions by priority (lower number = higher priority)
        missing_info["questions"].sort(key=lambda x: x.get("priority", 999))
        
        return missing_info
    
    def ask_user_for_info(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ask user for missing information.
        Handles validation and retries for invalid input (max 3 retries per question).
        
        Args:
            questions: List of questions to ask (already sorted by priority)
            
        Returns:
            Dictionary with collected information
        """
        collected_info = {}
        remaining_questions = questions.copy()
        max_retries = 3
        
        while remaining_questions:
            q = remaining_questions[0]
            field = q["field"]
            question = q["question"]
            retry_count = getattr(q, '_retry_count', 0)
            
            if retry_count >= max_retries:
                print(f"\n[Orchestrator] Skipping {field} after {max_retries} failed attempts.")
                remaining_questions.pop(0)
                continue
            
            print(f"\n[Orchestrator] {question}")
            user_response = self.user_input_callback("> ").strip()
            
            if user_response:
                # Validate and extract the value
                if field == "OrderID":
                    # Extract number from response
                    order_match = re.search(r'(\d+)', user_response)
                    if order_match:
                        collected_info["order_id"] = int(order_match.group(1))
                        remaining_questions.pop(0)  # Remove this question
                    else:
                        q._retry_count = retry_count + 1
                        print(f"[Orchestrator] Could not extract OrderID from your response. Please enter a number. (Attempt {q._retry_count}/{max_retries})")
                        # Don't remove question, will retry
                elif field == "Email":
                    # Extract email from response
                    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_response)
                    if email_match:
                        collected_info["email"] = email_match.group(0)
                        remaining_questions.pop(0)  # Remove this question
                    else:
                        q._retry_count = retry_count + 1
                        print(f"[Orchestrator] Could not extract email from your response. Please enter a valid email address. (Attempt {q._retry_count}/{max_retries})")
                        # Don't remove question, will retry
                else:
                    collected_info[field.lower()] = user_response
                    remaining_questions.pop(0)  # Remove this question
            else:
                q._retry_count = retry_count + 1
                if q._retry_count >= max_retries:
                    print(f"[Orchestrator] No input provided. Skipping {field}.")
                    remaining_questions.pop(0)
                else:
                    print(f"[Orchestrator] No input provided. Please try again. (Attempt {q._retry_count}/{max_retries})")
        
        return collected_info
    
    def parse_query(self, query: str, additional_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parse user query to identify required agents and intent.
        
        Args:
            query: User's natural language query
            additional_info: Additional information collected from user (e.g., OrderID, Email)
            
        Returns:
            Dictionary with identified agents and intent
        """
        # Merge additional info into query context
        context_info = ""
        if additional_info:
            if "order_id" in additional_info:
                context_info += f"OrderID: {additional_info['order_id']}\n"
            if "email" in additional_info:
                context_info += f"Email: {additional_info['email']}\n"
        
        prompt = f"""Analyze this customer query and identify which database agents are needed.

Available agents:
- ShopCore: Users, Products, Orders
- ShipStream: Shipments, Tracking, Warehouses
- PayGuard: Wallets, Transactions, Payment Methods
- CareDesk: Tickets, Messages, Satisfaction Surveys

Query: "{query}"
{context_info}

Extract entities from the query:
- product_name: Product names mentioned (e.g., "Gaming Monitor", "headphones")
- order_id: Order IDs mentioned (numbers)
- user_id: User IDs mentioned
- email: Email addresses mentioned
- premium_status: Whether user mentions being premium

Respond in JSON format:
{{
    "agents": ["ShopCore", "ShipStream"],
    "intent": "Find order status and tracking",
    "entities": {{
        "product_name": "Gaming Monitor",
        "order_id": null,
        "user_id": null,
        "email": null,
        "premium_status": false
    }},
    "dependencies": [
        {{
            "agent": "ShipStream",
            "requires": "ShopCore.OrderID",
            "description": "Need OrderID from ShopCore to query shipments"
        }}
    ]
}}

Only return the JSON, nothing else:"""
        
        response = self.llm.invoke(prompt).strip()
        
        # Clean up response
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
            response = response.strip()
        
        try:
            parsed = json.loads(response)
            
            # Merge additional_info into entities
            if additional_info:
                if "order_id" in additional_info:
                    parsed["entities"]["order_id"] = additional_info["order_id"]
                if "email" in additional_info:
                    parsed["entities"]["email"] = additional_info["email"]
            
            return parsed
        except json.JSONDecodeError:
            # Fallback parsing
            entities = {}
            if additional_info:
                entities.update(additional_info)
            
            return {
                "agents": self._fallback_agent_detection(query),
                "intent": query,
                "entities": entities,
                "dependencies": []
            }
    
    def _fallback_agent_detection(self, query: str) -> List[str]:
        """Fallback method to detect agents from keywords."""
        query_lower = query.lower()
        agents = []
        
        if any(word in query_lower for word in ["order", "product", "user", "premium"]):
            agents.append("ShopCore")
        if any(word in query_lower for word in ["ship", "track", "package", "deliver", "arrival"]):
            agents.append("ShipStream")
        if any(word in query_lower for word in ["pay", "refund", "transaction", "wallet", "payment"]):
            agents.append("PayGuard")
        if any(word in query_lower for word in ["ticket", "support", "satisfaction", "rating", "issue"]):
            agents.append("CareDesk")
        
        return agents if agents else ["ShopCore"]  # Default to ShopCore
    
    def create_execution_plan(self, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create execution plan with dependency resolution.
        
        Args:
            parsed_query: Parsed query from parse_query()
            
        Returns:
            List of execution steps with dependencies resolved
        """
        agents_needed = parsed_query.get("agents", [])
        dependencies = parsed_query.get("dependencies", [])
        entities = parsed_query.get("entities", {})
        
        # Build dependency graph
        execution_steps = []
        completed_agents = set()
        
        # First, execute agents with no dependencies
        for agent_name in agents_needed:
            if agent_name not in [dep["agent"] for dep in dependencies]:
                execution_steps.append({
                    "agent": agent_name,
                    "goal": self._generate_goal(agent_name, parsed_query),
                    "depends_on": None,
                    "step_id": len(execution_steps) + 1,
                    "filters": self._get_filters_for_agent(agent_name, entities)
                })
                completed_agents.add(agent_name)
        
        # Then, execute agents with dependencies
        remaining_deps = dependencies.copy()
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while remaining_deps and iteration < max_iterations:
            iteration += 1
            for dep in remaining_deps[:]:
                required_agent = dep.get("requires", "").split(".")[0] if "." in dep.get("requires", "") else None
                if required_agent in completed_agents or required_agent is None:
                    agent_name = dep["agent"]
                    execution_steps.append({
                        "agent": agent_name,
                        "goal": self._generate_goal(agent_name, parsed_query),
                        "depends_on": dep.get("requires"),
                        "step_id": len(execution_steps) + 1,
                        "filters": self._get_filters_for_agent(agent_name, entities)
                    })
                    completed_agents.add(agent_name)
                    remaining_deps.remove(dep)
        
        # Add any remaining agents
        for agent_name in agents_needed:
            if agent_name not in completed_agents:
                execution_steps.append({
                    "agent": agent_name,
                    "goal": self._generate_goal(agent_name, parsed_query),
                    "depends_on": None,
                    "step_id": len(execution_steps) + 1,
                    "filters": self._get_filters_for_agent(agent_name, entities)
                })
        
        return execution_steps
    
    def _get_filters_for_agent(self, agent_name: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Get initial filters for an agent based on entities."""
        filters = {}
        
        if agent_name == "ShopCore":
            if entities.get("order_id"):
                filters["OrderID"] = entities["order_id"]
            if entities.get("user_id"):
                filters["UserID"] = entities["user_id"]
            if entities.get("email"):
                # Email will be used to find UserID first
                filters["Email"] = entities["email"]
        elif agent_name == "ShipStream":
            if entities.get("order_id"):
                filters["OrderID"] = entities["order_id"]
        elif agent_name == "PayGuard":
            if entities.get("order_id"):
                filters["OrderID"] = entities["order_id"]
            if entities.get("user_id"):
                filters["UserID"] = entities["user_id"]
        elif agent_name == "CareDesk":
            if entities.get("user_id"):
                filters["UserID"] = entities["user_id"]
            if entities.get("order_id"):
                filters["ReferenceID"] = entities["order_id"]
        
        return filters
    
    def _generate_goal(self, agent_name: str, parsed_query: Dict[str, Any]) -> str:
        """Generate a goal description for an agent based on the query."""
        intent = parsed_query.get("intent", "")
        entities = parsed_query.get("entities", {})
        
        # Build goal from intent and entities
        goal_parts = [intent]
        
        if agent_name == "ShopCore":
            if entities.get("product_name"):
                goal_parts.append(f"for product {entities['product_name']}")
            if entities.get("order_id"):
                goal_parts.append(f"for order {entities['order_id']}")
            if entities.get("email"):
                goal_parts.append(f"for email {entities['email']}")
            if entities.get("premium_status"):
                goal_parts.append("with premium status")
        elif agent_name == "ShipStream":
            goal_parts.append("tracking information")
            if entities.get("order_id"):
                goal_parts.append(f"for order {entities['order_id']}")
        elif agent_name == "PayGuard":
            goal_parts.append("payment and transaction information")
            if entities.get("order_id"):
                goal_parts.append(f"for order {entities['order_id']}")
        elif agent_name == "CareDesk":
            goal_parts.append("support ticket information")
            if entities.get("order_id"):
                goal_parts.append(f"for order {entities['order_id']}")
        
        return " ".join(goal_parts)
    
    def execute_plan(self, execution_plan: List[Dict[str, Any]], 
                     original_query: str) -> Dict[str, Any]:
        """
        Execute the plan by calling agents sequentially.
        
        Args:
            execution_plan: List of execution steps
            original_query: Original user query
            
        Returns:
            Aggregated results from all agents
        """
        results = {}
        execution_log = []
        
        for step in execution_plan:
            agent_name = step["agent"]
            goal = step["goal"]
            depends_on = step.get("depends_on")
            initial_filters = step.get("filters", {})
            
            # Extract filters from previous results if dependency exists
            filters = initial_filters.copy()
            
            # Special handling: If ShopCore needs email, first find UserID from email
            if agent_name == "ShopCore" and "Email" in filters and "UserID" not in filters:
                email = filters.pop("Email")
                # First query to get UserID from email
                temp_result = self.agents["ShopCore"].process_task(
                    f"Find user with email {email}",
                    filters=None
                )
                if temp_result.get("rows") and len(temp_result["rows"]) > 0:
                    filters["UserID"] = temp_result["rows"][0].get("UserID")
            
            if depends_on:
                # Parse dependency like "ShopCore.OrderID"
                source_agent, source_field = depends_on.split(".")
                if source_agent in results:
                    source_result = results[source_agent]
                    if "rows" in source_result and source_result["rows"]:
                        # Extract the field value from the first row
                        first_row = source_result["rows"][0]
                        if source_field in first_row:
                            # Map to target agent's filter field
                            if agent_name == "ShipStream" and source_field == "OrderID":
                                filters["OrderID"] = first_row[source_field]
                            elif agent_name == "PayGuard" and source_field == "OrderID":
                                filters["OrderID"] = first_row[source_field]
                            elif agent_name == "CareDesk" and source_field == "UserID":
                                filters["UserID"] = first_row[source_field]
                            elif agent_name == "CareDesk" and source_field == "OrderID":
                                filters["ReferenceID"] = first_row[source_field]
            
            # Call agent
            agent = self.agents[agent_name]
            step_start = time.time()
            agent_result = agent.process_task(goal, filters=filters if filters else None)
            step_time = (time.time() - step_start) * 1000
            
            # Store result
            results[agent_name] = agent_result
            
            # Log execution
            execution_log.append({
                "step": step["step_id"],
                "agent": agent_name,
                "goal": goal,
                "depends_on": depends_on,
                "filters": filters,
                "query": agent_result.get("query_executed", "N/A"),
                "row_count": agent_result.get("metadata", {}).get("row_count", 0),
                "execution_time_ms": step_time,
                "error": agent_result.get("error")
            })
        
        return {
            "results": results,
            "execution_log": execution_log,
            "original_query": original_query
        }
    
    def synthesize_response(self, execution_results: Dict[str, Any]) -> str:
        """
        Synthesize final natural language response from agent results.
        
        Args:
            execution_results: Results from execute_plan()
            
        Returns:
            Natural language response
        """
        results = execution_results["results"]
        query = execution_results["original_query"]
        
        # Build context for LLM
        context_parts = [f"User Query: {query}\n"]
        context_parts.append("\nAgent Results:\n")
        
        for agent_name, result in results.items():
            if "error" in result:
                context_parts.append(f"{agent_name}: Error - {result['error']}\n")
            else:
                rows = result.get("rows", [])
                context_parts.append(f"{agent_name}: Found {len(rows)} result(s)\n")
                if rows:
                    # Include first few rows as examples
                    for i, row in enumerate(rows[:3]):
                        context_parts.append(f"  - {row}\n")
        
        context = "".join(context_parts)
        
        prompt = f"""You are a customer service assistant. Based on the following query and database results, provide a clear, helpful response to the customer.

{context}

Provide a natural, conversational response that directly answers the customer's question. Be specific with details from the results. If there are errors or missing data, mention that politely.

Response:"""
        
        response = self.llm.invoke(prompt).strip()
        return response
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Main method to process a user query end-to-end.
        Intelligently identifies missing information and asks user before proceeding.
        
        Args:
            query: User's natural language query
            
        Returns:
            Complete response with execution details
        """
        start_time = time.time()
        
        # Step 1: Initial parse to understand query
        parsed = self.parse_query(query)
        
        # Step 2: Identify missing information
        missing_info = self.identify_missing_info(query, parsed)
        
        # Step 3: Ask user for missing information if needed
        additional_info = {}
        if not missing_info["can_proceed"]:
            print("\n[Orchestrator] I need some additional information to help you:")
            additional_info = self.ask_user_for_info(missing_info["questions"])
            
            # Re-parse with additional information
            parsed = self.parse_query(query, additional_info)
        
        # Step 4: Create execution plan
        plan = self.create_execution_plan(parsed)
        
        # Step 5: Execute plan
        execution_results = self.execute_plan(plan, query)
        
        # Step 6: Synthesize response
        final_response = self.synthesize_response(execution_results)
        
        total_time = (time.time() - start_time) * 1000
        
        return {
            "query": query,
            "parsed_query": parsed,
            "missing_info_collected": additional_info,
            "execution_plan": plan,
            "execution_results": execution_results,
            "response": final_response,
            "total_execution_time_ms": round(total_time, 2)
        }
