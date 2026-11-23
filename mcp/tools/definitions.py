"""MCP Tool Definitions exposed through the protocol adapter."""
from typing import List, Dict, Any

AVAILABLE_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "list_nodes",
        "description": "List all active, standby, and edge nodes in the personal AI infrastructure.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filter_status": {"type": "string", "enum": ["online", "all"]}
            }
        },
        "required_scope": "nodes:read"
    },
    {
        "name": "get_node_status",
        "description": "Retrieve hardware, memory, and service status for a specific node (e.g. pi5).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string", "description": "Node identifier (pi5, redmi, box)"}
            },
            "required": ["node_id"]
        },
        "required_scope": "nodes:read"
    },
    {
        "name": "execute_node_task",
        "description": "Submit an execution task to a specific worker node.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string"},
                "command": {"type": "string"}
            },
            "required": ["node_id", "command"]
        },
        "required_scope": "terminal:execute"
    },
    {
        "name": "query_personal_context",
        "description": "Query indexed personal notes, documentation, and infrastructure runbooks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        },
        "required_scope": "context:read"
    }
]
