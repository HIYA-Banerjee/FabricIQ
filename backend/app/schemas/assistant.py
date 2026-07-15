from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AssistantQueryRequest(BaseModel):
    query: str
    tenant_id: Optional[str] = "factory_alpha"

class ToolCallLog(BaseModel):
    tool_name: str
    tool_args: Dict[str, Any]
    tool_output: Any

class AssistantResponse(BaseModel):
    answer: str
    thought_process: str
    tool_calls: List[ToolCallLog]
