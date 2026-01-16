"""
LangGraph-based Orchestrator
Converts orchestration logic into LangGraph nodes and edges with state management.
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated
import json
import time
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.llm_client import OpenRouterLLM
from langgraph.graph import StateGraph, END

from .shopcore_agent import ShopCoreAgent
from .shipstream_agent import ShipStreamAgent
from .payguard_agent import PayGuardAgent
from .caredesk_agent import CareDeskAgent

# Import logger
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger


class OrchestratorState(TypedDict):
    """State schema for LangGraph orchestrator."""
    query: str
    parsed_query: Optional[Dict[str, Any]]
    missing_info: Optional[Dict[str, Any]]
    collected_info: Optional[Dict[str, Any]]
    execution_plan: Optional[List[Dict[str, Any]]]
    execution_results: Optional[Dict[str, Any]]
    response: Optional[str]
    user_input_callback: Optional[Any]
    total_execution_time_ms: Optional[float]


class LangGraphOrchestrator:
    """LangGraph-based orchestrator with state management."""
    
    def __init__(self, user_input_callback: Optional[Any] = None):
        """
        Initialize LangGraph orchestrator.
        
        Args:
            user_input_callback: Optional callback function to get user input.
        """
        self.llm = OpenRouterLLM(temperature=0.1)
        self.agents = {
            "ShopCore": ShopCoreAgent(),
            "ShipStream": ShipStreamAgent(),
            "PayGuard": PayGuardAgent(),
            "CareDesk": CareDeskAgent()
        }
        self.user_input_callback = user_input_callback or input
        self.logger = get_logger()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(OrchestratorState)
        
        # Add nodes
        workflow.add_node("parse_query", self._parse_query_node)
        workflow.add_node("identify_missing_info", self._identify_missing_info_node)
        workflow.add_node("collect_user_info", self._collect_user_info_node)
        workflow.add_node("create_execution_plan", self._create_execution_plan_node)
        workflow.add_node("execute_plan", self._execute_plan_node)
        workflow.add_node("synthesize_response", self._synthesize_response_node)
        
        # Set entry point
        workflow.set_entry_point("parse_query")
        
        # Add edges
        workflow.add_edge("parse_query", "identify_missing_info")
        
        # Conditional edge: if missing info, collect it; otherwise, create plan
        workflow.add_conditional_edges(
            "identify_missing_info",
            self._should_collect_info,
            {
                "collect": "collect_user_info",
                "proceed": "create_execution_plan"
            }
        )
        
        # After collecting info, re-parse and create plan
        workflow.add_edge("collect_user_info", "create_execution_plan")
        
        # Execute plan and synthesize response
        workflow.add_edge("create_execution_plan", "execute_plan")
        workflow.add_edge("execute_plan", "synthesize_response")
        workflow.add_edge("synthesize_response", END)
        
        return workflow.compile()
    
    def _parse_query_node(self, state: OrchestratorState) -> OrchestratorState:
        """Parse user query to identify required agents and intent."""
        query = state["query"]
        additional_info = state.get("collected_info", {})
        
        prompt = f"""Analyze this customer query and identify which database agents are needed.

Available agents:
- ShopCore: Users, Products, Orders
- ShipStream: Shipments, Tracking, Warehouses (use for tracking, delivery status, return shipments)
- PayGuard: Wallets, Transactions, Payment Methods (use for payments, refunds, transactions, payment methods)
- CareDesk: Tickets, Messages, Satisfaction Surveys (use for support tickets, customer service)

IMPORTANT: 
- If query mentions "refund", "payment", "transaction", "paid", "charge", "billing" → include PayGuard
- If query mentions "tracking", "shipment", "delivery", "package", "shipping" → include ShipStream
- If query mentions "ticket", "support", "complaint", "satisfaction", "rating" → include CareDesk
- If query mentions "order", "product", "user", "premium" → include ShopCore

Query: "{query}"
{f"Additional info: {additional_info}" if additional_info else ""}

