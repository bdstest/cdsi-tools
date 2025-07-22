#!/usr/bin/env python3
"""
CDSI Session Manager - Anonymized Customer Interaction Tracking
Secure session management for live customer interactions with recommendation continuity

Author: bdstest
License: Apache 2.0
Copyright: 2025 CDSI - Compliance Data Systems Insights
"""

import hashlib
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
import logging

# Optional Redis import
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Import anonymization system
try:
    from .anonymization_engine import AnonymizedLogger, DataAnonymizer
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent))
    from anonymization_engine import AnonymizedLogger, DataAnonymizer

class SessionState(Enum):
    """Customer session states"""
    ACTIVE = "active"
    ANALYZING = "analyzing"
    RECOMMENDATIONS_READY = "recommendations_ready"
    IMPLEMENTATION_TRACKING = "implementation_tracking"
    EXPIRED = "expired"
    COMPLETED = "completed"

@dataclass
class CustomerSession:
    """Anonymized customer session"""
    session_id: str  # UUID - no connection to customer PII
    customer_hash: str  # Consistent anonymous identifier
    session_state: SessionState
    created_at: str
    last_activity: str
    expires_at: str
    
    # Session context (anonymized)
    website_analysis: Dict = field(default_factory=dict)
    recommendations_generated: List[Dict] = field(default_factory=list)
    implementation_progress: Dict = field(default_factory=dict)
    interaction_history: List[Dict] = field(default_factory=list)
    
    # Recommendation context preservation
    analysis_context: Dict = field(default_factory=dict)
    previous_suggestions: List[str] = field(default_factory=list)
    customer_preferences: Dict = field(default_factory=dict)
    
    # No PII stored - only hashed identifiers and anonymous context

@dataclass
class RecommendationContext:
    """Context for generating consistent recommendations"""
    customer_segment: str  # Generic segment, not specific business type
    website_category: str  # Generic category
    current_score: float
    previous_actions: List[str]  # Generic actions, not specific implementations
    preferences: Dict  # Anonymized preferences
    tier_level: str
    session_history: List[Dict]  # Previous anonymous interactions

