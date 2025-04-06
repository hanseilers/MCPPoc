"""
Logging utility for MCP services.
Provides consistent logging across all services with traceability features.
"""

import logging
import json
import uuid
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional


class MCPLogger:
    """
    Logger class for MCP services with traceability features.
    """
    
    def __init__(self, service_name: str, log_level: str = "INFO"):
        """
        Initialize the logger.
        
        Args:
            service_name: Name of the service using this logger
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.service_name = service_name
        self.log_level = getattr(logging, log_level)
        
        # Create logger
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(self.log_level)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(console_handler)
        
        # Create file handler if LOG_TO_FILE is set
        if os.getenv("LOG_TO_FILE", "false").lower() == "true":
            log_dir = os.getenv("LOG_DIR", "./logs")
            os.makedirs(log_dir, exist_ok=True)
            file_handler = logging.FileHandler(
                f"{log_dir}/{service_name}.log"
            )
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _format_message(self, message: str, trace_id: Optional[str] = None, 
                       extra_data: Optional[Dict[str, Any]] = None) -> str:
        """Format the log message with trace ID and extra data."""
        trace_id = trace_id or str(uuid.uuid4())
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "trace_id": trace_id,
            "message": message
        }
        
        if extra_data:
            log_data["data"] = extra_data
            
        return json.dumps(log_data)
    
    def debug(self, message: str, trace_id: Optional[str] = None, 
             extra_data: Optional[Dict[str, Any]] = None):
        """Log a debug message."""
        formatted_message = self._format_message(message, trace_id, extra_data)
        self.logger.debug(formatted_message)
        return formatted_message
    
    def info(self, message: str, trace_id: Optional[str] = None, 
            extra_data: Optional[Dict[str, Any]] = None):
        """Log an info message."""
        formatted_message = self._format_message(message, trace_id, extra_data)
        self.logger.info(formatted_message)
        return formatted_message
    
    def warning(self, message: str, trace_id: Optional[str] = None, 
               extra_data: Optional[Dict[str, Any]] = None):
        """Log a warning message."""
        formatted_message = self._format_message(message, trace_id, extra_data)
        self.logger.warning(formatted_message)
        return formatted_message
    
    def error(self, message: str, trace_id: Optional[str] = None, 
             extra_data: Optional[Dict[str, Any]] = None):
        """Log an error message."""
        formatted_message = self._format_message(message, trace_id, extra_data)
        self.logger.error(formatted_message)
        return formatted_message
    
    def critical(self, message: str, trace_id: Optional[str] = None, 
                extra_data: Optional[Dict[str, Any]] = None):
        """Log a critical message."""
        formatted_message = self._format_message(message, trace_id, extra_data)
        self.logger.critical(formatted_message)
        return formatted_message


# Create a default logger instance
def get_logger(service_name: str, log_level: str = "INFO") -> MCPLogger:
    """Get a logger instance for the specified service."""
    return MCPLogger(service_name, log_level)
