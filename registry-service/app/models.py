from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class ServiceType(str, Enum):
    MCP = "mcp"
    REST = "rest"
    GRAPHQL = "graphql"


class ServiceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


class ServiceRegistration(BaseModel):
    name: str
    url: str
    type: ServiceType
    capabilities: List[str]


class RegisteredService(ServiceRegistration):
    id: str
    status: ServiceStatus = ServiceStatus.ONLINE
    last_seen: datetime


class ServiceStatusUpdate(BaseModel):
    status: ServiceStatus