Extract entities from the query:
- product_name: Product names mentioned (e.g., "Gaming Monitor", "headphones")
- order_id: Order IDs mentioned (numbers)
- user_id: User IDs mentioned
- email: Email addresses mentioned
- premium_status: Whether user mentions being premium

Respond in JSON format:
{{
    "agents": ["ShopCore", "ShipStream", "PayGuard"],
    "intent": "Find order status, tracking, and refund information",
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
        }},
        {{
            "agent": "PayGuard",
            "requires": "ShopCore.OrderID",
            "description": "Need OrderID from ShopCore to query refund transactions"
        }}
    ]
}}

Only return the JSON, nothing else:"""
        
        response = self.llm.invoke(prompt)
        if isinstance(response, str):
            response = response.strip()
        else:
            response = str(response).strip()
        
        # Clean up response
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
            response = response.strip()
        
        try:
            parsed = json.loads(response)
            
            # Validate and fix parsed query structure
            if not isinstance(parsed, dict):
                parsed = {"agents": self._fallback_agent_detection(query), "intent": query, "entities": {}, "dependencies": []}
            
            # Ensure required fields exist
            if "agents" not in parsed or not parsed["agents"]:
                parsed["agents"] = self._fallback_agent_detection(query)
            if "intent" not in parsed:
                parsed["intent"] = query
            if "entities" not in parsed:
                parsed["entities"] = {}
            if "dependencies" not in parsed:
                parsed["dependencies"] = []
            
            # Ensure agents list contains valid agent names
            valid_agents = {"ShopCore", "ShipStream", "PayGuard", "CareDesk"}
            parsed["agents"] = [a for a in parsed["agents"] if a in valid_agents]
            if not parsed["agents"]:
                parsed["agents"] = self._fallback_agent_detection(query)
            
            # Merge additional_info into entities
            if additional_info:
                if "order_id" in additional_info:
                    parsed["entities"]["order_id"] = additional_info["order_id"]
                if "email" in additional_info:
                    parsed["entities"]["email"] = additional_info["email"]
            
            state["parsed_query"] = parsed
            self.logger.log_parsed_query(parsed)
        except json.JSONDecodeError as e:
            self.logger.logger.warning(f"Failed to parse LLM response as JSON: {e}")
            # Fallback parsing
            entities = {}
            if additional_info:
                entities.update(additional_info)
            
            state["parsed_query"] = {
                "agents": self._fallback_agent_detection(query),
                "intent": query,
                "entities": entities,
                "dependencies": []
            }
        
        return state
    
    def _identify_missing_info_node(self, state: OrchestratorState) -> OrchestratorState:
        """Identify what information is missing from the query."""
        query = state["query"]
        parsed_query = state.get("parsed_query", {})
        
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
                "priority": 1
            })
            missing_info["can_proceed"] = False
        
        # Check if query is asking for multiple/all items (shouldn't need OrderID)
        is_multi_item_query = any(phrase in query_lower for phrase in [
            "all my", "all orders", "all products", "show me all", "list all", 
            "what products", "available products", "products in", "category"
        ])
        
        # Check if UserID is provided (can find orders by UserID)
        has_user_id = entities.get("user_id") or re.search(r'user[_\s]*id[:\s]*(\d+)', query_lower)
        
        # RULE 2: If product-related query OR tracking query OR payment query but no OrderID, ask for OrderID
        # BUT: Don't ask if it's a multi-item query or if UserID is provided for order queries
        needs_order_id = False
        order_id_reason = ""
        
        # Don't ask for OrderID if:
        # - It's a product catalog query (asking about available products)
        # - It's a multi-item query with UserID provided
        # - Query explicitly asks for "all" items
        should_skip_order_id = is_multi_item_query or (has_user_id and "all" in query_lower)
        
        if not should_skip_order_id:
            if has_product and not entities.get("order_id") and not has_order_id_in_query:
                needs_order_id = True
                order_id_reason = "Product queries require OrderID to track shipments and payments"
            
            if "ShipStream" in agents and not entities.get("order_id") and not has_order_id_in_query:
                # Only need OrderID for ShipStream if not querying by UserID
                if not has_user_id:
                    needs_order_id = True
                    if not order_id_reason:
                        order_id_reason = "Tracking queries require OrderID"
            
            if "PayGuard" in agents and not entities.get("order_id") and not has_order_id_in_query:
                # Only need OrderID for PayGuard if not querying by UserID
                if not has_user_id:
                    needs_order_id = True
                    if not order_id_reason:
                        order_id_reason = "Payment queries require OrderID"
        
        # Only add OrderID question once
        if needs_order_id and "OrderID" not in missing_info["required_fields"]:
            if not is_premium_query or "Email" in missing_info["required_fields"]:
                missing_info["required_fields"].append("OrderID")
                missing_info["questions"].append({
                    "field": "OrderID",
                    "question": "To help you with your inquiry, could you please provide your Order ID?",
                    "reason": order_id_reason or "This query requires OrderID",
                    "priority": 2 if is_premium_query else 1
                })
                missing_info["can_proceed"] = False
        
        # Sort questions by priority
        missing_info["questions"].sort(key=lambda x: x.get("priority", 999))
        
        state["missing_info"] = missing_info
        self.logger.log_missing_info(missing_info)
        return state
    
    def _should_collect_info(self, state: OrchestratorState) -> str:
        """Determine if we need to collect user information."""
        missing_info = state.get("missing_info", {})
        if missing_info.get("can_proceed", True):
            return "proceed"
        return "collect"
    
    def _collect_user_info_node(self, state: OrchestratorState) -> OrchestratorState:
        """Collect missing information from user."""
        questions = state.get("missing_info", {}).get("questions", [])
        collected_info = {}
        max_retries = 3
        
        for q in questions:
            field = q["field"]
            question = q["question"]
            retry_count = 0
            
            while retry_count < max_retries:
                print(f"\n[Orchestrator] {question}")
                # Pass the actual question to the callback, not just a prompt
                user_response = self.user_input_callback(question).strip()
                
                if user_response:
                    if field == "OrderID":
                        order_match = re.search(r'(\d+)', user_response)
                        if order_match:
                            collected_info["order_id"] = int(order_match.group(1))
                            break
                        else:
                            retry_count += 1
                            print(f"[Orchestrator] Could not extract OrderID. Please enter a number. (Attempt {retry_count}/{max_retries})")
                    elif field == "Email":
                        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_response)
                        if email_match:
                            collected_info["email"] = email_match.group(0)
                            break
                        else:
                            retry_count += 1
                            print(f"[Orchestrator] Could not extract email. Please enter a valid email. (Attempt {retry_count}/{max_retries})")
                    else:
                        collected_info[field.lower()] = user_response
                        break
                else:
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"[Orchestrator] Skipping {field} after {max_retries} failed attempts.")
                    else:
                        print(f"[Orchestrator] No input provided. Please try again. (Attempt {retry_count}/{max_retries})")
        
        state["collected_info"] = collected_info
        # Re-parse query with collected info
        return self._parse_query_node(state)
    
    def _create_execution_plan_node(self, state: OrchestratorState) -> OrchestratorState:
        """Create execution plan with dependency resolution."""
        parsed_query = state.get("parsed_query", {})
        agents_needed = parsed_query.get("agents", [])
        dependencies = parsed_query.get("dependencies", [])
        entities = parsed_query.get("entities", {})
        
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
        max_iterations = 10
        iteration = 0
        
        while remaining_deps and iteration < max_iterations:
            iteration += 1
            for dep in remaining_deps[:]:
                requires = dep.get("requires")
                # Handle None or empty requires
                if requires and isinstance(requires, str) and "." in requires:
                    required_agent = requires.split(".")[0]
                else:
                    required_agent = None
                
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
        
        state["execution_plan"] = execution_steps
        self.logger.log_execution_plan(execution_steps)
        return state
    
    def _execute_plan_node(self, state: OrchestratorState) -> OrchestratorState:
        """Execute the plan by calling agents sequentially."""
        execution_plan = state.get("execution_plan", [])
        original_query = state["query"]
        
        results = {}
        execution_log = []
        
        for step in execution_plan:
            agent_name = step["agent"]
            goal = step["goal"]
            depends_on = step.get("depends_on")
            initial_filters = step.get("filters", {})
            
            filters = initial_filters.copy()
            
            # Special handling: If ShopCore needs email, first find UserID from email
            if agent_name == "ShopCore" and "Email" in filters and "UserID" not in filters:
                email = filters.pop("Email")
                try:
                    temp_result = self.agents["ShopCore"].process_task(
                        f"Find user with email {email}",
                        filters=None
                    )
                    if temp_result.get("rows") and len(temp_result["rows"]) > 0:
                        user_id = temp_result["rows"][0].get("UserID")
                        if user_id:
                            filters["UserID"] = user_id
                            self.logger.logger.info(f"Found UserID {user_id} for email {email}")
                        else:
                            self.logger.logger.warning(f"Could not find UserID for email {email} - result had no UserID field")
                            # Put Email back in filters so the main query can handle it
                            filters["Email"] = email
                    elif temp_result.get("error"):
                        self.logger.logger.warning(f"Error finding UserID for email {email}: {temp_result.get('error')}")
                        # Put Email back in filters so the main query can handle it
                        filters["Email"] = email
                    else:
                        self.logger.logger.warning(f"No results found for email {email}")
                        # Put Email back in filters so the main query can handle it
                        filters["Email"] = email
                except Exception as e:
                    self.logger.logger.warning(f"Exception while finding UserID for email {email}: {str(e)}")
                    # Put Email back in filters so the main query can handle it
                    filters["Email"] = email
            
            if depends_on:
                # Handle multiple dependencies with "or"
                if " or " in depends_on:
                    # Try each dependency until one works
                    dependencies = [d.strip() for d in depends_on.split(" or ")]
                    resolved = False
                    for dep in dependencies:
                        if "." in dep:
                            source_agent, source_field = dep.split(".", 1)
                            if source_agent in results:
                                source_result = results[source_agent]
                                if "rows" in source_result and source_result["rows"]:
                                    first_row = source_result["rows"][0]
                                    if source_field in first_row:
                                        if agent_name == "ShipStream" and source_field == "OrderID":
                                            filters["OrderID"] = first_row[source_field]
                                            resolved = True
                                            break
                                        elif agent_name == "PayGuard" and source_field == "OrderID":
                                            filters["OrderID"] = first_row[source_field]
                                            resolved = True
                                            break
                                        elif agent_name == "CareDesk" and source_field == "UserID":
                                            filters["UserID"] = first_row[source_field]
                                            resolved = True
                                            break
                                        elif agent_name == "CareDesk" and source_field == "OrderID":
                                            # Collect all OrderIDs for CareDesk ReferenceID
                                            reference_ids = []
                                            for row in source_result["rows"]:
                                                if source_field in row and row[source_field] is not None:
                                                    reference_ids.append(row[source_field])
                                            if reference_ids:
                                                if len(reference_ids) == 1:
                                                    filters["ReferenceID"] = reference_ids[0]
                                                else:
                                                    filters["ReferenceID"] = reference_ids
                                            resolved = True
                                            break
                # Handle single dependency in Agent.Field format
                elif "." in depends_on:
                    source_agent, source_field = depends_on.split(".", 1)
                    if source_agent in results:
                        source_result = results[source_agent]
                        if "rows" in source_result and source_result["rows"]:
                            # For OrderID dependencies, collect ALL OrderIDs from multiple rows
                            if (agent_name == "ShipStream" or agent_name == "PayGuard") and source_field == "OrderID":
                                # Collect all OrderIDs from all rows
                                order_ids = []
                                for row in source_result["rows"]:
                                    if source_field in row and row[source_field] is not None:
                                        order_ids.append(row[source_field])
                                
                                if order_ids:
                                    # If multiple OrderIDs, store as list for special handling
                                    if len(order_ids) == 1:
                                        filters["OrderID"] = order_ids[0]
                                    else:
                                        # Multiple OrderIDs - store as list
                                        filters["OrderID"] = order_ids
                            else:
                                # For other dependencies, check if we need to collect multiple values
                                if agent_name == "CareDesk" and source_field == "OrderID":
                                    # Collect all OrderIDs for CareDesk ReferenceID
                                    reference_ids = []
                                    for row in source_result["rows"]:
                                        if source_field in row and row[source_field] is not None:
                                            reference_ids.append(row[source_field])
                                    
                                    if reference_ids:
                                        if len(reference_ids) == 1:
                                            filters["ReferenceID"] = reference_ids[0]
                                        else:
                                            # Multiple ReferenceIDs - store as list
                                            filters["ReferenceID"] = reference_ids
                                else:
                                    # For other dependencies, use first row (existing behavior)
                                    first_row = source_result["rows"][0]
                                    if source_field in first_row:
                                        value = first_row[source_field]
                                        if agent_name == "PayGuard" and source_field == "UserID":
                                            filters["UserID"] = value
                                        elif agent_name == "CareDesk" and source_field == "UserID":
                                            filters["UserID"] = value
                        elif "error" in source_result:
                            # If source agent had an error, log it but continue
                            self.logger.logger.warning(f"Source agent {source_agent} had error: {source_result.get('error')}")
                # If depends_on is just a field name (no agent prefix), ignore it
                # as it's not an inter-agent dependency
            
            # Call agent with error handling
            try:
                agent = self.agents.get(agent_name)
                if not agent:
                    agent_result = {
                        "agent": agent_name,
                        "error": f"Agent {agent_name} not found",
                        "rows": [],
                        "metadata": {"row_count": 0, "execution_time_ms": 0}
                    }
                else:
                    step_start = time.time()
                    # Agents now handle multiple OrderIDs using IN clause, so normal processing works
                    agent_result = agent.process_task(goal, filters=filters if filters else None)
                    step_time = (time.time() - step_start) * 1000
                    # Ensure agent_result has required fields
                    if "metadata" not in agent_result:
                        agent_result["metadata"] = {"row_count": 0, "execution_time_ms": step_time}
                    if "rows" not in agent_result:
                        agent_result["rows"] = []
            except Exception as e:
                self.logger.logger.error(f"Error calling agent {agent_name}: {e}", exc_info=True)
                agent_result = {
                    "agent": agent_name,
                    "error": str(e),
                    "rows": [],
                    "metadata": {"row_count": 0, "execution_time_ms": 0}
                }
            
            results[agent_name] = agent_result
            
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
            
            # Log agent call
            self.logger.log_agent_call(
                agent_name=agent_name,
                goal=goal,
                filters=filters,
                query=agent_result.get("query_executed", "N/A"),
                row_count=agent_result.get("metadata", {}).get("row_count", 0),
                execution_time_ms=step_time,
                error=agent_result.get("error")
            )
        
        state["execution_results"] = {
            "results": results,
            "execution_log": execution_log,
            "original_query": original_query
        }
        return state
    
    def _synthesize_response_node(self, state: OrchestratorState) -> OrchestratorState:
        """Synthesize final natural language response."""
        execution_results = state.get("execution_results", {})
        results = execution_results.get("results", {})
        query = execution_results.get("original_query", state.get("query", ""))
        
        if not results:
            state["response"] = "I apologize, but I encountered an issue processing your query. Please try rephrasing your question."
            return state
        
        context_parts = [f"User Query: {query}\n"]
        context_parts.append("\nAgent Results:\n")
        
        for agent_name, result in results.items():
            if not isinstance(result, dict):
                context_parts.append(f"{agent_name}: Invalid result format\n")
                continue
                
            if "error" in result and result["error"]:
                context_parts.append(f"{agent_name}: Error - {result['error']}\n")
            else:
                rows = result.get("rows", [])
                if not isinstance(rows, list):
                    rows = []
                row_count = result.get("metadata", {}).get("row_count", len(rows)) if isinstance(result.get("metadata"), dict) else len(rows)
                if rows:
                    context_parts.append(f"{agent_name}: Found {row_count} result(s)\n")
                    for i, row in enumerate(rows[:5]):  # Limit to first 5 rows
                        if isinstance(row, dict):
                            context_parts.append(f"  Result {i+1}: {row}\n")
                        else:
                            context_parts.append(f"  Result {i+1}: {str(row)}\n")
                else:
                    context_parts.append(f"{agent_name}: No results found\n")
        
        context = "".join(context_parts)
        
        prompt = f"""You are a customer service assistant. Based on the following query and database results, provide a clear, helpful response to the customer.

