"""
Middleware for tracing requests across MCP services.
"""

import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Dict, Any, Optional

from .logger import get_logger


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracing requests across services.
    Adds trace_id to request and logs request/response details.
    """
    
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name
        self.logger = get_logger(f"{service_name}-tracing")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate trace_id
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        
        # Add trace_id to request state
        request.state.trace_id = trace_id
        
        # Log request
        start_time = time.time()
        path = request.url.path
        method = request.method
        
        self.logger.info(
            f"Request: {method} {path}",
            trace_id=trace_id,
            extra_data={
                "method": method,
                "path": path,
                "client": request.client.host if request.client else "unknown"
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            status_code = response.status_code
            
            self.logger.info(
                f"Response: {status_code} - Took {process_time:.4f}s",
                trace_id=trace_id,
                extra_data={
                    "status_code": status_code,
                    "process_time": process_time
                }
            )
            
            # Add trace_id to response headers
            response.headers["X-Trace-ID"] = trace_id
            
            return response
        except Exception as e:
            # Log exception
            process_time = time.time() - start_time
            
            self.logger.error(
                f"Exception: {str(e)}",
                trace_id=trace_id,
                extra_data={
                    "exception": str(e),
                    "process_time": process_time
                }
            )
            
            raise
