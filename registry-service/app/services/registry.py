import uuid
from datetime import datetime
from typing import Dict, List, Optional

from ..models import RegisteredService, ServiceRegistration, ServiceStatus


class RegistryService:
    def __init__(self):
        self.services: Dict[str, RegisteredService] = {}

    def register_service(self, service: ServiceRegistration) -> RegisteredService:
        """Register a new service with the registry."""
        service_id = str(uuid.uuid4())
        registered_service = RegisteredService(
            id=service_id,
            name=service.name,
            url=service.url,
            type=service.type,
            capabilities=service.capabilities,
            status=ServiceStatus.ONLINE,
            last_seen=datetime.now()
        )
        self.services[service_id] = registered_service
        return registered_service

    def deregister_service(self, service_id: str) -> bool:
        """Remove a service from the registry."""
        if service_id in self.services:
            del self.services[service_id]
            return True
        return False

    def get_service(self, service_id: str) -> Optional[RegisteredService]:
        """Get a service by ID."""
        return self.services.get(service_id)

    def get_all_services(self) -> List[RegisteredService]:
        """Get all registered services."""
        return list(self.services.values())

    def get_services_by_type(self, service_type: str) -> List[RegisteredService]:
        """Get all services of a specific type."""
        return [
            service for service in self.services.values()
            if service.type == service_type
        ]

    def update_service_status(self, service_id: str, status: ServiceStatus) -> Optional[RegisteredService]:
        """Update the status of a service."""
        if service_id in self.services:
            self.services[service_id].status = status
            self.services[service_id].last_seen = datetime.now()
            return self.services[service_id]
        return None

    def heartbeat(self, service_id: str) -> Optional[RegisteredService]:
        """Update the last_seen timestamp for a service."""
        if service_id in self.services:
            self.services[service_id].last_seen = datetime.now()
            return self.services[service_id]
        return None
