#!/usr/bin/env python3
"""
Secure logging configuration for AI Regulatory Watch

Implements PII-safe logging with automatic redaction and audit trails.
"""

import logging
import re
from typing import Any, Dict
from datetime import datetime
from pathlib import Path

from .security import PIIProtector

class PIIRedactingFormatter(logging.Formatter):
    """Custom formatter that redacts PII from log messages"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Format the message first
        message = super().format(record)
        
        # Redact PII
        message = PIIProtector.sanitize_log_message(message)
        
        # Additional redaction patterns
        patterns = {
            # Email addresses - replace with redacted version
            r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})': r'[EMAIL_REDACTED]@\2',
            # IP addresses
            r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b': '[IP_REDACTED]',
            # Phone numbers (various formats)
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b': '[PHONE_REDACTED]',
            # Social Security Numbers
            r'\b\d{3}-\d{2}-\d{4}\b': '[SSN_REDACTED]',
            # Credit card numbers
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b': '[CC_REDACTED]',
        }
        
        for pattern, replacement in patterns.items():
            message = re.sub(pattern, replacement, message)
        
        return message

class SecureFileHandler(logging.FileHandler):
    """File handler with secure permissions"""
    
    def __init__(self, filename: str, mode: str = 'a'):
        # Ensure log directory exists
        log_path = Path(filename)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        super().__init__(filename, mode)
        
        # Set secure permissions on log file
        if log_path.exists():
            import os
            os.chmod(log_path, 0o640)  # Owner read/write, group read only

def configure_secure_logging(
    app_name: str = "ai_regulatory_watch",
    log_level: str = "INFO",
    log_dir: str = "logs"
) -> logging.Logger:
    """Configure secure logging for the application"""
    
    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = PIIRedactingFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = PIIRedactingFormatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler (simple format)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler for general logs (detailed format)
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    general_log = log_path / f"{app_name}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = SecureFileHandler(str(general_log))
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Error file handler
    error_log = log_path / f"{app_name}_errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = SecureFileHandler(str(error_log))
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    # Security audit log (separate handler)
    audit_log = log_path / "audit" / f"security_audit_{datetime.now().strftime('%Y%m%d')}.log"
    audit_handler = SecureFileHandler(str(audit_log))
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(detailed_formatter)
    
    # Create separate audit logger
    audit_logger = logging.getLogger(f"{app_name}.security")
    audit_logger.setLevel(logging.INFO)
    audit_logger.addHandler(audit_handler)
    
    return logger

class SecureLogger:
    """Wrapper for secure logging operations"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.pii_protector = PIIProtector()
    
    def info_secure(self, message: str, **kwargs):
        """Log info with automatic PII redaction"""
        # Redact any emails in kwargs
        for key, value in kwargs.items():
            if isinstance(value, str) and '@' in value:
                kwargs[key] = self.pii_protector.redact_email(value)
        
        self.logger.info(message, extra=kwargs)
    
    def log_subscription(self, email: str, action: str):
        """Log subscription action securely"""
        email_hash = self.pii_protector.hash_email(email)
        redacted_email = self.pii_protector.redact_email(email)
        
        self.logger.info(
            f"Subscription action: {action} for user {email_hash} ({redacted_email})"
        )
    
    def log_data_access(self, data_type: str, purpose: str, user_context: str = "system"):
        """Log data access for audit"""
        self.logger.info(
            f"Data access: type={data_type}, purpose={purpose}, context={user_context}"
        )
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security event with sanitized details"""
        # Sanitize details
        safe_details = {}
        for key, value in details.items():
            if isinstance(value, str):
                safe_details[key] = self.pii_protector.sanitize_log_message(value)
            else:
                safe_details[key] = value
        
        self.logger.warning(
            f"Security event: {event_type} - {safe_details}"
        )

# Default logger configuration
def get_secure_logger(name: str) -> SecureLogger:
    """Get a secure logger instance"""
    base_logger = configure_secure_logging()
    child_logger = base_logger.getChild(name)
    return SecureLogger(child_logger)

# Logging best practices configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'secure': {
            '()': PIIRedactingFormatter,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'secure',
            'level': 'INFO'
        },
        'file': {
            '()': SecureFileHandler,
            'filename': 'logs/app.log',
            'formatter': 'secure',
            'level': 'DEBUG'
        },
        'audit': {
            '()': SecureFileHandler,
            'filename': 'logs/audit/audit.log',
            'formatter': 'secure',
            'level': 'INFO'
        }
    },
    'loggers': {
        'ai_regulatory_watch': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'ai_regulatory_watch.security': {
            'handlers': ['audit'],
            'level': 'INFO',
            'propagate': False
        }
    }
}