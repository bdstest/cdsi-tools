#!/usr/bin/env python3
"""
Security utilities for AI Regulatory Watch

Provides encryption, PII protection, and security guardrails
to ensure compliance with privacy regulations and audit requirements.
"""

import hashlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# Configure security logging
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

class PIIProtector:
    """Protects personally identifiable information from exposure"""
    
    @staticmethod
    def redact_email(email: str) -> str:
        """Redact email for logging purposes"""
        if not email or '@' not in email:
            return '[INVALID_EMAIL]'
        
        parts = email.split('@')
        username = parts[0]
        domain = parts[1]
        
        # Keep first and last char of username, redact middle
        if len(username) > 2:
            redacted_user = f"{username[0]}***{username[-1]}"
        else:
            redacted_user = "***"
        
        return f"{redacted_user}@{domain}"
    
    @staticmethod
    def hash_email(email: str) -> str:
        """Create consistent hash of email for tracking without storing PII"""
        return hashlib.sha256(email.encode()).hexdigest()[:16]
    
    @staticmethod
    def sanitize_log_message(message: str) -> str:
        """Remove PII from log messages"""
        # Email pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        message = re.sub(email_pattern, '[EMAIL_REDACTED]', message)
        
        # IP address pattern
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        message = re.sub(ip_pattern, '[IP_REDACTED]', message)
        
        return message
    
    @staticmethod
    def validate_no_pii_in_data(data: Dict[str, Any]) -> bool:
        """Validate that data doesn't contain unexpected PII fields"""
        prohibited_fields = [
            'ssn', 'social_security', 'tax_id', 'driver_license',
            'passport', 'credit_card', 'bank_account', 'password',
            'date_of_birth', 'dob', 'phone_number', 'street_address'
        ]
        
        data_str = json.dumps(data).lower()
        for field in prohibited_fields:
            if field in data_str:
                security_logger.warning(f"Prohibited PII field detected: {field}")
                return False
        
        return True

class SecureDataStorage:
    """Handles encrypted storage of sensitive data"""
    
    def __init__(self, key_path: Optional[str] = None):
        self.key_path = Path(key_path) if key_path else Path("config/.encryption_key")
        self.cipher_suite = self._initialize_encryption()
    
    def _initialize_encryption(self) -> Fernet:
        """Initialize or load encryption key"""
        if self.key_path.exists():
            # Load existing key
            with open(self.key_path, 'rb') as key_file:
                key = key_file.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            
            # Ensure config directory exists
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save key with restricted permissions
            with open(self.key_path, 'wb') as key_file:
                key_file.write(key)
            
            # Set restrictive permissions (owner read only)
            os.chmod(self.key_path, 0o400)
            
            security_logger.info("Generated new encryption key")
        
        return Fernet(key)
    
    def encrypt_data(self, data: Dict[str, Any]) -> bytes:
        """Encrypt dictionary data"""
        json_data = json.dumps(data)
        return self.cipher_suite.encrypt(json_data.encode())
    
    def decrypt_data(self, encrypted_data: bytes) -> Dict[str, Any]:
        """Decrypt data back to dictionary"""
        decrypted = self.cipher_suite.decrypt(encrypted_data)
        return json.loads(decrypted.decode())
    
    def save_encrypted_file(self, data: Dict[str, Any], filepath: Path):
        """Save encrypted data to file with secure permissions"""
        encrypted = self.encrypt_data(data)
        
        # Write encrypted data
        with open(filepath, 'wb') as f:
            f.write(encrypted)
        
        # Set restrictive permissions
        os.chmod(filepath, 0o600)
    
    def load_encrypted_file(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Load and decrypt data from file"""
        if not filepath.exists():
            return None
        
        with open(filepath, 'rb') as f:
            encrypted_data = f.read()
        
        return self.decrypt_data(encrypted_data)

class SecurityAuditLogger:
    """Logs security events for audit compliance"""
    
    def __init__(self, log_dir: str = "data/audit_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set restrictive permissions on audit log directory
        os.chmod(self.log_dir, 0o700)
        
        # Initialize audit logger
        self.audit_logger = logging.getLogger('audit')
        
        # Create secure file handler
        log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m')}.log"
        handler = logging.FileHandler(log_file)
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.audit_logger.addHandler(handler)
        self.audit_logger.setLevel(logging.INFO)
    
    def log_subscription_event(self, email_hash: str, event_type: str, ip_hash: Optional[str] = None):
        """Log subscription events without exposing PII"""
        self.audit_logger.info(
            f"SUBSCRIPTION_EVENT: type={event_type}, "
            f"user_hash={email_hash}, "
            f"ip_hash={ip_hash or 'N/A'}, "
            f"timestamp={datetime.now().isoformat()}"
        )
    
    def log_data_access(self, accessor: str, data_type: str, purpose: str):
        """Log data access for audit trail"""
        self.audit_logger.info(
            f"DATA_ACCESS: accessor={accessor}, "
            f"data_type={data_type}, "
            f"purpose={purpose}, "
            f"timestamp={datetime.now().isoformat()}"
        )
    
    def log_security_event(self, event_type: str, details: str):
        """Log security-related events"""
        sanitized_details = PIIProtector.sanitize_log_message(details)
        self.audit_logger.warning(
            f"SECURITY_EVENT: type={event_type}, "
            f"details={sanitized_details}, "
            f"timestamp={datetime.now().isoformat()}"
        )
    
    def log_data_deletion(self, data_type: str, count: int):
        """Log data deletion for compliance"""
        self.audit_logger.info(
            f"DATA_DELETION: type={data_type}, "
            f"count={count}, "
            f"timestamp={datetime.now().isoformat()}"
        )

class RateLimiter:
    """Implements rate limiting for security"""
    
    def __init__(self, max_requests: int = 10, time_window: int = 3600):
        self.max_requests = max_requests
        self.time_window = time_window  # seconds
        self.requests = {}  # ip_hash -> list of timestamps
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed under rate limit"""
        current_time = datetime.now().timestamp()
        
        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                ts for ts in self.requests[identifier]
                if current_time - ts < self.time_window
            ]
        
        # Check limit
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[identifier].append(current_time)
        return True

