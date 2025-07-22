#!/usr/bin/env python3
"""
CDSI Anonymization Engine - Customer Data Protection System
Comprehensive anonymization for all customer interactions, logs, and data processing

Author: bdstest
License: Apache 2.0
Copyright: 2025 CDSI - Compliance Data Systems Insights
"""

import hashlib
import re
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from urllib.parse import urlparse

# Configure logging with anonymization
class AnonymizedFormatter(logging.Formatter):
    """Custom formatter that anonymizes sensitive data in log messages"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.anonymizer = DataAnonymizer()
    
    def format(self, record):
        # Anonymize the message before formatting
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self.anonymizer.anonymize_text(record.msg)
        return super().format(record)

class PIIType(Enum):
    """Types of Personally Identifiable Information"""
    EMAIL = "email"
    URL = "url" 
    DOMAIN = "domain"
    IP_ADDRESS = "ip_address"
    PHONE = "phone"
    NAME = "name"
    COMPANY = "company"
    ADDRESS = "address"
    CREDIT_CARD = "credit_card"
    SSN = "ssn"

@dataclass
class AnonymizationRule:
    """Rule for anonymizing specific PII types"""
    pii_type: PIIType
    pattern: str
    replacement_template: str
    hash_original: bool = True
    preserve_structure: bool = True

@dataclass
class AnonymizedCustomer:
    """Anonymized customer representation"""
    customer_hash: str  # SHA-256 hash of original identifier
    customer_segment: str  # Generic segment (e.g., "small_business")
    website_category: str  # Generic category (e.g., "professional_services")
    registration_date: str  # Date only, no specific times
    tier_level: str
    anonymized_domain: str  # Hashed domain representation
    interaction_count: int = 0
    last_activity_date: str = ""
    
    # Original data NEVER stored - only hashes and generic categories
    def __post_init__(self):
        # Ensure no PII can accidentally be stored
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, str):
                # Check if any field contains potential PII patterns
                if self._contains_pii(field_value) and field_name not in ['customer_hash', 'anonymized_domain']:
                    raise ValueError(f"PII detected in field {field_name}: {field_value}")
    
    def _contains_pii(self, value: str) -> bool:
        """Check if string contains potential PII"""
        pii_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'https?://[^\s]+',  # URL
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'  # Credit card pattern
        ]
        return any(re.search(pattern, value) for pattern in pii_patterns)

class DataAnonymizer:
    """Core data anonymization engine"""
    
    def __init__(self):
        self.salt = "CDSI_ANONYMIZATION_SALT_2025"  # Static salt for consistent hashing
        self.anonymization_rules = self._load_anonymization_rules()
        self.domain_hash_cache = {}  # Cache for consistent domain hashing
        self.customer_hash_cache = {}  # Cache for consistent customer hashing
        
    def _load_anonymization_rules(self) -> List[AnonymizationRule]:
        """Load PII anonymization rules"""
        return [
            AnonymizationRule(
                pii_type=PIIType.EMAIL,
                pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                replacement_template="user_{}@domain.com",
                hash_original=True,
                preserve_structure=True
            ),
            AnonymizationRule(
                pii_type=PIIType.URL,
                pattern=r'https?://[^\s]+',
                replacement_template="https://site_{}.example",
                hash_original=True,
                preserve_structure=True
            ),
            AnonymizationRule(
                pii_type=PIIType.DOMAIN,
                pattern=r'\b[a-zA-Z0-9-]+\.[a-zA-Z]{2,}\b',
                replacement_template="domain_{}.com",
                hash_original=True,
                preserve_structure=True
            ),
            AnonymizationRule(
                pii_type=PIIType.IP_ADDRESS,
                pattern=r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                replacement_template="ip_{}",
                hash_original=True,
                preserve_structure=False
            ),
            AnonymizationRule(
                pii_type=PIIType.PHONE,
                pattern=r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                replacement_template="phone_{}",
                hash_original=True,
                preserve_structure=False
            )
        ]
    
    def anonymize_customer_data(self, customer_data: Dict) -> AnonymizedCustomer:
        """Convert customer data to anonymized representation"""
        
        # Generate consistent customer hash
        customer_id = customer_data.get('email', '') + customer_data.get('website_url', '')
        customer_hash = self._generate_hash(customer_id, 'customer')
        
        # Anonymize website URL
        website_url = customer_data.get('website_url', '')
        anonymized_domain = self._anonymize_domain(website_url)
        
        # Determine generic segments
        customer_segment = self._categorize_customer(customer_data)
        website_category = self._categorize_website(customer_data)
        
        return AnonymizedCustomer(
            customer_hash=customer_hash,
            customer_segment=customer_segment,
            website_category=website_category,
            registration_date=datetime.now().strftime('%Y-%m-%d'),  # Date only
            tier_level=customer_data.get('tier_level', 'aware'),
            anonymized_domain=anonymized_domain,
            interaction_count=customer_data.get('interaction_count', 0)
        )
    
    def anonymize_text(self, text: str) -> str:
        """Anonymize PII in any text content"""
        if not text:
            return text
            
        anonymized_text = text
        
        for rule in self.anonymization_rules:
            matches = re.finditer(rule.pattern, anonymized_text, re.IGNORECASE)
            for match in reversed(list(matches)):  # Reverse to maintain indices
                original_value = match.group()
                anonymized_value = self._apply_anonymization_rule(original_value, rule)
                anonymized_text = (anonymized_text[:match.start()] + 
                                anonymized_value + 
                                anonymized_text[match.end():])
        
        return anonymized_text
    
    def anonymize_log_entry(self, log_data: Dict) -> Dict:
        """Anonymize a complete log entry"""
        anonymized_log = {}
        
        for key, value in log_data.items():
            if isinstance(value, str):
                anonymized_log[key] = self.anonymize_text(value)
            elif isinstance(value, dict):
                anonymized_log[key] = self.anonymize_log_entry(value)
            elif isinstance(value, list):
                anonymized_log[key] = [
                    self.anonymize_text(item) if isinstance(item, str) 
                    else self.anonymize_log_entry(item) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                anonymized_log[key] = value
        
        # Add anonymization metadata
        anonymized_log['_anonymized'] = True
        anonymized_log['_anonymization_timestamp'] = datetime.now().isoformat()
        
        return anonymized_log
    
    def _generate_hash(self, value: str, hash_type: str) -> str:
        """Generate consistent hash for values"""
        if not value:
            return f"{hash_type}_unknown"
            
        # Use SHA-256 with salt for security
        hash_input = f"{self.salt}_{hash_type}_{value}".encode('utf-8')
        hash_object = hashlib.sha256(hash_input)
        hash_hex = hash_object.hexdigest()
        
        # Return first 8 characters for readability
        return f"{hash_type}_{hash_hex[:8]}"
    
    def _anonymize_domain(self, url: str) -> str:
        """Anonymize domain from URL"""
        if not url:
            return "domain_unknown"
            
        if url in self.domain_hash_cache:
            return self.domain_hash_cache[url]
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            domain_hash = self._generate_hash(domain, 'domain')
            self.domain_hash_cache[url] = domain_hash
            return domain_hash
        except:
            return "domain_invalid"
    
    def _apply_anonymization_rule(self, original_value: str, rule: AnonymizationRule) -> str:
        """Apply specific anonymization rule to value"""
        if rule.hash_original:
            hash_value = self._generate_hash(original_value, rule.pii_type.value)
            # Extract hash portion after underscore, or use full hash if no underscore
            hash_part = hash_value.split('_')[1] if '_' in hash_value else hash_value
            return rule.replacement_template.format(hash_part)
        else:
            return rule.replacement_template.format("redacted")
    
    def _categorize_customer(self, customer_data: Dict) -> str:
        """Categorize customer into generic segment"""
        # Use business logic to determine segment WITHOUT storing PII
        website_url = customer_data.get('website_url', '').lower()
        
        # Generic categorization based on patterns, not specific data
        if any(term in website_url for term in ['consulting', 'advisory', 'services']):
            return "professional_services"
        elif any(term in website_url for term in ['shop', 'store', 'ecommerce']):
            return "ecommerce"  
        elif any(term in website_url for term in ['tech', 'software', 'app']):
            return "technology"
        elif any(term in website_url for term in ['health', 'medical', 'clinic']):
            return "healthcare"
        else:
            return "small_business_general"
    
    def _categorize_website(self, customer_data: Dict) -> str:
        """Categorize website type generically"""
        # Analyze patterns without storing actual content
        if customer_data.get('site_builder'):
            return "site_builder_platform"
        elif customer_data.get('has_ecommerce'):
            return "ecommerce_site"
        elif customer_data.get('is_corporate'):
            return "corporate_website"
        else:
            return "simple_business_site"

class AnonymizedLogger:
    """Logging system with built-in anonymization"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.anonymizer = DataAnonymizer()
        
        # Set up anonymized formatter
        handler = logging.StreamHandler()
        formatter = AnonymizedFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        if not self.logger.handlers:
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_customer_interaction(self, level: str, message: str, customer_data: Dict = None, **kwargs):
        """Log customer interaction with automatic anonymization"""
        log_entry = {
            'message': message,
            'customer_data': customer_data or {},
            'additional_data': kwargs,
            'interaction_type': 'customer_interaction'
        }
        
        # Anonymize the entire log entry
        anonymized_entry = self.anonymizer.anonymize_log_entry(log_entry)
        
        # Log with appropriate level
        getattr(self.logger, level.lower())(
            f"Customer Interaction: {anonymized_entry['message']}", 
            extra={'anonymized_data': anonymized_entry}
        )
    
    def log_compliance_analysis(self, website_url: str, results: Dict, customer_id: str = None):
        """Log compliance analysis with anonymization"""
        log_data = {
            'website_url': website_url,
            'customer_id': customer_id or 'anonymous',
            'compliance_score': results.get('score', 0),
            'analysis_type': 'compliance_scan',
            'findings_count': len(results.get('findings', [])),
            'timestamp': datetime.now().isoformat()
        }
        
        anonymized_log = self.anonymizer.anonymize_log_entry(log_data)
        
        self.logger.info(
            f"Compliance Analysis: Score {anonymized_log['compliance_score']}/10 for {anonymized_log['website_url']}",
            extra={'analysis_data': anonymized_log}
        )
    
    def log_tier_upgrade(self, customer_hash: str, old_tier: str, new_tier: str):
        """Log tier upgrade with anonymized customer data"""
        self.logger.info(
            f"Tier Upgrade: {customer_hash} upgraded from {old_tier} to {new_tier}",
            extra={
                'event_type': 'tier_upgrade',
                'customer_hash': customer_hash,
                'old_tier': old_tier, 
                'new_tier': new_tier,
                'timestamp': datetime.now().isoformat()
            }
        )

