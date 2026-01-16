"""
Structured logging utility for the orchestrator system.
Logs execution plans, agent calls, SQL queries, and outputs.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


class StructuredLogger:
    """Structured logger for orchestrator execution."""
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize structured logger.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"orchestrator_{timestamp}.log"
        self.json_log_file = self.log_dir / f"orchestrator_{timestamp}.jsonl"
        
        # Setup Python logger
        self.logger = logging.getLogger("Orchestrator")
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_query(self, query: str):
        """Log user query."""
        self.logger.info(f"User Query: {query}")
        self._write_json({"type": "user_query", "query": query, "timestamp": datetime.now().isoformat()})
    
    def log_parsed_query(self, parsed: Dict[str, Any]):
        """Log parsed query."""
        self.logger.info(f"Parsed Query - Agents: {parsed.get('agents', [])}, Intent: {parsed.get('intent', 'N/A')}")
        self._write_json({"type": "parsed_query", "data": parsed, "timestamp": datetime.now().isoformat()})
    
    def log_missing_info(self, missing_info: Dict[str, Any]):
        """Log missing information detection."""
        if not missing_info.get("can_proceed", True):
            questions = missing_info.get("questions", [])
            self.logger.info(f"Missing Info Detected - Required: {missing_info.get('required_fields', [])}")
            for q in questions:
                self.logger.info(f"  Question: {q.get('question', 'N/A')}")
        self._write_json({"type": "missing_info", "data": missing_info, "timestamp": datetime.now().isoformat()})
    
    def log_execution_plan(self, plan: List[Dict[str, Any]]):
        """Log execution plan."""
        self.logger.info(f"Execution Plan - {len(plan)} steps")
        for step in plan:
            self.logger.info(f"  Step {step['step_id']}: {step['agent']} - {step['goal']}")
            if step.get('depends_on'):
                self.logger.info(f"    Depends on: {step['depends_on']}")
        self._write_json({"type": "execution_plan", "plan": plan, "timestamp": datetime.now().isoformat()})
    
    def log_agent_call(self, agent_name: str, goal: str, filters: Optional[Dict[str, Any]], 
                      query: str, row_count: int, execution_time_ms: float, error: Optional[str] = None):
        """Log agent call and results."""
        if error:
            self.logger.error(f"[{agent_name}] Error: {error}")
        else:
            self.logger.info(f"[{agent_name}] Goal: {goal}")
            self.logger.info(f"[{agent_name}] SQL: {query}")
            self.logger.info(f"[{agent_name}] Result: {row_count} rows, {execution_time_ms:.2f}ms")
        
        self._write_json({
            "type": "agent_call",
            "agent": agent_name,
            "goal": goal,
            "filters": filters,
            "query": query,
            "row_count": row_count,
            "execution_time_ms": execution_time_ms,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_final_response(self, response: str, total_time_ms: Optional[float] = None):
        """Log final response."""
        self.logger.info(f"Final Response: {response[:200]}...")
        if total_time_ms is not None:
            self.logger.info(f"Total Execution Time: {total_time_ms:.2f}ms")
        else:
            self.logger.info("Total Execution Time: N/A")
        self._write_json({
            "type": "final_response",
            "response": response,
            "total_execution_time_ms": total_time_ms,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_dependency(self, agent: str, requires: str, description: str):
        """Log dependency resolution."""
        self.logger.info(f"Dependency: {agent} requires {requires} - {description}")
        self._write_json({
            "type": "dependency",
            "agent": agent,
            "requires": requires,
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
    
    def _write_json(self, data: Dict[str, Any]):
        """Write JSON log entry."""
        try:
            with open(self.json_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        except Exception as e:
            self.logger.warning(f"Failed to write JSON log: {e}")


# Global logger instance
_logger_instance: Optional[StructuredLogger] = None


def get_logger() -> StructuredLogger:
    """Get or create global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = StructuredLogger()
    return _logger_instance
