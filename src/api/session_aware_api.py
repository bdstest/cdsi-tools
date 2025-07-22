#!/usr/bin/env python3
"""
CDSI Session-Aware API - Complete Integration
FastAPI endpoints with session management and contextual recommendations

Author: bdstest
License: Apache 2.0
Copyright: 2025 CDSI - Compliance Data Systems Insights
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime

# Import CDSI core systems
try:
    from ..core.tiered_analysis_system import TieredAnalysisEngine, TierLevel
    from ..core.session_manager import AnonymizedSessionManager
    from ..core.contextual_recommendations import ContextualRecommendationEngine
    from ..core.anonymization_engine import AnonymizedLogger
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from core.tiered_analysis_system import TieredAnalysisEngine, TierLevel
    from core.session_manager import AnonymizedSessionManager
    from core.contextual_recommendations import ContextualRecommendationEngine
    from core.anonymization_engine import AnonymizedLogger

# Initialize CDSI systems
analysis_engine = TieredAnalysisEngine()
session_manager = AnonymizedSessionManager()
recommendation_engine = ContextualRecommendationEngine()
logger = AnonymizedLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="CDSI Compliance Analysis API",
    description="Privacy-first compliance analysis with session-aware recommendations",
    version="1.0.0",
    contact={
        "name": "bdstest",
        "email": "consulting@getcdsi.com"
    }
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class AnalysisRequest(BaseModel):
    website_url: str = Field(..., description="Website URL to analyze")
    customer_identifier: str = Field(..., description="Customer identifier (gets anonymized)")
    tier_level: str = Field(default="aware", description="Analysis tier level")
    session_id: Optional[str] = Field(None, description="Existing session ID")

class SessionResponse(BaseModel):
    session_id: str
    customer_hash: str
    session_state: str
    analysis_score: Optional[float] = None
    recommendations_count: int = 0

class RecommendationRequest(BaseModel):
    session_id: str = Field(..., description="Active session ID")
    max_recommendations: Optional[int] = Field(None, description="Maximum recommendations to return")

class ProgressUpdate(BaseModel):
    session_id: str = Field(..., description="Active session ID")
    recommendation_id: str = Field(..., description="Recommendation being tracked")
    status: str = Field(..., description="Progress status")
    completion_percentage: Optional[int] = Field(None, description="Completion percentage")
    notes: Optional[str] = Field(None, description="Progress notes")

# API Endpoints

@app.post("/api/v1/analysis/start", response_model=SessionResponse)
async def start_analysis_session(request: AnalysisRequest):
    """Start new compliance analysis session with anonymization"""
    
    try:
        # Create or retrieve session
        if request.session_id:
            session = session_manager.get_session(request.session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found or expired")
        else:
            # Create new session
            initial_context = {
                'website_url': request.website_url,
                'tier_level': request.tier_level,
                'customer_identifier': request.customer_identifier
            }
            session = session_manager.create_session(
                request.customer_identifier,
                initial_context
            )
        
        # Convert tier level
        try:
            tier = TierLevel[request.tier_level.upper()]
        except KeyError:
            tier = TierLevel.AWARE
        
        # Run analysis with session tracking
        analysis_result = analysis_engine.analyze_website(
            request.website_url,
            tier,
            user_id=request.customer_identifier,
            session_id=session.session_id
        )
        
        logger.log_customer_interaction(
            'info',
            'Analysis session started',
            {
                'session_id': session.session_id,
                'tier_level': request.tier_level,
                'compliance_score': analysis_result.current_score
            }
        )
        
        return SessionResponse(
            session_id=session.session_id,
            customer_hash=session.customer_hash,
            session_state=session.session_state.value,
            analysis_score=analysis_result.current_score,
            recommendations_count=0  # Will be generated separately
        )
        
    except Exception as e:
        logger.log_customer_interaction('error', f'Analysis failed: {str(e)}', request.dict())
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/v1/recommendations/generate")
async def generate_recommendations(request: RecommendationRequest):
    """Generate contextual recommendations for session"""
    
    try:
        # Validate session exists
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Generate contextual recommendations
        recommendations = recommendation_engine.generate_recommendations_for_session(
            request.session_id,
            session_manager,
            max_recommendations=request.max_recommendations
        )
        
        logger.log_customer_interaction(
            'info',
            f'Generated {len(recommendations)} recommendations',
            {'session_id': request.session_id}
        )
        
        return {
            "session_id": request.session_id,
            "recommendations": [
                {
                    "id": rec.id,
                    "title": rec.title,
                    "description": rec.description,
                    "priority": rec.priority,
                    "estimated_impact": rec.estimated_score_improvement,
                    "implementation_time": rec.implementation_time,
                    "cost_estimate": rec.cost_estimate,
                    "context_relevance": rec.context_relevance,
                    "implementation_steps": rec.implementation_steps
                }
                for rec in recommendations
            ],
            "total_recommendations": len(recommendations),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.log_customer_interaction('error', f'Recommendation generation failed: {str(e)}', request.dict())
        raise HTTPException(status_code=500, detail=f"Recommendation generation failed: {str(e)}")

@app.post("/api/v1/recommendations/progress")
async def update_recommendation_progress(request: ProgressUpdate):
    """Update progress on recommendation implementation"""
    
    try:
        # Track progress in session
        progress_data = {
            'status': request.status,
            'completion_percentage': request.completion_percentage,
            'notes': request.notes,
            'updated_at': datetime.now().isoformat()
        }
        
        success = session_manager.track_recommendation_progress(
            request.session_id,
            request.recommendation_id,
            progress_data
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Track feedback for learning
        recommendation_engine.track_recommendation_feedback(
            request.session_id,
            request.recommendation_id,
            {
                'type': 'progress_update',
                'status': request.status,
                'completion': request.completion_percentage
            }
        )
        
        logger.log_customer_interaction(
            'info',
            'Recommendation progress updated',
            {
                'session_id': request.session_id,
                'recommendation_id': request.recommendation_id,
                'status': request.status
            }
        )
        
        return {
            "success": True,
            "session_id": request.session_id,
            "recommendation_id": request.recommendation_id,
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.log_customer_interaction('error', f'Progress update failed: {str(e)}', request.dict())
        raise HTTPException(status_code=500, detail=f"Progress update failed: {str(e)}")

@app.get("/api/v1/session/{session_id}/insights")
async def get_session_insights(session_id: str):
    """Get comprehensive session insights and context"""
    
    try:
        insights = session_manager.get_session_insights(session_id)
        
        if not insights:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        logger.log_customer_interaction(
            'info',
            'Session insights retrieved',
            {'session_id': session_id}
        )
        
        return {
            "session_id": session_id,
            "insights": insights,
            "retrieved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.log_customer_interaction('error', f'Insights retrieval failed: {str(e)}', {'session_id': session_id})
        raise HTTPException(status_code=500, detail=f"Insights retrieval failed: {str(e)}")

@app.get("/api/v1/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get current session status"""
    
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        return {
            "session_id": session_id,
            "customer_hash": session.customer_hash,
            "session_state": session.session_state.value,
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "expires_at": session.expires_at,
            "interaction_count": len(session.interaction_history),
            "recommendations_generated": len(session.recommendations_generated),
            "implementations_tracked": len(session.implementation_progress)
        }
        
    except Exception as e:
        logger.log_customer_interaction('error', f'Status retrieval failed: {str(e)}', {'session_id': session_id})
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")