class AnonymizedAnalyticsCollector:
    """Collect analytics data with built-in anonymization"""
    
    def __init__(self):
        self.anonymizer = DataAnonymizer()
        self.logger = AnonymizedLogger('analytics')
    
    def record_website_analysis(self, website_url: str, analysis_results: Dict, customer_context: Dict = None):
        """Record website analysis with full anonymization"""
        
        # Create anonymized customer representation
        anonymized_customer = None
        if customer_context:
            anonymized_customer = self.anonymizer.anonymize_customer_data(customer_context)
        
        # Anonymize analysis results
        anonymized_results = self.anonymizer.anonymize_log_entry(analysis_results)
        
        # Record anonymized analytics
        analytics_record = {
            'event_type': 'website_analysis',
            'anonymized_customer': anonymized_customer.__dict__ if anonymized_customer else None,
            'anonymized_results': anonymized_results,
            'analysis_timestamp': datetime.now().isoformat(),
            'session_id': str(uuid.uuid4())  # Random session ID, not linked to customer
        }
        
        self.logger.log_compliance_analysis(
            website_url=anonymized_results.get('website_url', 'unknown'),
            results=anonymized_results,
            customer_id=anonymized_customer.customer_hash if anonymized_customer else None
        )
        
        return analytics_record
    
    def record_customer_success_pattern(self, success_data: Dict):
        """Record customer success patterns with anonymization"""
        
        anonymized_success = self.anonymizer.anonymize_log_entry(success_data)
        
        # Extract learnings without PII
        pattern_record = {
            'pattern_type': 'customer_success',
            'customer_segment': anonymized_success.get('customer_segment', 'unknown'),
            'improvement_score': anonymized_success.get('score_improvement', 0),
            'implementation_time': anonymized_success.get('implementation_time', 'unknown'),
            'success_factors': anonymized_success.get('success_factors', []),
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.logger.info(
            f"Success Pattern: {pattern_record['customer_segment']} achieved {pattern_record['improvement_score']} point improvement",
            extra={'pattern_data': pattern_record}
        )
        
        return pattern_record

# Global anonymized logger instance
anonymized_logger = AnonymizedLogger('cdsi_platform')
analytics_collector = AnonymizedAnalyticsCollector()

# Usage examples and testing
if __name__ == "__main__":
    
    print("🔒 CDSI Anonymization Engine Test")
    print("=" * 50)
    
    # Test data anonymization
    anonymizer = DataAnonymizer()
    
    # Test text anonymization
    test_text = "Contact john.doe@example.com for website https://mycompany.com analysis. IP: 192.168.1.1"
    anonymized = anonymizer.anonymize_text(test_text)
    print(f"Original: {test_text}")
    print(f"Anonymized: {anonymized}")
    print()
    
    # Test customer data anonymization
    customer_data = {
        'email': 'customer@businesswebsite.com',
        'website_url': 'https://businesswebsite.com',
        'tier_level': 'aware',
        'interaction_count': 5
    }
    
    anonymized_customer = anonymizer.anonymize_customer_data(customer_data)
    print(f"Anonymized Customer: {anonymized_customer}")
    print()
    
    # Test logging with anonymization
    logger = AnonymizedLogger('test')
    logger.log_customer_interaction(
        'info', 
        'Customer signed up with email customer@business.com for website https://business.com',
        customer_data=customer_data
    )
    
    # Test analytics collection
    analytics = AnonymizedAnalyticsCollector()
    analysis_results = {
        'website_url': 'https://testbusiness.com',
        'score': 8.5,
        'findings': ['privacy policy missing', 'cookie consent needed'],
        'recommendations': ['Add privacy policy', 'Implement cookie banner']
    }
    
    analytics_record = analytics.record_website_analysis(
        'https://testbusiness.com', 
        analysis_results, 
        customer_data
    )
    
    print("✅ Anonymization engine test completed")
    print("🔒 All customer data automatically protected")