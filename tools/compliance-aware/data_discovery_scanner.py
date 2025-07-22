#!/usr/bin/env python3
"""
CDSI Data Discovery Scanner - Level 1: COMPLIANCE AWARE

Helps organizations discover personal data across their file systems
to understand what they're working with for GDPR/CCPA compliance.

Contact: consulting@getcdsi.com
Website: getcdsi.com
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path

class CDSIDataDiscoveryScanner:
    """CDSI Data Discovery Scanner for Personal Data"""
    
    def __init__(self):
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b',
            'phone': r'\b\(\d{3}\)\s?\d{3}-\d{4}\b|\b\d{3}-\d{3}-\d{4}\b',
            'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'date_of_birth': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b',
            'drivers_license': r'\b[A-Z]{1,2}\d{6,8}\b'
        }
        
        self.sensitive_file_patterns = [
            r'.*\.csv$', r'.*\.xlsx?$', r'.*\.json$', r'.*\.xml$',
            r'.*\.sql$', r'.*\.db$', r'.*\.sqlite$', r'.*log$'
        ]
        
        self.results = {
            'scan_timestamp': datetime.now().isoformat(),
            'files_scanned': 0,
            'pii_matches': {},
            'high_risk_files': [],
            'summary': {},
            'recommendations': []
        }
    
    def scan_directory(self, directory_path, max_files=100):
        """Scan directory for personal data patterns"""
        print(f"🔍 CDSI Data Discovery Scanner")
        print("=" * 50)
        print(f"Scanning: {directory_path}")
        print(f"Looking for: {', '.join(self.pii_patterns.keys())}")
        print()
        
        directory = Path(directory_path)
        files_scanned = 0
        
        for file_path in directory.rglob('*'):
            if files_scanned >= max_files:
                print(f"⚠️  Scan limited to {max_files} files. Use full version for complete scan.")
                break
                
            if file_path.is_file() and self._should_scan_file(file_path):
                try:
                    self._scan_file(file_path)
                    files_scanned += 1
                    if files_scanned % 10 == 0:
                        print(f"📊 Scanned {files_scanned} files...")
                        
                except Exception as e:
                    print(f"⚠️  Skipped {file_path}: {e}")
        
        self.results['files_scanned'] = files_scanned
        self._generate_summary()
        return self.results
    
    def _should_scan_file(self, file_path):
        """Determine if file should be scanned based on extension"""
        file_str = str(file_path).lower()
        
        # Skip binary files that are unlikely to contain readable PII
        skip_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', 
                          '.tar', '.gz', '.exe', '.dll', '.so', '.dylib']
        
        if any(file_str.endswith(ext) for ext in skip_extensions):
            return False
            
        # Focus on files likely to contain structured data
        return any(re.match(pattern, file_str) for pattern in self.sensitive_file_patterns)
    
    def _scan_file(self, file_path):
        """Scan individual file for PII patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(10000)  # Limit to first 10KB for performance
                
            file_matches = {}
            for pii_type, pattern in self.pii_patterns.items():
                matches = re.findall(pattern, content)
                if matches:
                    file_matches[pii_type] = len(matches)
            
            if file_matches:
                self.results['pii_matches'][str(file_path)] = file_matches
                
                # Calculate risk score
                risk_score = sum(file_matches.values())
                if risk_score >= 10:  # High risk threshold
                    self.results['high_risk_files'].append({
                        'file': str(file_path),
                        'risk_score': risk_score,
                        'pii_types': list(file_matches.keys())
                    })
                    
        except Exception as e:
            pass  # Skip files that can't be read
    
    def _generate_summary(self):
        """Generate summary statistics and recommendations"""
        total_files_with_pii = len(self.results['pii_matches'])
        total_pii_instances = sum(
            sum(matches.values()) for matches in self.results['pii_matches'].values()
        )
        high_risk_files = len(self.results['high_risk_files'])
        
        self.results['summary'] = {
            'files_with_pii': total_files_with_pii,
            'total_pii_instances': total_pii_instances,
            'high_risk_files': high_risk_files,
            'pii_types_found': self._get_unique_pii_types()
        }
        
        # Generate recommendations based on findings
        recommendations = []
        
        if high_risk_files > 0:
            recommendations.append(f"🚨 {high_risk_files} high-risk files need immediate attention")
            recommendations.append("Implement data classification and access controls")
        
        if total_files_with_pii > 0:
            recommendations.append("Create data inventory documentation (GDPR Article 30)")
            recommendations.append("Implement data retention and deletion policies")
            recommendations.append("Review data processing purposes and legal bases")
        
        if 'email' in self.results['summary']['pii_types_found']:
            recommendations.append("Ensure email marketing consent compliance")
        
        if 'ssn' in self.results['summary']['pii_types_found']:
            recommendations.append("Implement additional security for SSN data")
        
        recommendations.extend([
            "Consider data minimization opportunities",
            "Implement regular data discovery scanning",
            "Train staff on data handling procedures"
        ])
        
        self.results['recommendations'] = recommendations
    
    def _get_unique_pii_types(self):
        """Get list of unique PII types found across all files"""
        pii_types = set()
        for file_matches in self.results['pii_matches'].values():
            pii_types.update(file_matches.keys())
        return list(pii_types)
    
    def generate_report(self):
        """Generate comprehensive discovery report"""
        print(f"\n🎯 CDSI DATA DISCOVERY REPORT")
        print("=" * 50)
        
        summary = self.results['summary']
        print(f"📊 SUMMARY:")
        print(f"  Files Scanned: {self.results['files_scanned']}")
        print(f"  Files with PII: {summary['files_with_pii']}")
        print(f"  Total PII Instances: {summary['total_pii_instances']}")
        print(f"  High-Risk Files: {summary['high_risk_files']}")
        print(f"  PII Types Found: {', '.join(summary['pii_types_found']) if summary['pii_types_found'] else 'None'}")
        
        if self.results['high_risk_files']:
            print(f"\n🚨 HIGH-RISK FILES:")
            for file_info in self.results['high_risk_files'][:5]:  # Show top 5
                print(f"  {file_info['file']} (Score: {file_info['risk_score']})")
        
        print(f"\n🚀 RECOMMENDATIONS:")
        for i, rec in enumerate(self.results['recommendations'][:8], 1):
            print(f"  {i}. {rec}")
        
        print(f"\n📧 Next Steps:")
        print(f"Visit getcdsi.com for COMPLIANCE AWARE level tools")
        print(f"Contact: consulting@getcdsi.com for data governance consulting")
        
        # Save results to file
        output_file = f"cdsi_data_discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {output_file}")
        return self.results

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python data_discovery_scanner.py <directory_path>")
        print("Example: python data_discovery_scanner.py /path/to/data")
        sys.exit(1)
    
    scanner = CDSIDataDiscoveryScanner()
    results = scanner.scan_directory(sys.argv[1])
    scanner.generate_report()