"""
WebSocket server for Omni-Retail Multi-Agent Orchestrator
Provides real-time UI integration via WebSocket.
"""

import asyncio
import json
import sys
import queue
import threading
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.langgraph_orchestrator import LangGraphOrchestrator
from utils.logger import get_logger

app = FastAPI(title="Omni-Retail Orchestrator API")

# Mount static files (for UI)
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Global orchestrator instance
orchestrator: Optional[LangGraphOrchestrator] = None
logger = get_logger()


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        # Use thread-safe queues for user input
        self.user_input_queues: Dict[int, queue.Queue] = {}
        self.pending_prompts: Dict[int, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        connection_id = id(websocket)
        self.user_input_queues[connection_id] = queue.Queue()
        self.pending_prompts[connection_id] = {}
        print(f"[Server] Client connected. Total connections: {len(self.active_connections)}")
        return connection_id
    
    def disconnect(self, websocket: WebSocket, connection_id: int):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if connection_id in self.user_input_queues:
            del self.user_input_queues[connection_id]
        if connection_id in self.pending_prompts:
            del self.pending_prompts[connection_id]
        print(f"[Server] Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"[Server] Error sending message: {e}")
    
    def wait_for_user_input_sync(self, connection_id: int, prompt: str, field: str, timeout: float = 300.0) -> str:
        """Wait for user input from WebSocket (thread-safe, blocking)."""
        try:
            # Store the prompt info
            self.pending_prompts[connection_id] = {"prompt": prompt, "field": field}
            
            # Wait for input from queue (blocking, thread-safe)
            value = self.user_input_queues[connection_id].get(timeout=timeout)
            
            # Clear pending prompt
            self.pending_prompts[connection_id] = {}
            
            return value
        except queue.Empty:
            raise Exception("User input timeout")


manager = ConnectionManager()


def process_query_in_thread(query: str, connection_id: int, websocket: WebSocket, loop: asyncio.AbstractEventLoop):
    """
    Process a query in a separate thread and send updates via WebSocket.
    """
    try:
        global orchestrator
        if orchestrator is None:
            # Send init message via event loop
            asyncio.run_coroutine_threadsafe(
                manager.send_message({
                    "type": "status",
                    "message": "Initializing orchestrator...",
                    "stage": "init"
                }, websocket),
                loop
            ).result()
            orchestrator = LangGraphOrchestrator()
        
        # Create sync input callback that sends async messages
        def websocket_input_sync(prompt: str) -> str:
            """Sync input callback that sends async WebSocket messages."""
            # Extract field from prompt - be more specific
            prompt_lower = prompt.lower()
            if "order id" in prompt_lower or "orderid" in prompt_lower or "order" in prompt_lower:
                field = "OrderID"
            elif "email" in prompt_lower:
                field = "Email"
            else:
                field = "unknown"
            
            # Send input request via event loop
            asyncio.run_coroutine_threadsafe(
                manager.send_message({
                    "type": "user_input_required",
                    "prompt": prompt,
                    "field": field
                }, websocket),
                loop
            ).result()
            
            # Wait for input (blocking, thread-safe)
            value = manager.wait_for_user_input_sync(connection_id, prompt, field)
            return value
        
        orchestrator.user_input_callback = websocket_input_sync
        
        # Send status
        asyncio.run_coroutine_threadsafe(
            manager.send_message({
                "type": "status",
                "message": "Processing your query...",
                "stage": "parsing"
            }, websocket),
            loop
        ).result()
        
        # Process query
        result = orchestrator.process_query(query)
        
        # Send parsed query
        if result.get("parsed_query"):
            asyncio.run_coroutine_threadsafe(
                manager.send_message({
                    "type": "parsed_query",
                    "data": result["parsed_query"]
                }, websocket),
                loop
            ).result()
        
        # Send execution plan
        if result.get("execution_plan"):
            asyncio.run_coroutine_threadsafe(
                manager.send_message({
                    "type": "execution_plan",
                    "plan": result["execution_plan"]
                }, websocket),
                loop
            ).result()
        
        # Send agent results
        if result.get("execution_results"):
            execution_log = result["execution_results"].get("execution_log", [])
            for log_entry in execution_log:
                asyncio.run_coroutine_threadsafe(
                    manager.send_message({
                        "type": "agent_result",
                        "agent": log_entry["agent"],
                        "row_count": log_entry["row_count"],
                        "execution_time_ms": log_entry["execution_time_ms"],
                        "error": log_entry.get("error")
                    }, websocket),
                    loop
                ).result()
        
        # Send final response
        if result.get("response"):
            asyncio.run_coroutine_threadsafe(
                manager.send_message({
                    "type": "final_response",
                    "response": result["response"],
                    "total_time_ms": result.get("total_execution_time_ms", 0)
                }, websocket),
                loop
            ).result()
        
    except Exception as e:
        logger.logger.error(f"Error processing query: {e}")
        import traceback
        traceback.print_exc()
        asyncio.run_coroutine_threadsafe(
            manager.send_message({
                "type": "error",
                "message": f"Error: {str(e)}"
            }, websocket),
            loop
        ).result()


@app.get("/", response_class=HTMLResponse)
async def get_ui():
    """Serve the main UI page."""
    html_file = static_dir / "index.html"
    if html_file.exists():
        return html_file.read_text(encoding="utf-8")
    else:
        return """
        <html>
            <head><title>Omni-Retail Orchestrator</title></head>
            <body>
                <h1>UI not found. Please create static/index.html</h1>
            </body>
        </html>
        """


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    connection_id = await manager.connect(websocket)
    loop = asyncio.get_event_loop()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "query":
                # Process a new query in background thread
                query = data.get("query", "")
                if query:
                    thread = threading.Thread(
                        target=process_query_in_thread,
                        args=(query, connection_id, websocket, loop)
                    )
                    thread.daemon = True
                    thread.start()
            
            elif message_type == "user_input":
                # User provided input (for missing info)
                value = data.get("value", "")
                if connection_id in manager.user_input_queues:
                    # Put value in queue (thread-safe)
                    manager.user_input_queues[connection_id].put(value)
            
            elif message_type == "ping":
                # Keep-alive ping
                await manager.send_message({"type": "pong"}, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, connection_id)
    except Exception as e:
        logger.logger.error(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()
        manager.disconnect(websocket, connection_id)


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("=" * 70)
    print("Omni-Retail Multi-Agent Orchestrator - WebSocket Server")
    print("=" * 70)
    print("Server starting...")
    print("Access the UI at: http://localhost:8000")
    print("=" * 70)


if __name__ == "__main__":
    # Initialize databases
    from db.init_databases import main as init_db
    print("Initializing databases...")
    try:
        init_db()
    except Exception as e:
        print(f"Warning: {e}")
    
    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
