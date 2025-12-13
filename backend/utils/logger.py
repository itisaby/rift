"""
Rift Logging Utility
Provides structured logging with traceability
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

import structlog
from pythonjsonlogger import jsonlogger


class TraceIDProcessor:
    """Adds trace_id to log context"""

    def __call__(self, logger, method_name, event_dict):
        if "trace_id" not in event_dict:
            event_dict["trace_id"] = str(uuid4())
        return event_dict


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    Configure structured logging for Rift

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
    """

    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # JSON formatter for file handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s %(trace_id)s"
        )
        file_handler.setFormatter(formatter)
        logging.root.addHandler(file_handler)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            TraceIDProcessor(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """
    Get a structured logger instance

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class IncidentLogger:
    """Specialized logger for incident workflows"""

    def __init__(self, incident_id: str):
        self.incident_id = incident_id
        self.trace_id = str(uuid4())
        self.logger = get_logger("rift.incident")

    def log_detection(self, incident_data: dict):
        """Log incident detection"""
        self.logger.info(
            "incident_detected",
            trace_id=self.trace_id,
            incident_id=self.incident_id,
            event_type="detection",
            **incident_data
        )

    def log_diagnosis(self, diagnosis_data: dict):
        """Log diagnosis phase"""
        self.logger.info(
            "diagnosis_completed",
            trace_id=self.trace_id,
            incident_id=self.incident_id,
            event_type="diagnosis",
            **diagnosis_data
        )

    def log_remediation_start(self, plan_data: dict):
        """Log remediation start"""
        self.logger.info(
            "remediation_started",
            trace_id=self.trace_id,
            incident_id=self.incident_id,
            event_type="remediation_start",
            **plan_data
        )

    def log_remediation_complete(self, result_data: dict):
        """Log remediation completion"""
        self.logger.info(
            "remediation_completed",
            trace_id=self.trace_id,
            incident_id=self.incident_id,
            event_type="remediation_complete",
            **result_data
        )

    def log_error(self, error_message: str, error_data: Optional[dict] = None):
        """Log error"""
        self.logger.error(
            error_message,
            trace_id=self.trace_id,
            incident_id=self.incident_id,
            event_type="error",
            **(error_data or {})
        )

    def get_trace_id(self) -> str:
        """Get current trace ID"""
        return self.trace_id
