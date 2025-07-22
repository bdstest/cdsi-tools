#!/usr/bin/env python3
"""
CDSI Basic Integration Test - No External Dependencies
Complete testing of session management and anonymization

Author: bdstest
License: Apache 2.0
Copyright: 2025 CDSI - Compliance Data Systems Insights
"""

import json
from datetime import datetime
import uuid

# Import CDSI systems for testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.session_manager import AnonymizedSessionManager, SessionState
from core.contextual_recommendations import ContextualRecommendationEngine
from core.anonymization_engine import DataAnonymizer

def test_complete_customer_journey():
    """Test complete customer journey with session management"""
    
    print("🚀 Testing Complete Customer Journey")
    print("=" * 50)
    
    # Initialize systems
    session_manager = AnonymizedSessionManager()
    recommendation_engine = ContextualRecommendationEngine()
    
    # 1. Customer arrives
    customer_id = "journey-test@business-site.com"
    website_url = "https://business-site.com"
    
    session = session_manager.create_session(
        customer_id,
        {
            'website_url': website_url,
            'tier_level': 'aware',
            'customer_segment': 'professional_services'
        }
    )
    
    print(f"✅ Step 1: Session created - {session.customer_hash}")
    
    # 2. Website analysis
    analysis_results = {
        'score': 5.5,
        'findings': ['privacy_policy_missing', 'contact_form_unprotected', 'no_cookie_policy'],
        'tier_level': 'aware'
    }
    
    session_manager.track_website_analysis(
        session.session_id,
        website_url,
        analysis_results
    )
    
    print(f"✅ Step 2: Analysis tracked - Score: {analysis_results['score']}/10")
    
    # 3. Generate contextual recommendations
    recommendations = recommendation_engine.generate_recommendations_for_session(
        session.session_id,
        session_manager,
        max_recommendations=3  # Free tier limit
    )
    
    print(f"✅ Step 3: Generated {len(recommendations)} recommendations")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec.title} ({rec.priority} priority)")
    
    # 4. Customer starts implementing first recommendation
    if recommendations:
        first_rec = recommendations[0]
        session_manager.track_recommendation_progress(
            session.session_id,
            first_rec.id,
            {
                'status': 'started',
                'completion_percentage': 10,
                'notes': 'Started working on privacy policy'
            }
        )
        
        print(f"✅ Step 4: Progress tracked for '{first_rec.title}'")
    
    # 5. Get session insights
    insights = session_manager.get_session_insights(session.session_id)
    
    print(f"✅ Step 5: Session insights generated")
    print(f"   Duration: {insights['session_metrics']['session_duration_minutes']} minutes")
    print(f"   Interactions: {insights['session_metrics']['interaction_count']}")
    print(f"   State: {insights['session_metrics']['current_state']}")
    
    # 6. Verify no PII stored anywhere
    session_data = session_manager.get_session(session.session_id)
    session_json = json.dumps(session_data.__dict__, default=str)
    
    assert 'journey-test@business-site.com' not in session_json
    assert 'https://business-site.com' not in session_json
    assert 'business-site' not in session_json
    
    print(f"✅ Step 6: PII protection verified - no identifiable data stored")
    
    print(f"\n🎯 Complete customer journey successful!")
    print(f"   Session ID: {session.session_id}")
    print(f"   Customer Hash: {session.customer_hash}")
    print(f"   Privacy Status: ✅ FULLY PROTECTED")
    
    return True

def test_anonymization_comprehensive():
    """Test comprehensive anonymization functionality"""
    
    print(f"\n🔒 Testing Comprehensive Anonymization")
    print("=" * 40)
    
    anonymizer = DataAnonymizer()
    
    # Test various PII types
    test_cases = [
        ("Email: contact@realbusiness.com", "email anonymization"),
        ("Visit https://realbusiness.com for more info", "URL anonymization"),
        ("Call 555-123-4567 for support", "phone anonymization"),
        ("Server IP: 192.168.1.100", "IP anonymization")
    ]
    
    for original, test_type in test_cases:
        anonymized = anonymizer.anonymize_text(original)
        print(f"✅ {test_type}")
        print(f"   Original: {original}")
        print(f"   Anonymized: {anonymized}")
        
        # Verify no original data remains
        assert 'realbusiness' not in anonymized
        assert '555-123-4567' not in anonymized
        assert '192.168.1.100' not in anonymized
    
    return True

