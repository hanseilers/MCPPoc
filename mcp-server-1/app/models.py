from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid


class MCPMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    target_id: Optional[str] = None
    content: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class GenerateTextRequest(BaseModel):
    prompt: str
    max_tokens: int = 100


class GenerateTextResponse(BaseModel):
    text: str
    confidence: float
    model_used: str


class ServerStatus(BaseModel):
    status: str
    load: float
    uptime: int
    connected_services: List[str] = []