@app.delete("/api/v1/session/{session_id}")
async def end_session(session_id: str):
    """End and cleanup session"""
    
    try:
        session = session_manager.get_session(session_id)
        if session:
            # Mark session as completed
            session_manager.update_session(session_id, {'session_state': 'completed'})
            
            logger.log_customer_interaction(
                'info',
                'Session ended by request',
                {'session_id': session_id}
            )
        
        return {
            "success": True,
            "session_id": session_id,
            "ended_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.log_customer_interaction('error', f'Session end failed: {str(e)}', {'session_id': session_id})
        raise HTTPException(status_code=500, detail=f"Session end failed: {str(e)}")

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CDSI Compliance API",
        "version": "1.0.0",
        "author": "bdstest",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "anonymized_session_management",
            "contextual_recommendations", 
            "tiered_analysis",
            "privacy_by_design"
        ]
    }

@app.get("/api/v1/system/stats")
async def get_system_stats():
    """Get anonymized system statistics"""
    
    try:
        # Get anonymized analytics
        analytics = analysis_engine.get_tier_analytics()
        
        return {
            "system_performance": analytics.get('system_performance', {}),
            "tier_statistics": analytics.get('tier_statistics', {}),
            "total_analyses": analytics.get('total_analyses', 0),
            "upgrade_opportunities": analytics.get('upgrade_opportunities', 0),
            "data_protection": {
                "pii_storage": "none",
                "anonymization": "active",
                "session_security": "enterprise_grade"
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.log_customer_interaction('error', f'Stats retrieval failed: {str(e)}', {})
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize CDSI systems on startup"""
    logger.log_customer_interaction(
        'info',
        'CDSI API service started',
        {
            'version': '1.0.0',
            'features': ['session_management', 'contextual_recommendations', 'anonymization']
        }
    )

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Cleanup expired sessions
    session_manager.cleanup_expired_sessions()
    
    logger.log_customer_interaction(
        'info',
        'CDSI API service stopped',
        {'cleanup_completed': True}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=False  # Disable access logs to prevent PII logging
    )