{context}

Provide a natural, conversational response that directly answers the customer's question. Be specific with details from the results. If there are errors or missing data, mention that politely. Use markdown formatting for emphasis (e.g., **bold** for important information).

Response:"""
        
        try:
            response = self.llm.invoke(prompt)
            if isinstance(response, str):
                response = response.strip()
            else:
                response = str(response).strip()
            
            # Ensure response is not empty
            if not response:
                response = "I found the information, but I'm having trouble formulating a response. Please try rephrasing your question."
        except Exception as e:
            self.logger.logger.error(f"Error generating response: {e}", exc_info=True)
            response = "I apologize, but I encountered an error while generating a response. Please try again or rephrase your question."
        
        state["response"] = response
        
        # Log final response (total_time will be set later in process_query)
        self.logger.log_final_response(response, None)
        
        return state
    
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
        
        return agents if agents else ["ShopCore"]
    
    def _get_filters_for_agent(self, agent_name: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Get initial filters for an agent based on entities."""
        filters = {}
        
        if agent_name == "ShopCore":
            if entities.get("order_id"):
                filters["OrderID"] = entities["order_id"]
            if entities.get("user_id"):
                filters["UserID"] = entities["user_id"]
            if entities.get("email"):
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
        """Generate a goal description for an agent."""
        intent = parsed_query.get("intent", "Process query")
        entities = parsed_query.get("entities", {})
        
        goal_parts = [intent]
        
        if agent_name == "ShopCore":
            if entities.get("product_name"):
                goal_parts.append(f"for product {entities['product_name']}")
            if entities.get("order_id"):
                goal_parts.append(f"for order {entities['order_id']}")
            if entities.get("user_id"):
                goal_parts.append(f"for user {entities['user_id']}")
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
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query using LangGraph workflow.
        
        Args:
            query: User's natural language query
            
        Returns:
            Complete response with execution details
        """
        start_time = time.time()
        
        # Log user query
        self.logger.log_query(query)
        
        # Validate input
        if not query or not isinstance(query, str) or not query.strip():
            return {
                "query": query,
                "response": "Please provide a valid query.",
                "error": "Empty or invalid query",
                "total_execution_time_ms": 0
            }
        
        # Initialize state
        initial_state: OrchestratorState = {
            "query": query.strip(),
            "parsed_query": None,
            "missing_info": None,
            "collected_info": None,
            "execution_plan": None,
            "execution_results": None,
            "response": None,
            "user_input_callback": self.user_input_callback,
            "total_execution_time_ms": None
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        total_time = (time.time() - start_time) * 1000
        final_state["total_execution_time_ms"] = round(total_time, 2)
        
        # Log final response with total time
        if final_state.get("response"):
            self.logger.log_final_response(final_state["response"], total_time)
        
        return {
            "query": query,
            "parsed_query": final_state.get("parsed_query"),
            "missing_info_collected": final_state.get("collected_info"),
            "execution_plan": final_state.get("execution_plan"),
            "execution_results": final_state.get("execution_results"),
            "response": final_state.get("response"),
            "total_execution_time_ms": final_state.get("total_execution_time_ms")
        }