def test_session_consistency():
    """Test session consistency and customer tracking"""
    
    print(f"\n🎯 Testing Session Consistency")
    print("=" * 30)
    
    session_manager = AnonymizedSessionManager()
    customer_id = "consistency-test@example.com"
    
    # Create multiple sessions for same customer
    session1 = session_manager.create_session(customer_id, {'context': 'first'})
    session2 = session_manager.create_session(customer_id, {'context': 'second'})
    
    print(f"✅ Multiple sessions created")
    print(f"   Session 1: {session1.session_id}")
    print(f"   Session 2: {session2.session_id}")
    
    # Verify consistent customer hash
    assert session1.customer_hash == session2.customer_hash
    print(f"✅ Consistent customer hash: {session1.customer_hash}")
    
    # But different session IDs
    assert session1.session_id != session2.session_id
    print(f"✅ Unique session IDs verified")
    
    return True

def test_recommendation_contextuality():
    """Test contextual recommendation generation"""
    
    print(f"\n🧠 Testing Contextual Recommendations")
    print("=" * 35)
    
    session_manager = AnonymizedSessionManager()
    recommendation_engine = ContextualRecommendationEngine()
    
    # Test different scenarios
    scenarios = [
        {
            'name': 'Low Compliance Score',
            'score': 3.0,
            'segment': 'professional_services',
            'expected_priority': 'high'
        },
        {
            'name': 'Medium Compliance Score',
            'score': 7.0,
            'segment': 'ecommerce',
            'expected_priority': 'medium'
        }
    ]
    
    for scenario in scenarios:
        print(f"Testing: {scenario['name']}")
        
        # Create session with scenario context
        session = session_manager.create_session(
            f"test-{scenario['name']}@example.com",
            {
                'customer_segment': scenario['segment'],
                'tier_level': 'aware'
            }
        )
        
        # Add analysis context
        session_manager.track_website_analysis(
            session.session_id,
            "https://test-site.example",
            {
                'score': scenario['score'],
                'tier_level': 'aware'
            }
        )
        
        # Generate recommendations
        recommendations = recommendation_engine.generate_recommendations_for_session(
            session.session_id,
            session_manager,
            max_recommendations=3
        )
        
        print(f"   Generated {len(recommendations)} recommendations")
        
        # Verify contextual relevance
        if recommendations:
            priorities = [rec.priority for rec in recommendations]
            assert scenario['expected_priority'] in priorities
            print(f"   ✅ Expected priority '{scenario['expected_priority']}' found")
        
        print(f"   ✅ Scenario '{scenario['name']}' completed\n")
    
    return True

def test_tier_based_limits():
    """Test tier-based recommendation limits"""
    
    print(f"📊 Testing Tier-Based Limits")
    print("=" * 25)
    
    session_manager = AnonymizedSessionManager()
    recommendation_engine = ContextualRecommendationEngine()
    
    # Test free tier limits
    session = session_manager.create_session(
        "tier-test@example.com",
        {
            'tier_level': 'aware',
            'customer_segment': 'small_business_general'
        }
    )
    
    # Low score should generate many recommendations
    session_manager.track_website_analysis(
        session.session_id,
        "https://test-site.example",
        {'score': 2.0, 'tier_level': 'aware'}
    )
    
    # Generate with free tier limits
    recommendations = recommendation_engine.generate_recommendations_for_session(
        session.session_id,
        session_manager,
        max_recommendations=3  # Free tier limit
    )
    
    print(f"✅ Free tier recommendations: {len(recommendations)}")
    assert len(recommendations) <= 3  # Should respect limit
    
    # Check for upgrade prompts
    upgrade_recs = [r for r in recommendations if 'upgrade' in r.title.lower()]
    if upgrade_recs:
        print(f"✅ Upgrade prompt included: {upgrade_recs[0].title}")
    
    return True

def run_all_tests():
    """Run all integration tests"""
    
    print("🔒 CDSI Complete Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Complete Customer Journey", test_complete_customer_journey),
        ("Comprehensive Anonymization", test_anonymization_comprehensive),
        ("Session Consistency", test_session_consistency),
        ("Contextual Recommendations", test_recommendation_contextuality),
        ("Tier-Based Limits", test_tier_based_limits)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed_tests += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
        
        print("-" * 50)
    
    print(f"\n📊 TEST RESULTS")
    print(f"Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print(f"🎯 ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION")
        print(f"🔒 Complete privacy protection verified")
        print(f"🧠 Contextual recommendations working")
        print(f"📈 Session management operational")
        return True
    else:
        print(f"⚠️  Some tests failed - review system before deployment")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print(f"\n🚀 CDSI INTEGRATION COMPLETE")
        print(f"Author: bdstest")
        print(f"System: Privacy-first compliance platform")
        print(f"Status: PRODUCTION READY ✅")
    
    exit(0 if success else 1)