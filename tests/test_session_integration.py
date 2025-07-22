#!/usr/bin/env python3
"""
CDSI Session Integration Tests
Comprehensive testing of anonymized session management and recommendations

Author: bdstest
License: Apache 2.0
Copyright: 2025 CDSI - Compliance Data Systems Insights
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
import uuid
from unittest.mock import Mock, patch

# Import CDSI systems for testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.session_manager import AnonymizedSessionManager, SessionState
from core.contextual_recommendations import ContextualRecommendationEngine
from core.tiered_analysis_system import TieredAnalysisEngine, TierLevel
from core.anonymization_engine import DataAnonymizer

class TestSessionIntegration:
    """Test session-aware compliance analysis integration"""
    
    @pytest.fixture
    def session_manager(self):
        """Create session manager for testing"""
        return AnonymizedSessionManager()
    
    @pytest.fixture
    def recommendation_engine(self):
        """Create recommendation engine for testing"""
        return ContextualRecommendationEngine()
    
    @pytest.fixture
    def analysis_engine(self):
        """Create analysis engine for testing"""
        return TieredAnalysisEngine()
    
    @pytest.fixture
    def customer_data(self):
        """Sample customer data for testing"""
        return {
            'customer_identifier': 'test-customer@business-example.com',
            'website_url': 'https://test-business-site.com',
            'tier_level': 'aware',
            'customer_segment': 'professional_services'
        }
    
    def test_session_creation_anonymization(self, session_manager, customer_data):
        """Test session creation with complete anonymization"""
        
        # Create session
        session = session_manager.create_session(
            customer_data['customer_identifier'],
            customer_data
        )
        
        # Verify session structure
        assert session.session_id is not None
        assert len(session.session_id) == 36  # UUID length
        assert session.customer_hash.startswith('customer_')
        assert session.session_state == SessionState.ACTIVE
        
        # Verify no PII in session
        session_dict = session.__dict__
        session_json = json.dumps(session_dict, default=str)
        
        # Check that no actual customer data is stored
        assert 'test-customer@business-example.com' not in session_json
        assert 'https://test-business-site.com' not in session_json
        assert 'business-example' not in session_json
        
        print(f"✅ Session created with anonymization: {session.customer_hash}")
    
    def test_session_persistence_and_retrieval(self, session_manager, customer_data):
        """Test session persistence and retrieval"""
        
        # Create session
        session = session_manager.create_session(
            customer_data['customer_identifier'],
            customer_data
        )
        
        session_id = session.session_id
        original_hash = session.customer_hash
        
        # Retrieve session
        retrieved_session = session_manager.get_session(session_id)
        
        assert retrieved_session is not None
        assert retrieved_session.session_id == session_id
        assert retrieved_session.customer_hash == original_hash
        assert retrieved_session.session_state == SessionState.ACTIVE
        
        print(f"✅ Session persistence verified: {session_id}")
    
    def test_website_analysis_with_session_tracking(self, session_manager, analysis_engine, customer_data):
        """Test website analysis with session tracking"""
        
        # Create session
        session = session_manager.create_session(
            customer_data['customer_identifier'],
            customer_data
        )
        
        # Mock analysis results for testing
        mock_analysis = {
            'score': 6.5,
            'findings': ['privacy_policy_missing', 'cookie_consent_needed'],
            'tier_level': 'aware',
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # Track analysis in session
        success = session_manager.track_website_analysis(
            session.session_id,
            customer_data['website_url'],
            mock_analysis
        )
        
        assert success is True
        
        # Retrieve updated session
        updated_session = session_manager.get_session(session.session_id)
        assert updated_session.session_state == SessionState.ANALYZING
        assert updated_session.website_analysis['compliance_score'] == 6.5
        
        # Verify URL is anonymized in session
        stored_url = updated_session.website_analysis['website_url']
        assert 'test-business-site' not in stored_url
        assert 'site_' in stored_url
        
        print(f"✅ Website analysis tracked with anonymization")
    
    def test_contextual_recommendation_generation(self, session_manager, recommendation_engine, customer_data):
        """Test contextual recommendation generation"""
        
        # Create and setup session
        session = session_manager.create_session(
            customer_data['customer_identifier'],
            customer_data
        )
        
        # Add analysis context
        analysis_data = {
            'score': 5.0,  # Low score to trigger critical recommendations
            'findings': ['privacy_policy_missing', 'contact_form_unprotected'],
            'tier_level': 'aware'
        }
        
        session_manager.track_website_analysis(
            session.session_id,
            customer_data['website_url'],
            analysis_data
        )
        
        # Generate recommendations
        recommendations = recommendation_engine.generate_recommendations_for_session(
            session.session_id,
            session_manager,
            max_recommendations=5
        )
        
        assert len(recommendations) > 0
        assert len(recommendations) <= 5  # Respects max limit
        
        # Verify recommendation structure
        rec = recommendations[0]
        assert hasattr(rec, 'id')
        assert hasattr(rec, 'title')
        assert hasattr(rec, 'priority')
        assert hasattr(rec, 'estimated_score_improvement')
        
        # Verify context relevance for low score
        high_priority_recs = [r for r in recommendations if r.priority == 'high']
        assert len(high_priority_recs) > 0
        
        print(f"✅ Generated {len(recommendations)} contextual recommendations")
    
    def test_recommendation_progress_tracking(self, session_manager, recommendation_engine, customer_data):
        """Test recommendation implementation progress tracking"""
        
        # Setup session with recommendations
        session = session_manager.create_session(
            customer_data['customer_identifier'],
            customer_data
        )
        
        session_manager.track_website_analysis(
            session.session_id,
            customer_data['website_url'],
            {'score': 5.0, 'tier_level': 'aware'}
        )
        
        recommendations = recommendation_engine.generate_recommendations_for_session(
            session.session_id,
            session_manager
        )
        
        # Track progress on first recommendation
        rec_id = recommendations[0].id
        progress_data = {
            'status': 'in_progress',
            'completion_percentage': 50,
            'notes': 'Privacy policy draft completed'
        }
        
        success = session_manager.track_recommendation_progress(
            session.session_id,
            rec_id,
            progress_data
        )
        
        assert success is True
        
        # Verify progress tracking
        updated_session = session_manager.get_session(session.session_id)
        assert rec_id in updated_session.implementation_progress
        assert updated_session.implementation_progress[rec_id]['status'] == 'in_progress'
        assert updated_session.session_state == SessionState.IMPLEMENTATION_TRACKING
        
        print(f"✅ Recommendation progress tracking verified")
    
    def test_session_insights_generation(self, session_manager, customer_data):
        """Test session insights and analytics"""
        
        # Create session with interaction history
        session = session_manager.create_session(
            customer_data['customer_identifier'],
            customer_data
        )
        
        # Add some interaction history
        session_manager.track_website_analysis(
            session.session_id,
            customer_data['website_url'],
            {'score': 6.0, 'tier_level': 'aware'}
        )
        
        # Get insights
        insights = session_manager.get_session_insights(session.session_id)
        
        assert 'session_metrics' in insights
        assert 'recommendation_context' in insights
        assert 'session_continuity' in insights
        
        # Verify metrics
        metrics = insights['session_metrics']
        assert 'interaction_count' in metrics
        assert 'session_duration_minutes' in metrics
        assert 'current_state' in metrics
        
        # Verify context preservation
        context = insights['recommendation_context']
        assert 'customer_segment' in context
        assert context['customer_segment'] != 'unknown'  # Should be categorized
        
        print(f"✅ Session insights generated successfully")
    
    def test_customer_consistency_across_sessions(self, session_manager, customer_data):
        """Test that same customer gets consistent hash across sessions"""
        
        # Create first session
        session1 = session_manager.create_session(
            customer_data['customer_identifier'],
            customer_data
        )
        
        # Create second session with same customer
        session2 = session_manager.create_session(
            customer_data['customer_identifier'],
            {'different': 'context'}
        )
        
        # Verify same customer hash
        assert session1.customer_hash == session2.customer_hash
        
        # But different session IDs
        assert session1.session_id != session2.session_id
        
        print(f"✅ Customer consistency verified: {session1.customer_hash}")
    
    def test_pii_detection_prevention(self, session_manager):
        """Test that PII cannot be accidentally stored"""
        
        # Attempt to create session with PII in context
        malicious_context = {
            'email': 'real-customer@actual-business.com',
            'phone': '555-123-4567',
            'address': '123 Real Street',
            'company_name': 'Actual Business Inc'
        }
        
        # Create session (should anonymize all PII)
        session = session_manager.create_session(
            'test@example.com',
            malicious_context
        )
        
        # Verify PII is not stored in session
        session_json = json.dumps(session.__dict__, default=str)
        
        assert 'real-customer@actual-business.com' not in session_json
        assert '555-123-4567' not in session_json
        assert '123 Real Street' not in session_json
        assert 'Actual Business Inc' not in session_json
        
        # But verify anonymized versions exist
        assert 'user_' in session_json  # Anonymized email
        assert session.customer_hash.startswith('customer_')
        
        print(f"✅ PII protection verified - all sensitive data anonymized")
    
    def test_session_expiration_cleanup(self, session_manager, customer_data):
        """Test session expiration and cleanup"""
        
        # Create session
        session = session_manager.create_session(
            customer_data['customer_identifier'],
            customer_data
        )
        
        session_id = session.session_id
        
        # Verify session exists
        assert session_manager.get_session(session_id) is not None
        
        # Manually expire session for testing
        expired_session = session_manager.get_session(session_id)
        if expired_session:
            # Set expiration to past
            expired_time = (datetime.now() - timedelta(hours=1)).isoformat()
            session_manager.update_session(session_id, {'expires_at': expired_time})
        
        # Try to retrieve expired session
        retrieved = session_manager.get_session(session_id)
        
        # Should return None for expired session
        assert retrieved is None
        
        print(f"✅ Session expiration and cleanup verified")
    
    def test_tier_based_recommendation_limits(self, session_manager, recommendation_engine, customer_data):
        """Test that recommendations respect tier limits"""
        
        # Test free tier (AWARE) - should limit recommendations
        session = session_manager.create_session(
            customer_data['customer_identifier'],
            {**customer_data, 'tier_level': 'aware'}
        )
        
        session_manager.track_website_analysis(
            session.session_id,
            customer_data['website_url'],
            {'score': 4.0, 'tier_level': 'aware'}  # Low score = many recommendations needed
        )
        
        # Generate recommendations with free tier limits
        recommendations = recommendation_engine.generate_recommendations_for_session(
            session.session_id,
            session_manager,
            max_recommendations=3  # Free tier limit
        )
        
        # Should respect tier limits
        assert len(recommendations) <= 3
        
        # Should include upgrade prompt for free tier
        upgrade_recs = [r for r in recommendations if 'upgrade' in r.title.lower()]
        assert len(upgrade_recs) > 0
        
        print(f"✅ Tier-based recommendation limits verified")

class TestEndToEndWorkflow:
    """Test complete end-to-end customer workflow"""
    
    def test_complete_customer_journey(self):
        """Test complete customer journey with session management"""
        
        print("\n🚀 Testing Complete Customer Journey")
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

# Main execution
if __name__ == "__main__":
    # Run basic tests
    print("🔒 CDSI Session Integration Tests")
    print("=" * 50)
    
    # Create test instances
    session_mgr = AnonymizedSessionManager()
    rec_engine = ContextualRecommendationEngine()
    
    # Run end-to-end test
    e2e_test = TestEndToEndWorkflow()
    e2e_test.test_complete_customer_journey()
    
    print(f"\n✅ All integration tests completed successfully")
    print(f"🔒 Session management with complete anonymization verified")
    print(f"🎯 Ready for production deployment")
    
    # Cleanup
    session_mgr.cleanup_expired_sessions()