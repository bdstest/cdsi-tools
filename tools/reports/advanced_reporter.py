#!/usr/bin/env python3
"""
Advanced Compliance Reporting for CDSI - DRAFT
Professional report generation with multiple formats and visualizations

Contact: consulting@getcdsi.com
Website: getcdsi.com
"""

import json
import csv
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import base64

@dataclass
class ComplianceMetric:
    """Represents a compliance metric"""
    name: str
    value: float
    target: float
    status: str  # compliant, warning, non_compliant
    framework: str
    last_updated: datetime

@dataclass
class AuditFinding:
    """Represents an audit finding"""
    finding_id: str
    severity: str  # critical, high, medium, low
    title: str
    description: str
    recommendation: str
    affected_systems: List[str]
    compliance_frameworks: List[str]
    due_date: Optional[datetime]
    assigned_to: str
    status: str  # open, in_progress, resolved

class AdvancedComplianceReporter:
    """Advanced compliance reporting with multiple output formats"""
    
    def __init__(self):
        self.report_templates = {
            'executive_summary': self._executive_summary_template,
            'detailed_audit': self._detailed_audit_template,
            'risk_assessment': self._risk_assessment_template,
            'gap_analysis': self._gap_analysis_template,
            'compliance_dashboard': self._dashboard_template
        }
        
        self.supported_formats = ['json', 'csv', 'xml', 'html', 'pdf']
        
    def generate_executive_summary(self, metrics: List[ComplianceMetric], 
                                 findings: List[AuditFinding]) -> Dict[str, Any]:
        """Generate executive summary report"""
        # Calculate overall compliance score
        total_score = sum(min(m.value / m.target, 1.0) for m in metrics)
        compliance_percentage = (total_score / len(metrics)) * 100 if metrics else 0
        
        # Categorize findings by severity
        finding_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for finding in findings:
            if finding.status != 'resolved':
                finding_counts[finding.severity] += 1
        
        # Framework compliance breakdown
        framework_scores = {}
        for framework in set(m.framework for m in metrics):
            framework_metrics = [m for m in metrics if m.framework == framework]
            framework_score = sum(min(m.value / m.target, 1.0) for m in framework_metrics)
            framework_scores[framework] = (framework_score / len(framework_metrics)) * 100
        
        # Risk level determination
        if finding_counts['critical'] > 0:
            risk_level = "CRITICAL"
            risk_color = "#FF0000"
        elif finding_counts['high'] > 2:
            risk_level = "HIGH"
            risk_color = "#FF6600"
        elif finding_counts['high'] > 0 or finding_counts['medium'] > 5:
            risk_level = "MEDIUM"
            risk_color = "#FFAA00"
        else:
            risk_level = "LOW"
            risk_color = "#00AA00"
        
        # Key recommendations
        recommendations = []
        if finding_counts['critical'] > 0:
            recommendations.append("IMMEDIATE: Address critical compliance gaps")
        if compliance_percentage < 80:
            recommendations.append("Implement comprehensive compliance improvement plan")
        if finding_counts['high'] > 0:
            recommendations.append("Prioritize high-severity findings resolution")
        
        recommendations.extend([
            "Regular compliance monitoring and assessment",
            "Staff training on regulatory requirements",
            "Contact consulting@getcdsi.com for remediation support"
        ])
        
        return {
            "report_type": "executive_summary",
            "generated_date": datetime.utcnow().isoformat(),
            "reporting_period": {
                "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end_date": datetime.utcnow().isoformat()
            },
            "overall_compliance": {
                "percentage": round(compliance_percentage, 1),
                "status": "Compliant" if compliance_percentage >= 90 else "Non-Compliant",
                "total_metrics": len(metrics)
            },
            "risk_assessment": {
                "level": risk_level,
                "color": risk_color,
                "open_findings": sum(finding_counts.values()),
                "finding_breakdown": finding_counts
            },
            "framework_compliance": framework_scores,
            "key_recommendations": recommendations,
            "next_review_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
    
    def generate_detailed_audit_report(self, findings: List[AuditFinding], 
                                     metrics: List[ComplianceMetric]) -> Dict[str, Any]:
        """Generate detailed audit report with findings and evidence"""
        # Group findings by framework
        framework_findings = {}
        for finding in findings:
            for framework in finding.compliance_frameworks:
                if framework not in framework_findings:
                    framework_findings[framework] = []
                framework_findings[framework].append(finding)
        
        # Calculate remediation timeline
        overdue_findings = [f for f in findings if f.due_date and f.due_date < datetime.utcnow()]
        due_soon = [f for f in findings if f.due_date and 
                   f.due_date > datetime.utcnow() and 
                   f.due_date < datetime.utcnow() + timedelta(days=30)]
        
        # Control effectiveness analysis
        control_effectiveness = {}
        for metric in metrics:
            effectiveness = min(metric.value / metric.target, 1.0)
            control_effectiveness[metric.name] = {
                "percentage": round(effectiveness * 100, 1),
                "status": "Effective" if effectiveness >= 0.9 else "Needs Improvement",
                "framework": metric.framework
            }
        
        return {
            "report_type": "detailed_audit",
            "generated_date": datetime.utcnow().isoformat(),
            "audit_scope": "Full Organizational Compliance Assessment",
            "findings_summary": {
                "total_findings": len(findings),
                "by_severity": {
                    severity: len([f for f in findings if f.severity == severity])
                    for severity in ['critical', 'high', 'medium', 'low']
                },
                "by_status": {
                    status: len([f for f in findings if f.status == status])
                    for status in ['open', 'in_progress', 'resolved']
                }
            },
            "framework_analysis": {
                framework: {
                    "findings_count": len(framework_findings.get(framework, [])),
                    "critical_findings": len([f for f in framework_findings.get(framework, []) 
                                            if f.severity == 'critical']),
                    "compliance_metrics": [m.name for m in metrics if m.framework == framework]
                }
                for framework in set(f.compliance_frameworks[0] for f in findings if f.compliance_frameworks)
            },
            "remediation_timeline": {
                "overdue_findings": len(overdue_findings),
                "due_within_30_days": len(due_soon),
                "overdue_details": [
                    {
                        "id": f.finding_id,
                        "title": f.title,
                        "severity": f.severity,
                        "days_overdue": (datetime.utcnow() - f.due_date).days
                    }
                    for f in overdue_findings
                ]
            },
            "control_effectiveness": control_effectiveness,
            "detailed_findings": [asdict(f) for f in findings],
            "audit_methodology": "CDSI Compliance Assessment Framework",
            "next_audit_date": (datetime.utcnow() + timedelta(days=90)).isoformat()
        }
    
    def generate_risk_assessment_matrix(self, findings: List[AuditFinding]) -> Dict[str, Any]:
        """Generate risk assessment matrix and heat map data"""
        # Risk matrix: Probability vs Impact
        risk_matrix = {
            'critical': {'high_prob': [], 'medium_prob': [], 'low_prob': []},
            'high': {'high_prob': [], 'medium_prob': [], 'low_prob': []},
            'medium': {'high_prob': [], 'medium_prob': [], 'low_prob': []},
            'low': {'high_prob': [], 'medium_prob': [], 'low_prob': []}
        }
        
        # Simulate probability assessment based on affected systems
        for finding in findings:
            # More affected systems = higher probability
            system_count = len(finding.affected_systems)
            if system_count > 5:
                prob = 'high_prob'
            elif system_count > 2:
                prob = 'medium_prob'
            else:
                prob = 'low_prob'
            
            risk_matrix[finding.severity][prob].append({
                'id': finding.finding_id,
                'title': finding.title,
                'systems': system_count
            })
        
        # Calculate risk scores
        risk_scores = {
            'critical': {'high_prob': 9, 'medium_prob': 8, 'low_prob': 7},
            'high': {'high_prob': 7, 'medium_prob': 6, 'low_prob': 5},
            'medium': {'high_prob': 5, 'medium_prob': 4, 'low_prob': 3},
            'low': {'high_prob': 3, 'medium_prob': 2, 'low_prob': 1}
        }
        
        # Generate heat map data
        heat_map_data = []
        for impact in ['critical', 'high', 'medium', 'low']:
            for probability in ['high_prob', 'medium_prob', 'low_prob']:
                finding_count = len(risk_matrix[impact][probability])
                heat_map_data.append({
                    'impact': impact,
                    'probability': probability.replace('_prob', ''),
                    'risk_score': risk_scores[impact][probability],
                    'finding_count': finding_count,
                    'heat_value': risk_scores[impact][probability] * finding_count
                })
        
        # Risk treatment recommendations
        treatment_strategies = []
        high_risk_findings = []
        
        for impact in ['critical', 'high']:
            for prob in ['high_prob', 'medium_prob']:
                high_risk_findings.extend(risk_matrix[impact][prob])
        
        if high_risk_findings:
            treatment_strategies.extend([
                "IMMEDIATE: Implement risk mitigation controls",
                "Enhance monitoring and detection capabilities",
                "Develop incident response procedures"
            ])
        
        treatment_strategies.extend([
            "Regular risk assessment reviews",
            "Continuous compliance monitoring",
            "Contact consulting@getcdsi.com for risk management consulting"
        ])
        
        return {
            "report_type": "risk_assessment",
            "generated_date": datetime.utcnow().isoformat(),
            "risk_matrix": risk_matrix,
            "heat_map_data": heat_map_data,
            "risk_summary": {
                "total_risks": len(findings),
                "high_risk_count": len(high_risk_findings),
                "risk_distribution": {
                    severity: len([f for f in findings if f.severity == severity])
                    for severity in ['critical', 'high', 'medium', 'low']
                }
            },
            "treatment_strategies": treatment_strategies,
            "risk_appetite_statement": "Organization maintains low risk tolerance for compliance violations",
            "next_assessment_date": (datetime.utcnow() + timedelta(days=60)).isoformat()
        }
    
    def export_to_format(self, report_data: Dict[str, Any], format_type: str) -> str:
        """Export report to specified format"""
        if format_type not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format_type}")
        
        if format_type == 'json':
            return json.dumps(report_data, indent=2, default=str)
        
        elif format_type == 'csv':
            return self._export_to_csv(report_data)
        
        elif format_type == 'xml':
            return self._export_to_xml(report_data)
        
        elif format_type == 'html':
            return self._export_to_html(report_data)
        
        elif format_type == 'pdf':
            return self._export_to_pdf(report_data)
        
        else:
            return json.dumps(report_data, indent=2, default=str)
    
    def _export_to_csv(self, report_data: Dict[str, Any]) -> str:
        """Export report data to CSV format"""
        # Simplified CSV export for tabular data
        csv_content = []
        
        # Add header with report info
        csv_content.append("CDSI Compliance Report")
        csv_content.append(f"Generated: {report_data.get('generated_date', '')}")
        csv_content.append(f"Report Type: {report_data.get('report_type', '')}")
        csv_content.append("")
        
        # Add summary metrics if available
        if 'overall_compliance' in report_data:
            csv_content.append("Overall Compliance Summary")
            csv_content.append("Metric,Value")
            compliance = report_data['overall_compliance']
            csv_content.append(f"Compliance Percentage,{compliance.get('percentage', 0)}%")
            csv_content.append(f"Status,{compliance.get('status', 'Unknown')}")
            csv_content.append("")
        
        # Add findings if available
        if 'detailed_findings' in report_data:
            csv_content.append("Detailed Findings")
            csv_content.append("ID,Severity,Title,Status,Due Date,Assigned To")
            for finding in report_data['detailed_findings']:
                csv_content.append(
                    f"{finding.get('finding_id', '')},"
                    f"{finding.get('severity', '')},"
                    f"\"{finding.get('title', '')}\"," 
                    f"{finding.get('status', '')},"
                    f"{finding.get('due_date', '')},"
                    f"{finding.get('assigned_to', '')}"
                )
        
        csv_content.append("")
        csv_content.append("Generated by CDSI - consulting@getcdsi.com")
        
        return "\n".join(csv_content)
    
    def _export_to_xml(self, report_data: Dict[str, Any]) -> str:
        """Export report data to XML format"""
        root = ET.Element("CDSIComplianceReport")
        
        # Add metadata
        metadata = ET.SubElement(root, "Metadata")
        ET.SubElement(metadata, "GeneratedDate").text = report_data.get('generated_date', '')
        ET.SubElement(metadata, "ReportType").text = report_data.get('report_type', '')
        ET.SubElement(metadata, "Contact").text = "consulting@getcdsi.com"
        
        # Add compliance summary
        if 'overall_compliance' in report_data:
            compliance = ET.SubElement(root, "ComplianceSummary")
            for key, value in report_data['overall_compliance'].items():
                ET.SubElement(compliance, key.replace('_', '')).text = str(value)
        
        # Add findings
        if 'detailed_findings' in report_data:
            findings_elem = ET.SubElement(root, "Findings")
            for finding in report_data['detailed_findings']:
                finding_elem = ET.SubElement(findings_elem, "Finding")
                for key, value in finding.items():
                    if isinstance(value, list):
                        list_elem = ET.SubElement(finding_elem, key)
                        for item in value:
                            ET.SubElement(list_elem, "item").text = str(item)
                    else:
                        ET.SubElement(finding_elem, key).text = str(value)
        
        return ET.tostring(root, encoding='unicode')
    
    def _export_to_html(self, report_data: Dict[str, Any]) -> str:
        """Export report data to HTML format"""
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CDSI Compliance Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .metric {{ background-color: #e8f4f8; padding: 10px; margin: 5px 0; border-radius: 3px; }}
                .finding {{ border-left: 4px solid #ff6600; padding: 10px; margin: 10px 0; }}
                .critical {{ border-left-color: #ff0000; }}
                .high {{ border-left-color: #ff6600; }}
                .medium {{ border-left-color: #ffaa00; }}
                .low {{ border-left-color: #00aa00; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>CDSI Compliance Report</h1>
                <p><strong>Generated:</strong> {report_data.get('generated_date', '')}</p>
                <p><strong>Report Type:</strong> {report_data.get('report_type', '')}</p>
                <p><strong>Contact:</strong> consulting@getcdsi.com</p>
            </div>
        """
        
        # Add compliance summary
        if 'overall_compliance' in report_data:
            compliance = report_data['overall_compliance']
            html_template += f"""
            <div class="section">
                <h2>Compliance Summary</h2>
                <div class="metric">
                    <strong>Overall Compliance:</strong> {compliance.get('percentage', 0)}%
                </div>
                <div class="metric">
                    <strong>Status:</strong> {compliance.get('status', 'Unknown')}
                </div>
            </div>
            """
        
        # Add recommendations
        if 'key_recommendations' in report_data:
            html_template += """
            <div class="section">
                <h2>Key Recommendations</h2>
                <ul>
            """
            for rec in report_data['key_recommendations']:
                html_template += f"<li>{rec}</li>"
            html_template += "</ul></div>"
        
        html_template += """
            <div class="section">
                <p><em>This report was generated by CDSI compliance automation tools.</em></p>
                <p><strong>For implementation consulting:</strong> consulting@getcdsi.com</p>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _export_to_pdf(self, report_data: Dict[str, Any]) -> str:
        """Export report data to PDF format (placeholder)"""
        # In a real implementation, this would use a PDF library like reportlab
        pdf_placeholder = f"""
        PDF Report Generation (DRAFT)
        =============================
        
        Report Type: {report_data.get('report_type', '')}
        Generated: {report_data.get('generated_date', '')}
        
        This is a placeholder for PDF generation.
        Full PDF implementation available in production version.
        
        Contact: consulting@getcdsi.com for PDF reporting capabilities.
        
        Base64 Encoded PDF Content: {base64.b64encode(b'PDF_PLACEHOLDER_CONTENT').decode()}
        """
        
        return pdf_placeholder
    
    def _executive_summary_template(self) -> str:
        """Template for executive summary reports"""
        return "executive_summary_template"
    
    def _detailed_audit_template(self) -> str:
        """Template for detailed audit reports"""
        return "detailed_audit_template"
    
    def _risk_assessment_template(self) -> str:
        """Template for risk assessment reports"""
        return "risk_assessment_template"
    
    def _gap_analysis_template(self) -> str:
        """Template for gap analysis reports"""
        return "gap_analysis_template"
    
    def _dashboard_template(self) -> str:
        """Template for compliance dashboard"""
        return "dashboard_template"

def main():
    """Test the advanced compliance reporter"""
    reporter = AdvancedComplianceReporter()
    
    # Sample data for testing
    sample_metrics = [
        ComplianceMetric("Data Protection Controls", 85, 90, "warning", "GDPR", datetime.utcnow()),
        ComplianceMetric("Access Management", 95, 90, "compliant", "SOC2", datetime.utcnow()),
        ComplianceMetric("Incident Response", 70, 90, "non_compliant", "HIPAA", datetime.utcnow())
    ]
    
    sample_findings = [
        AuditFinding(
            "F001", "critical", "Unencrypted PII Storage", 
            "Personal data stored without encryption", 
            "Implement encryption at rest",
            ["Database", "File Storage"], ["GDPR", "HIPAA"],
            datetime.utcnow() + timedelta(days=7), "Security Team", "open"
        ),
        AuditFinding(
            "F002", "high", "Missing Access Logs",
            "Access logging not enabled on critical systems",
            "Enable comprehensive access logging",
            ["Application Server"], ["SOC2"],
            datetime.utcnow() + timedelta(days=14), "IT Team", "in_progress"
        )
    ]
    
    print("Advanced Compliance Reporting - DRAFT VERSION")
    print("=" * 50)
    
    # Generate executive summary
    exec_summary = reporter.generate_executive_summary(sample_metrics, sample_findings)
    print(f"Executive Summary Generated")
    print(f"Overall Compliance: {exec_summary['overall_compliance']['percentage']}%")
    print(f"Risk Level: {exec_summary['risk_assessment']['level']}")
    
    # Generate detailed audit report
    audit_report = reporter.generate_detailed_audit_report(sample_findings, sample_metrics)
    print(f"\nDetailed Audit Report Generated")
    print(f"Total Findings: {audit_report['findings_summary']['total_findings']}")
    
    # Generate risk assessment
    risk_assessment = reporter.generate_risk_assessment_matrix(sample_findings)
    print(f"\nRisk Assessment Generated")
    print(f"Total Risks: {risk_assessment['risk_summary']['total_risks']}")
    
    # Test format exports
    print(f"\nTesting Export Formats:")
    for format_type in ['json', 'csv', 'html']:
        try:
            exported = reporter.export_to_format(exec_summary, format_type)
            print(f"✓ {format_type.upper()} export successful ({len(exported)} chars)")
        except Exception as e:
            print(f"✗ {format_type.upper()} export failed: {e}")
    
    print(f"\nContact consulting@getcdsi.com for production implementation")

if __name__ == "__main__":
    main()