class InputSanitizer:
    """Sanitizes user input to prevent injection attacks"""
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize email input"""
        # Remove any HTML/script tags
        email = re.sub(r'<[^>]+>', '', email)
        # Remove any non-email characters
        email = re.sub(r'[^\w\.-@]', '', email)
        return email.lower().strip()
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize general text input"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove potentially dangerous characters
        text = re.sub(r'[<>&"\'`]', '', text)
        return text.strip()
    
    @staticmethod
    def validate_preferences(preferences: Dict[str, Any]) -> Dict[str, bool]:
        """Validate and sanitize preference inputs"""
        allowed_keys = [
            'weekly_digest', 'sector_healthcare', 'sector_finance',
            'geographic_us', 'geographic_eu', 'geographic_global'
        ]
        
        sanitized = {}
        for key in allowed_keys:
            if key in preferences:
                # Ensure boolean value
                sanitized[key] = bool(preferences[key])
            else:
                sanitized[key] = False
        
        return sanitized

# Security configuration
SECURITY_CONFIG = {
    'rate_limit': {
        'subscription': {'max_requests': 5, 'time_window': 3600},  # 5 per hour
        'api': {'max_requests': 100, 'time_window': 3600},  # 100 per hour
    },
    'password_policy': {
        'min_length': 12,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_numbers': True,
        'require_special': True
    },
    'session': {
        'timeout_minutes': 30,
        'secure_cookie': True,
        'httponly': True,
        'samesite': 'strict'
    },
    'encryption': {
        'algorithm': 'AES-256-GCM',
        'key_rotation_days': 90
    }
}

# Initialize security components
pii_protector = PIIProtector()
audit_logger = SecurityAuditLogger()

def get_secure_storage(key_path: Optional[str] = None) -> SecureDataStorage:
    """Factory function for secure storage"""
    return SecureDataStorage(key_path)

def get_rate_limiter(limit_type: str = 'api') -> RateLimiter:
    """Factory function for rate limiters"""
    config = SECURITY_CONFIG['rate_limit'].get(limit_type, {'max_requests': 100, 'time_window': 3600})
    return RateLimiter(config['max_requests'], config['time_window'])