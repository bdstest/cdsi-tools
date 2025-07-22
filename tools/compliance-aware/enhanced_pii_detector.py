#!/usr/bin/env python3
"""
Enhanced PII Detection for CDSI - DRAFT
Advanced personal data identification with international compliance support

Contact: consulting@getcdsi.com
Website: getcdsi.com
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

@dataclass
class PIIMatch:
    """Represents a detected PII match"""
    pattern_type: str
    value: str
    confidence: float
    line_number: int
    context: str
    risk_level: str

class EnhancedPIIDetector:
    """Enhanced PII detection with international compliance patterns"""
    
    def __init__(self):
        self.patterns = {
            # US Patterns
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b',
            'ein': r'\b\d{2}-\d{7}\b',
            'itin': r'\b9\d{2}-\d{2}-\d{4}\b',
            'passport_us': r'\b[A-Z]{1,2}\d{6,9}\b',
            
            # International ID Patterns
            'uk_nino': r'\b[A-CEGHJ-PR-TW-Z]{1}[A-CEGHJ-NPR-TW-Z]{1}[0-9]{6}[A-D]{1}\b',
            'canada_sin': r'\b\d{3}-\d{3}-\d{3}\b',
            'australia_tfn': r'\b\d{3}\s\d{3}\s\d{3}\b',
            'germany_tax': r'\b\d{2}\s\d{3}\s\d{3}\s\d{3}\b',
            
            # EU GDPR Special Categories
            'iban': r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}([A-Z0-9]?){0,16}\b',
            'swift_bic': r'\b[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?\b',
            
            # Healthcare (HIPAA/GDPR Article 9)
            'medical_record': r'\bMRN:?\s*\d{6,10}\b',
            'patient_id': r'\bPT:?\s*\d{6,12}\b',
            'prescription': r'\bRX:?\s*\d{8,12}\b',
            'insurance_member': r'\bINS:?\s*[A-Z0-9]{8,15}\b',
            
            # Financial (PCI DSS Enhanced)
            'credit_card_visa': r'\b4[0-9]{12}(?:[0-9]{3})?\b',
            'credit_card_mc': r'\b5[1-5][0-9]{14}\b',
            'credit_card_amex': r'\b3[47][0-9]{13}\b',
            'credit_card_discover': r'\b6(?:011|5[0-9]{2})[0-9]{12}\b',
            'bank_routing': r'\b[0-9]{9}\b',
            'bank_account': r'\bACC:?\s*[0-9]{8,17}\b',
            
            # Biometric (GDPR Article 9 Special Category)
            'biometric_template': r'\bBIO:?\s*[A-F0-9]{32,128}\b',
            'facial_encoding': r'\bFACE:?\s*[A-F0-9]{64,256}\b',
            'fingerprint_hash': r'\bFP:?\s*[A-F0-9]{40,128}\b',
            
            # Communication
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone_us': r'\b(?:\+1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
            'phone_uk': r'\b(?:\+44[-.]?)?(?:\(?0\)?[-.]?)?[1-9]\d{8,9}\b',
            'phone_eu': r'\b(?:\+[1-9]\d{1,3}[-.]?)?(?:\(?0\)?[-.]?)?[1-9]\d{6,14}\b',
            
            # Geographic
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'mac_address': r'\b[0-9A-Fa-f]{2}[:-]([0-9A-Fa-f]{2}[:-]){4}[0-9A-Fa-f]{2}\b',
            'gps_coordinates': r'\b-?\d{1,3}\.\d{4,},\s*-?\d{1,3}\.\d{4,}\b',
            'postal_code_us': r'\b\d{5}(?:-\d{4})?\b',
            'postal_code_uk': r'\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b',
            'postal_code_ca': r'\b[A-Z]\d[A-Z]\s*\d[A-Z]\d\b',
            
            # Dates (Potential DOB)
            'date_us': r'\b(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])/(19|20)\d{2}\b',
            'date_eu': r'\b(0?[1-9]|[12]\d|3[01])/(0?[1-9]|1[0-2])/(19|20)\d{2}\b',
            'date_iso': r'\b(19|20)\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b',
            
            # Employment/HR
            'employee_id': r'\bEMP:?\s*[A-Z0-9]{6,12}\b',
            'badge_number': r'\bBDG:?\s*[A-Z0-9]{4,10}\b',
            'salary': r'\$[0-9]{2,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?\b',
            
            # Legal/Court
            'case_number': r'\bCASE:?\s*[A-Z0-9]{8,15}\b',
            'docket_number': r'\bDOCKET:?\s*[A-Z0-9]{6,12}\b',
            
            # Education (FERPA)
            'student_id': r'\bSTU:?\s*[A-Z0-9]{6,12}\b',
            'grade': r'\bGRADE:?\s*[A-F][+-]?\b',
            
            # Digital Identity
            'username': r'\bUSER:?\s*[A-Za-z0-9._-]{3,20}\b',
            'device_id': r'\bDEV:?\s*[A-F0-9]{12,40}\b',
            'session_token': r'\bTOKEN:?\s*[A-Za-z0-9+/]{32,128}=*\b'
        }
        
        self.risk_levels = {
            # Critical Risk (immediate breach notification)
            'critical': ['ssn', 'credit_card_visa', 'credit_card_mc', 'credit_card_amex', 
                        'passport_us', 'biometric_template', 'medical_record'],
            
            # High Risk (significant compliance impact)
            'high': ['bank_account', 'bank_routing', 'patient_id', 'prescription', 
                    'facial_encoding', 'fingerprint_hash', 'insurance_member'],
            
            # Medium Risk (regulated but less severe)
            'medium': ['email', 'phone_us', 'phone_uk', 'employee_id', 'student_id', 
                      'iban', 'swift_bic', 'uk_nino', 'canada_sin'],
            
            # Low Risk (potentially sensitive)
            'low': ['ip_address', 'postal_code_us', 'date_us', 'username', 'device_id']
        }
        
        self.compliance_frameworks = {
            'GDPR': ['email', 'biometric_template', 'facial_encoding', 'medical_record', 
                    'iban', 'uk_nino', 'phone_eu', 'gps_coordinates'],
            'HIPAA': ['medical_record', 'patient_id', 'prescription', 'insurance_member'],
            'PCI_DSS': ['credit_card_visa', 'credit_card_mc', 'credit_card_amex', 
                       'credit_card_discover', 'bank_account', 'bank_routing'],
            'CCPA': ['ssn', 'email', 'phone_us', 'ip_address', 'gps_coordinates', 
                    'biometric_template'],
            'FERPA': ['student_id', 'grade', 'email'],
            'SOX': ['employee_id', 'salary', 'bank_account']
        }
    
    def scan_text(self, text: str, context_chars: int = 50) -> List[PIIMatch]:
        """Scan text for PII patterns with enhanced detection"""
        matches = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern_name, pattern in self.patterns.items():
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    # Extract context around match
                    start = max(0, match.start() - context_chars)
                    end = min(len(line), match.end() + context_chars)
                    context = line[start:end]
                    
                    # Calculate confidence based on context
                    confidence = self._calculate_confidence(pattern_name, match.group(), context)
                    
                    # Determine risk level
                    risk_level = self._get_risk_level(pattern_name)
                    
                    matches.append(PIIMatch(
                        pattern_type=pattern_name,
                        value=match.group(),
                        confidence=confidence,
                        line_number=line_num,
                        context=context,
                        risk_level=risk_level
                    ))
        
        return matches
    
    def _calculate_confidence(self, pattern_name: str, value: str, context: str) -> float:
        """Calculate confidence score for PII match"""
        base_confidence = 0.7
        
        # Boost confidence for certain patterns
        high_confidence_patterns = ['ssn', 'credit_card_visa', 'email', 'iban']
        if pattern_name in high_confidence_patterns:
            base_confidence = 0.9
        
        # Context-based adjustments
        context_lower = context.lower()
        
        # Positive indicators
        positive_keywords = {
            'ssn': ['social', 'security', 'ssn'],
            'email': ['email', 'contact', 'address'],
            'phone_us': ['phone', 'tel', 'mobile', 'cell'],
            'credit_card_visa': ['card', 'visa', 'payment'],
            'medical_record': ['patient', 'medical', 'health']
        }
        
        if pattern_name in positive_keywords:
            for keyword in positive_keywords[pattern_name]:
                if keyword in context_lower:
                    base_confidence += 0.1
        
        # Negative indicators (likely false positives)
        negative_keywords = ['test', 'sample', 'example', 'dummy', 'fake']
        for keyword in negative_keywords:
            if keyword in context_lower:
                base_confidence -= 0.2
        
        return min(1.0, max(0.1, base_confidence))
    
    def _get_risk_level(self, pattern_name: str) -> str:
        """Get risk level for pattern type"""
        for level, patterns in self.risk_levels.items():
            if pattern_name in patterns:
                return level
        return 'low'
    
    def get_compliance_impact(self, matches: List[PIIMatch]) -> Dict[str, List[str]]:
        """Analyze compliance framework impact"""
        impact = {}
        
        for framework, patterns in self.compliance_frameworks.items():
            affected_patterns = []
            for match in matches:
                if match.pattern_type in patterns and match.confidence > 0.6:
                    affected_patterns.append(match.pattern_type)
            
            if affected_patterns:
                impact[framework] = list(set(affected_patterns))
        
        return impact
    
    def generate_risk_report(self, matches: List[PIIMatch]) -> Dict:
        """Generate comprehensive risk assessment report"""
        if not matches:
            return {
                "risk_level": "NONE",
                "summary": "No PII detected",
                "recommendations": ["Continue monitoring data inputs"]
            }
        
        # Count by risk level
        risk_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for match in matches:
            if match.confidence > 0.6:
                risk_counts[match.risk_level] += 1
        
        # Determine overall risk
        if risk_counts['critical'] > 0:
            overall_risk = "CRITICAL"
        elif risk_counts['high'] > 5:
            overall_risk = "HIGH"
        elif risk_counts['high'] > 0 or risk_counts['medium'] > 10:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
        
        # Generate recommendations
        recommendations = []
        if risk_counts['critical'] > 0:
            recommendations.append("IMMEDIATE ACTION: Critical PII detected - implement encryption")
            recommendations.append("Review data access controls and audit logging")
        
        if risk_counts['high'] > 0:
            recommendations.append("Implement data classification and handling procedures")
            recommendations.append("Consider data anonymization or pseudonymization")
        
        compliance_impact = self.get_compliance_impact(matches)
        if compliance_impact:
            frameworks = ', '.join(compliance_impact.keys())
            recommendations.append(f"Review compliance requirements for: {frameworks}")
        
        recommendations.extend([
            "Regular PII discovery scanning recommended",
            "Staff training on data handling procedures",
            "Contact consulting@getcdsi.com for advanced data governance"
        ])
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "risk_level": overall_risk,
            "total_matches": len(matches),
            "high_confidence_matches": len([m for m in matches if m.confidence > 0.8]),
            "risk_distribution": risk_counts,
            "compliance_frameworks_affected": list(compliance_impact.keys()),
            "summary": f"{overall_risk} risk level with {len(matches)} PII instances detected",
            "recommendations": recommendations
        }

def main():
    """Test the enhanced PII detector"""
    detector = EnhancedPIIDetector()
    
    # Test data with various PII types
    test_data = """
    Customer Information:
    Name: John Smith
    SSN: 123-45-6789
    Email: john.smith@example.com
    Phone: (555) 123-4567
    Credit Card: 4111-1111-1111-1111
    Medical Record: MRN: 1234567890
    Employee ID: EMP: ABC123456
    IP Address: 192.168.1.100
    
    International Data:
    UK NINO: AB123456C
    IBAN: GB82WEST12345698765432
    Canadian SIN: 123-456-789
    
    Test data - this should be flagged as test
    Sample SSN: 000-00-0000
    """
    
    print("Enhanced PII Detection - DRAFT VERSION")
    print("=" * 50)
    
    matches = detector.scan_text(test_data)
    
    print(f"Found {len(matches)} potential PII matches:")
    for match in matches:
        print(f"  {match.pattern_type}: {match.value} "
              f"(confidence: {match.confidence:.2f}, risk: {match.risk_level})")
    
    print("\nRisk Assessment:")
    risk_report = detector.generate_risk_report(matches)
    print(f"Overall Risk: {risk_report['risk_level']}")
    print(f"Summary: {risk_report['summary']}")
    
    print("\nCompliance Impact:")
    compliance_impact = detector.get_compliance_impact(matches)
    for framework, patterns in compliance_impact.items():
        print(f"  {framework}: {', '.join(patterns)}")
    
    print(f"\nContact consulting@getcdsi.com for production implementation")

if __name__ == "__main__":
    main()