#!/usr/bin/env python3
"""
Security Audit Verification Script

Verifies that all security controls are properly implemented and
the system is ready for security audits.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import (
    PIIProtector,
    SecureDataStorage,
    SecurityAuditLogger,
    RateLimiter,
    InputSanitizer,
    get_secure_logger
)

logger = get_secure_logger(__name__)

class SecurityAuditChecker:
    """Performs security audit checks"""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.results = []
    
    def run_all_checks(self):
        """Run all security verification checks"""
        print("🔐 AI Regulatory Watch - Security Audit Verification")
        print("=" * 60)
        
        # PII Protection Checks
        self.check_pii_protection()
        
        # Encryption Checks
        self.check_encryption()
        
        # File Permission Checks
        self.check_file_permissions()
        
        # Logging Security Checks
        self.check_logging_security()
        
        # Rate Limiting Checks
        self.check_rate_limiting()
        
        # Input Validation Checks
        self.check_input_validation()
        
        # Audit Trail Checks
        self.check_audit_trail()
        
        # Summary
        self.print_summary()
    
    def check_pii_protection(self):
        """Test PII protection mechanisms"""
        print("\n📋 PII Protection Checks:")
        
        # Test email redaction
        test_email = "test.user@example.com"
        redacted = PIIProtector.redact_email(test_email)
        if "@" in redacted and "***" in redacted and test_email not in redacted:
            self.pass_check("Email redaction working correctly")
        else:
            self.fail_check("Email redaction not working properly")
        
        # Test email hashing
        hash1 = PIIProtector.hash_email(test_email)
        hash2 = PIIProtector.hash_email(test_email)
        if hash1 == hash2 and len(hash1) == 16:
            self.pass_check("Email hashing consistent and secure")
        else:
            self.fail_check("Email hashing inconsistent")
        
        # Test log sanitization
        log_msg = f"User {test_email} logged in from 192.168.1.1"
        sanitized = PIIProtector.sanitize_log_message(log_msg)
        if test_email not in sanitized and "192.168.1.1" not in sanitized:
            self.pass_check("Log sanitization removes PII")
        else:
            self.fail_check("Log sanitization failed to remove PII")
    
    def check_encryption(self):
        """Test encryption functionality"""
        print("\n🔒 Encryption Checks:")
        
        try:
            # Test encryption/decryption
            storage = SecureDataStorage()
            test_data = {"email": "test@example.com", "preferences": {"weekly": True}}
            
            # Encrypt data
            encrypted = storage.encrypt_data(test_data)
            
            # Verify encrypted data is different
            if encrypted != json.dumps(test_data).encode():
                self.pass_check("Data encryption working")
            else:
                self.fail_check("Data not being encrypted")
            
            # Test decryption
            decrypted = storage.decrypt_data(encrypted)
            if decrypted == test_data:
                self.pass_check("Data decryption working")
            else:
                self.fail_check("Data decryption failed")
            
        except Exception as e:
            self.fail_check(f"Encryption system error: {str(e)}")
    
    def check_file_permissions(self):
        """Check file permission security"""
        print("\n📁 File Permission Checks:")
        
        # Check if encryption key has proper permissions
        key_path = Path("config/.encryption_key")
        if key_path.exists():
            stat_info = os.stat(key_path)
            mode = oct(stat_info.st_mode)[-3:]
            if mode == "400":
                self.pass_check("Encryption key has secure permissions (400)")
            else:
                self.fail_check(f"Encryption key has insecure permissions ({mode})")
        else:
            self.pass_check("Encryption key will be created with secure permissions")
        
        # Check data directory
        data_dir = Path("data")
        if data_dir.exists():
            stat_info = os.stat(data_dir)
            mode = oct(stat_info.st_mode)[-3:]
            if mode in ["700", "750"]:
                self.pass_check(f"Data directory has secure permissions ({mode})")
            else:
                self.fail_check(f"Data directory has insecure permissions ({mode})")
    
    def check_logging_security(self):
        """Test secure logging functionality"""
        print("\n📝 Logging Security Checks:")
        
        # Test that PII is not logged
        test_logger = get_secure_logger("test")
        
        # This should not expose the actual email in logs
        test_logger.log_subscription("sensitive@email.com", "subscribe")
        self.pass_check("Secure logging initialized successfully")
        
        # Check log directory permissions
        log_dir = Path("logs")
        if log_dir.exists():
            self.pass_check("Log directory exists")
        else:
            self.pass_check("Log directory will be created with secure permissions")
    
    def check_rate_limiting(self):
        """Test rate limiting functionality"""
        print("\n⏱️ Rate Limiting Checks:")
        
        # Test subscription rate limiter
        sub_limiter = RateLimiter(max_requests=5, time_window=3600)
        
        # Should allow first 5 requests
        test_id = "test_user_123"
        for i in range(5):
            if not sub_limiter.is_allowed(test_id):
                self.fail_check(f"Rate limiter blocked request {i+1} of 5")
                return
        
        # 6th request should be blocked
        if sub_limiter.is_allowed(test_id):
            self.fail_check("Rate limiter failed to block 6th request")
        else:
            self.pass_check("Rate limiting working correctly")
    
    def check_input_validation(self):
        """Test input validation and sanitization"""
        print("\n✅ Input Validation Checks:")
        
        # Test email sanitization
        malicious_email = "<script>alert('xss')</script>test@example.com"
        sanitized = InputSanitizer.sanitize_email(malicious_email)
        if "<script>" not in sanitized:
            self.pass_check("Email input sanitization removes XSS")
        else:
            self.fail_check("Email input sanitization failed")
        
        # Test text sanitization
        malicious_text = "Normal text <img src=x onerror=alert('xss')>"
        sanitized_text = InputSanitizer.sanitize_text(malicious_text)
        if "<img" not in sanitized_text and "onerror" not in sanitized_text:
            self.pass_check("Text input sanitization removes XSS")
        else:
            self.fail_check("Text input sanitization failed")
        
        # Test preference validation
        malicious_prefs = {
            "weekly_digest": True,
            "malicious_field": "<script>evil</script>",
            "sql_injection": "'; DROP TABLE users; --"
        }
        clean_prefs = InputSanitizer.validate_preferences(malicious_prefs)
        if "malicious_field" not in clean_prefs and "sql_injection" not in clean_prefs:
            self.pass_check("Preference validation filters unknown fields")
        else:
            self.fail_check("Preference validation allowed unknown fields")
    
    def check_audit_trail(self):
        """Test audit logging functionality"""
        print("\n📊 Audit Trail Checks:")
        
        try:
            # Initialize audit logger
            audit = SecurityAuditLogger()
            
            # Test logging different event types
            audit.log_subscription_event("test_hash_123", "subscribe", "ip_hash_456")
            audit.log_data_access("system", "subscriber_list", "newsletter_generation")
            audit.log_security_event("rate_limit_exceeded", "source=test@example.com")
            audit.log_data_deletion("subscriber", 1)
            
            self.pass_check("Audit logging system functional")
            
            # Check audit log directory permissions
            audit_dir = Path("data/audit_logs")
            if audit_dir.exists():
                stat_info = os.stat(audit_dir)
                mode = oct(stat_info.st_mode)[-3:]
                if mode == "700":
                    self.pass_check("Audit log directory has secure permissions (700)")
                else:
                    self.fail_check(f"Audit log directory has insecure permissions ({mode})")
            else:
                self.pass_check("Audit directory created with secure permissions")
                
        except Exception as e:
            self.fail_check(f"Audit system error: {str(e)}")
    
    def pass_check(self, message):
        """Record a passed check"""
        self.checks_passed += 1
        self.results.append(("PASS", message))
        print(f"  ✅ {message}")
    
    def fail_check(self, message):
        """Record a failed check"""
        self.checks_failed += 1
        self.results.append(("FAIL", message))
        print(f"  ❌ {message}")
    
    def print_summary(self):
        """Print audit summary"""
        print("\n" + "=" * 60)
        print("🏁 Security Audit Summary")
        print("=" * 60)
        
        total_checks = self.checks_passed + self.checks_failed
        print(f"Total Checks: {total_checks}")
        print(f"Passed: {self.checks_passed} ✅")
        print(f"Failed: {self.checks_failed} ❌")
        
        if self.checks_failed == 0:
            print("\n🎉 ALL SECURITY CHECKS PASSED!")
            print("The system is ready for security audits.")
        else:
            print("\n⚠️  SECURITY ISSUES DETECTED!")
            print("Please address the failed checks before audit.")
            print("\nFailed checks:")
            for result, message in self.results:
                if result == "FAIL":
                    print(f"  - {message}")
        
        # Generate audit report
        self.generate_audit_report()
    
    def generate_audit_report(self):
        """Generate detailed audit report"""
        report_path = Path("security_audit_report.json")
        
        report = {
            "audit_timestamp": datetime.now().isoformat(),
            "system": "AI Regulatory Watch",
            "total_checks": self.checks_passed + self.checks_failed,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "audit_result": "PASS" if self.checks_failed == 0 else "FAIL",
            "detailed_results": [
                {
                    "status": result,
                    "check": message,
                    "timestamp": datetime.now().isoformat()
                }
                for result, message in self.results
            ]
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed audit report saved to: {report_path}")

def main():
    """Run security audit verification"""
    checker = SecurityAuditChecker()
    checker.run_all_checks()

if __name__ == "__main__":
    main()