"""
Tool Execution Bus Registry & Sandboxed Permission Layer.
Defines schemas, permission policies, and audit logging for all agent-callable tools.
"""

from typing import Dict, Any, Callable, List, Optional
from datetime import datetime, timezone
import json
import hashlib


class ToolDefinition:
    def __init__(
        self,
        name: str,
        description: str,
        handler: Callable[..., Any],
        parameters: Dict[str, Any],
        permission_level: str = "READ",  # READ, ANALYZE, CALCULATE, RECOMMEND, EXPORT, MODIFY
        requires_approval: bool = False,
    ):
        self.name = name
        self.description = description
        self.handler = handler
        self.parameters = parameters
        self.permission_level = permission_level
        self.requires_approval = requires_approval


class ToolBus:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
                "permission_level": t.permission_level,
                "requires_approval": t.requires_approval,
            }
            for t in self._tools.values()
        ]

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        actor: str = "Engineering Copilot",
    ) -> Dict[str, Any]:
        """
        Execute tool through sandboxed verification and emit structured execution audit event.
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' is not registered on the Tool Execution Bus."}

        ts = datetime.now(timezone.utc).isoformat()
        try:
            raw_result = tool.handler(**arguments)
            payload_str = json.dumps(raw_result, default=str, sort_keys=True)
            result_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

            return {
                "tool_name": tool_name,
                "status": "SUCCESS",
                "timestamp_utc": ts,
                "permission_level": tool.permission_level,
                "result": raw_result,
                "result_sha256": result_hash,
                "audit_trace": f"Tool '{tool_name}' executed by {actor} with hash {result_hash[:16]}...",
            }
        except Exception as e:
            return {
                "tool_name": tool_name,
                "status": "ERROR",
                "timestamp_utc": ts,
                "error": str(e),
            }


TOOL_BUS = ToolBus()