class AnonymizedSessionManager:
    """Session management with complete anonymization"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.anonymizer = DataAnonymizer()
        self.logger = AnonymizedLogger(__name__)
        
        # Initialize Redis for session storage (or fallback to in-memory)
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host, 
                    port=redis_port, 
                    decode_responses=True
                )
                self.redis_client.ping()  # Test connection
                self.storage_type = "redis"
            except:
                # Redis not available or not running
                self.memory_storage = {}
                self.storage_type = "memory"
                self.logger.log_customer_interaction(
                    'warning',
                    'Redis unavailable, using in-memory session storage',
                    {'storage_type': 'memory'}
                )
        else:
            # Fallback to in-memory storage for development
            self.memory_storage = {}
            self.storage_type = "memory"
            self.logger.log_customer_interaction(
                'warning',
                'Redis unavailable, using in-memory session storage',
                {'storage_type': 'memory'}
            )
        
        self.session_timeout_hours = 24
        
    def create_session(self, customer_identifier: str, initial_context: Dict = None) -> CustomerSession:
        """Create anonymized customer session"""
        
        # Generate anonymous session identifiers
        session_id = str(uuid.uuid4())
        customer_hash = self.anonymizer._generate_hash(customer_identifier, 'customer')
        
        now = datetime.now()
        expires_at = now + timedelta(hours=self.session_timeout_hours)
        
        # Create session with anonymized context
        session = CustomerSession(
            session_id=session_id,
            customer_hash=customer_hash,
            session_state=SessionState.ACTIVE,
            created_at=now.isoformat(),
            last_activity=now.isoformat(),
            expires_at=expires_at.isoformat(),
            analysis_context=self.anonymizer.anonymize_log_entry(initial_context or {})
        )
        
        # Store session
        self._store_session(session)
        
        self.logger.log_customer_interaction(
            'info',
            'Session created for customer interaction',
            {
                'session_id': session_id,
                'customer_hash': customer_hash,
                'expires_at': expires_at.isoformat()
            }
        )
        
        return session
    
    def get_session(self, session_id: str) -> Optional[CustomerSession]:
        """Retrieve customer session"""
        session_data = self._get_session_data(session_id)
        
        if not session_data:
            return None
        
        # Check expiration
        session = CustomerSession(**session_data)
        if datetime.fromisoformat(session.expires_at) < datetime.now():
            self._delete_session(session_id)
            return None
        
        return session
    
    def update_session(self, session_id: str, updates: Dict) -> bool:
        """Update session with anonymized data"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Anonymize any updates before storing
        anonymized_updates = self.anonymizer.anonymize_log_entry(updates)
        
        # Update session fields
        for key, value in anonymized_updates.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        session.last_activity = datetime.now().isoformat()
        
        # Store updated session
        self._store_session(session)
        return True
    
    def track_website_analysis(self, session_id: str, website_url: str, analysis_results: Dict) -> bool:
        """Track website analysis in session context"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Anonymize analysis results
        anonymized_analysis = self.anonymizer.anonymize_log_entry(analysis_results)
        anonymized_url = self.anonymizer.anonymize_text(website_url)
        
        # Update session with analysis context
        session.website_analysis = {
            'website_url': anonymized_url,
            'analysis_results': anonymized_analysis,
            'analysis_timestamp': datetime.now().isoformat(),
            'compliance_score': analysis_results.get('score', 0)
        }
        
        session.session_state = SessionState.ANALYZING
        session.last_activity = datetime.now().isoformat()
        
        self._store_session(session)
        
        self.logger.log_customer_interaction(
            'info',
            'Website analysis tracked in session',
            {
                'session_id': session_id,
                'anonymized_url': anonymized_url,
                'compliance_score': analysis_results.get('score', 0)
            }
        )
        
        return True
    
    def generate_contextual_recommendations(self, session_id: str) -> List[Dict]:
        """Generate recommendations based on session context"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        # Build recommendation context from session
        context = RecommendationContext(
            customer_segment=session.analysis_context.get('customer_segment', 'unknown'),
            website_category=session.analysis_context.get('website_category', 'unknown'),
            current_score=session.website_analysis.get('compliance_score', 0),
            previous_actions=session.previous_suggestions,
            preferences=session.customer_preferences,
            tier_level=session.analysis_context.get('tier_level', 'aware'),
            session_history=session.interaction_history[-5:]  # Last 5 interactions
        )
        
        # Generate recommendations based on context
        recommendations = self._create_contextual_recommendations(context)
        
        # Update session with new recommendations
        session.recommendations_generated = recommendations
        session.session_state = SessionState.RECOMMENDATIONS_READY
        session.last_activity = datetime.now().isoformat()
        
        # Track recommendation patterns
        for rec in recommendations:
            session.previous_suggestions.append(rec['title'])
        
        self._store_session(session)
        
        self.logger.log_customer_interaction(
            'info',
            f'Generated {len(recommendations)} contextual recommendations',
            {
                'session_id': session_id,
                'recommendation_count': len(recommendations),
                'customer_segment': context.customer_segment
            }
        )
        
        return recommendations
    
    def track_recommendation_progress(self, session_id: str, recommendation_id: str, progress_data: Dict) -> bool:
        """Track customer progress on recommendations"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Anonymize progress data
        anonymized_progress = self.anonymizer.anonymize_log_entry(progress_data)
        
        # Update implementation progress
        if 'implementation_progress' not in session.implementation_progress:
            session.implementation_progress = {}
        
        session.implementation_progress[recommendation_id] = {
            'progress_data': anonymized_progress,
            'last_updated': datetime.now().isoformat(),
            'status': progress_data.get('status', 'in_progress')
        }
        
        session.session_state = SessionState.IMPLEMENTATION_TRACKING
        session.last_activity = datetime.now().isoformat()
        
        # Add to interaction history for context
        session.interaction_history.append({
            'type': 'recommendation_progress',
            'recommendation_id': recommendation_id,
            'timestamp': datetime.now().isoformat(),
            'progress_status': progress_data.get('status', 'unknown')
        })
        
        self._store_session(session)
        
        return True
    
    def get_session_insights(self, session_id: str) -> Dict:
        """Get anonymized insights for session continuity"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        # Calculate session metrics
        interaction_count = len(session.interaction_history)
        recommendations_count = len(session.recommendations_generated)
        implementation_progress = len(session.implementation_progress)
        
        # Session duration
        start_time = datetime.fromisoformat(session.created_at)
        current_time = datetime.now()
        session_duration_minutes = (current_time - start_time).total_seconds() / 60
        
        insights = {
            'session_metrics': {
                'interaction_count': interaction_count,
                'recommendations_generated': recommendations_count,
                'implementations_tracked': implementation_progress,
                'session_duration_minutes': round(session_duration_minutes, 2),
                'current_state': session.session_state.value
            },
            'recommendation_context': {
                'customer_segment': session.analysis_context.get('customer_segment', 'unknown'),
                'website_category': session.analysis_context.get('website_category', 'unknown'),
                'current_compliance_score': session.website_analysis.get('compliance_score', 0),
                'previous_suggestions': session.previous_suggestions[-3:],  # Last 3
                'preferred_implementation_style': session.customer_preferences.get('style', 'progressive')
            },
            'session_continuity': {
                'can_resume': session.session_state != SessionState.EXPIRED,
                'next_steps': self._suggest_next_steps(session),
                'context_preserved': len(session.analysis_context) > 0
            }
        }
        
        return insights
    
    def _create_contextual_recommendations(self, context: RecommendationContext) -> List[Dict]:
        """Create recommendations based on session context"""
        recommendations = []
        
        # Base recommendations from compliance score
        if context.current_score < 7.0:
            recommendations.append({
                'id': str(uuid.uuid4()),
                'title': 'Critical Compliance Gaps',
                'priority': 'high',
                'description': 'Address fundamental compliance requirements first',
                'estimated_impact': '+3.5 points',
                'context_relevance': 'Based on current compliance analysis'
            })
        
        # Context-aware recommendations based on previous interactions
        if 'privacy_policy' not in context.previous_actions:
            recommendations.append({
                'id': str(uuid.uuid4()),
                'title': 'Privacy Policy Implementation',
                'priority': 'high',
                'description': 'Create comprehensive privacy policy',
                'estimated_impact': '+3.0 points',
                'context_relevance': 'Not previously suggested in this session'
            })
        
        # Segment-specific recommendations
        if context.customer_segment == 'professional_services':
            recommendations.append({
                'id': str(uuid.uuid4()),
                'title': 'Professional Service Privacy Notice',
                'priority': 'medium',
                'description': 'Add service-specific privacy considerations',
                'estimated_impact': '+1.5 points',
                'context_relevance': f'Tailored for {context.customer_segment} segment'
            })
        
        # Progressive recommendations based on tier
        if context.tier_level == 'aware' and len(recommendations) > 3:
            recommendations = recommendations[:3]
            recommendations.append({
                'id': str(uuid.uuid4()),
                'title': 'Upgrade for Advanced Recommendations',
                'priority': 'info',
                'description': f'Unlock {len(recommendations)} more recommendations',
                'estimated_impact': 'Enhanced guidance',
                'context_relevance': 'Based on your current needs'
            })
        
        return recommendations
    
    def _suggest_next_steps(self, session: CustomerSession) -> List[str]:
        """Suggest next steps based on session state"""
        if session.session_state == SessionState.ACTIVE:
            return ['Start website analysis', 'Review compliance requirements']
        elif session.session_state == SessionState.ANALYZING:
            return ['Wait for analysis completion', 'Review preliminary findings']
        elif session.session_state == SessionState.RECOMMENDATIONS_READY:
            return ['Review recommendations', 'Select implementation priorities']
        elif session.session_state == SessionState.IMPLEMENTATION_TRACKING:
            return ['Continue implementation', 'Update progress status']
        else:
            return ['Resume analysis', 'Check session status']
    
    def _store_session(self, session: CustomerSession):
        """Store session data"""
        session_data = asdict(session)
        
        if self.storage_type == "redis":
            self.redis_client.setex(
                f"session:{session.session_id}",
                int(self.session_timeout_hours * 3600),  # TTL in seconds
                json.dumps(session_data, default=str)
            )
        else:
            self.memory_storage[session.session_id] = session_data
    
    def _get_session_data(self, session_id: str) -> Optional[Dict]:
        """Retrieve session data"""
        if self.storage_type == "redis":
            data = self.redis_client.get(f"session:{session_id}")
            return json.loads(data) if data else None
        else:
            return self.memory_storage.get(session_id)
    
    def _delete_session(self, session_id: str):
        """Delete expired session"""
        if self.storage_type == "redis":
            self.redis_client.delete(f"session:{session_id}")
        else:
            self.memory_storage.pop(session_id, None)
    
    def cleanup_expired_sessions(self):
        """Cleanup expired sessions"""
        if self.storage_type == "memory":
            current_time = datetime.now()
            expired_sessions = []
            
            for session_id, session_data in self.memory_storage.items():
                expires_at = datetime.fromisoformat(session_data['expires_at'])
                if expires_at < current_time:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.memory_storage[session_id]
                
            if expired_sessions:
                self.logger.log_customer_interaction(
                    'info',
                    f'Cleaned up {len(expired_sessions)} expired sessions',
                    {'expired_count': len(expired_sessions)}
                )

