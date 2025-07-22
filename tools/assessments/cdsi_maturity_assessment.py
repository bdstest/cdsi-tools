#!/usr/bin/env python3
"""
CDSI Compliance Maturity Assessment Tool

Helps organizations determine their current compliance maturity level
and provides roadmap for advancement to next level.

Contact: consulting@getcdsi.com
Website: getcdsi.com
"""

import json
from datetime import datetime

class CDSIMaturityAssessment:
    """CDSI Compliance Maturity Assessment Tool"""
    
    def __init__(self):
        self.assessment_areas = {
            'data_discovery': 'Do you know what personal data you collect and where it\'s stored?',
            'process_documentation': 'Are your compliance processes documented and followed?',
            'automation_level': 'How much of your compliance work is automated?',
            'risk_management': 'How do you identify and manage compliance risks?',
            'audit_readiness': 'How prepared are you for regulatory audits?',
            'incident_response': 'How quickly can you respond to data incidents?',
            'training_program': 'How comprehensive is your compliance training?',
            'continuous_improvement': 'How systematically do you improve compliance?'
        }
    
    def run_assessment(self):
        """Interactive assessment that determines maturity level"""
        print("🎯 CDSI Compliance Maturity Assessment")
        print("=" * 50)
        print("Answer each question on a scale of 1-5:")
        print("1 = Not at all  2 = Minimal  3 = Some  4 = Good  5 = Excellent\n")
        
        scores = {}
        for area, question in self.assessment_areas.items():
            while True:
                try:
                    score = int(input(f"{question} (1-5): "))
                    if 1 <= score <= 5:
                        scores[area] = score
                        break
                    else:
                        print("Please enter a number between 1 and 5.")
                except ValueError:
                    print("Please enter a valid number.")
        
        return self.calculate_maturity_level(scores)
    
    def calculate_maturity_level(self, scores):
        """Calculate overall maturity level and recommendations"""
        average_score = sum(scores.values()) / len(scores)
        
        if average_score < 2.0:
            level = "COMPLIANCE AWARE"
            description = "Getting real about compliance - time to understand what you're working with"
            next_level = "COMPLIANCE BUILDER"
            priority_actions = [
                "Complete data discovery and mapping",
                "Document basic compliance processes", 
                "Implement emergency incident response plan"
            ]
        elif average_score < 3.0:
            level = "COMPLIANCE BUILDER"
            description = "Not winging it anymore - building systematic processes"
            next_level = "COMPLIANCE MANAGER"
            priority_actions = [
                "Automate routine compliance tasks",
                "Integrate compliance into business workflows",
                "Implement compliance monitoring systems"
            ]
        elif average_score < 4.0:
            level = "COMPLIANCE MANAGER"
            description = "Making compliance look professional and systematic"
            next_level = "COMPLIANCE ENGINEER"
            priority_actions = [
                "Implement predictive compliance analytics",
                "Optimize compliance process efficiency",
                "Build advanced reporting capabilities"
            ]
        elif average_score < 4.5:
            level = "COMPLIANCE ENGINEER"
            description = "Optimizing compliance systems for peak performance"
            next_level = "COMPLIANCE MASTER"
            priority_actions = [
                "Implement AI-enhanced compliance monitoring",
                "Build industry-leading compliance innovation",
                "Develop strategic compliance planning systems"
            ]
        else:
            level = "COMPLIANCE MASTER"
            description = "Setting industry standards that others follow"
            next_level = "Continue Innovation"
            priority_actions = [
                "Share expertise through thought leadership",
                "Mentor other organizations",
                "Drive industry compliance innovation"
            ]
        
        return {
            'current_level': level,
            'description': description,
            'average_score': round(average_score, 1),
            'next_level': next_level,
            'priority_actions': priority_actions,
            'area_scores': scores,
            'weak_areas': [area for area, score in scores.items() if score < average_score],
            'strong_areas': [area for area, score in scores.items() if score >= average_score]
        }
    
    def generate_report(self, results):
        """Generate detailed maturity assessment report"""
        print(f"\n🎯 CDSI MATURITY ASSESSMENT RESULTS")
        print("=" * 50)
        print(f"Current Level: {results['current_level']}")
        print(f"Description: {results['description']}")
        print(f"Overall Score: {results['average_score']}/5.0")
        print(f"Next Level: {results['next_level']}")
        
        print(f"\n🚀 PRIORITY ACTIONS TO REACH {results['next_level']}:")
        for i, action in enumerate(results['priority_actions'], 1):
            print(f"  {i}. {action}")
        
        print(f"\n📊 AREA BREAKDOWN:")
        for area, score in results['area_scores'].items():
            status = "💪" if area in results['strong_areas'] else "⚠️"
            print(f"  {status} {area.replace('_', ' ').title()}: {score}/5")
        
        print(f"\n📧 Next Steps:")
        print(f"Visit getcdsi.com for tools to advance to {results['next_level']}")
        print(f"Contact: consulting@getcdsi.com for implementation consulting")
        
        return results

if __name__ == "__main__":
    assessment = CDSIMaturityAssessment()
    results = assessment.run_assessment()
    assessment.generate_report(results)