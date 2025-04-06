import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import ServiceRegistration, ServiceStatusUpdate, ServiceType
from .services.registry import RegistryService

app = FastAPI(title="MCP Registry Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the registry service
registry_service = RegistryService()


@app.get("/")
async def root():
    return {"message": "MCP Registry Service"}


@app.get("/registry/health")
async def health_check():
    """Health check endpoint for the registry service."""
    return {
        "status": "healthy",
        "service": "registry-service",
        "services_count": len(registry_service.services)
    }


@app.post("/registry/services", status_code=201)
async def register_service(service: ServiceRegistration):
    """Register a new service with the registry."""
    registered_service = registry_service.register_service(service)
    return registered_service


@app.delete("/registry/services/{service_id}")
async def deregister_service(service_id: str):
    """Remove a service from the registry."""
    success = registry_service.deregister_service(service_id)
    if not success:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"message": "Service deregistered successfully"}


@app.get("/registry/services/{service_id}")
async def get_service(service_id: str):
    """Get a service by ID."""
    service = registry_service.get_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@app.get("/registry/services")
async def get_all_services(type: str = None):
    """Get all registered services, optionally filtered by type."""
    if type:
        try:
            service_type = ServiceType(type)
            return registry_service.get_services_by_type(service_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid service type: {type}")
    return registry_service.get_all_services()


@app.put("/registry/services/{service_id}/status")
async def update_service_status(service_id: str, status_update: ServiceStatusUpdate):
    """Update the status of a service."""
    updated_service = registry_service.update_service_status(service_id, status_update.status)
    if not updated_service:
        raise HTTPException(status_code=404, detail="Service not found")
    return updated_service


@app.post("/registry/services/{service_id}/heartbeat")
async def service_heartbeat(service_id: str):
    """Update the last_seen timestamp for a service."""
    service = registry_service.heartbeat(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"message": "Heartbeat received"}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("SERVICE_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