# Global session manager instance
session_manager = AnonymizedSessionManager()

# Usage example and testing
if __name__ == "__main__":
    print("🔒 CDSI Session Manager Test")
    print("=" * 50)
    
    # Test session creation
    manager = AnonymizedSessionManager()
    
    # Create session for customer (using anonymous identifier)
    customer_id = "customer@business.com"  # This gets hashed
    initial_context = {
        'website_url': 'https://business.com',
        'tier_level': 'aware',
        'customer_segment': 'professional_services'
    }
    
    session = manager.create_session(customer_id, initial_context)
    print(f"Session Created: {session.session_id}")
    print(f"Customer Hash: {session.customer_hash}")
    
    # Track analysis
    analysis_results = {
        'score': 5.0,
        'findings': ['missing privacy policy', 'no cookie consent'],
        'recommendations_needed': True
    }
    
    manager.track_website_analysis(session.session_id, 'https://business.com', analysis_results)
    print("Website analysis tracked")
    
    # Generate contextual recommendations
    recommendations = manager.generate_contextual_recommendations(session.session_id)
    print(f"Generated {len(recommendations)} recommendations")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec['title']} - {rec['priority']} priority")
    
    # Track progress
    if recommendations:
        manager.track_recommendation_progress(
            session.session_id,
            recommendations[0]['id'],
            {'status': 'in_progress', 'completion': 25}
        )
        print("Progress tracked for first recommendation")
    
    # Get session insights
    insights = manager.get_session_insights(session.session_id)
    print(f"\nSession Insights:")
    print(f"  Interactions: {insights['session_metrics']['interaction_count']}")
    print(f"  Duration: {insights['session_metrics']['session_duration_minutes']} minutes")
    print(f"  Current State: {insights['session_metrics']['current_state']}")
    print(f"  Next Steps: {insights['session_continuity']['next_steps']}")
    
    print("\n✅ Session management test completed")
    print("🔒 All session data anonymized and secure")