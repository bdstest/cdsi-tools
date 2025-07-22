#!/usr/bin/env python3
"""
CDSI Compliance API - RESTful API for Heuristics Engine

FastAPI-based REST API providing access to CDSI compliance heuristics engine
with tier-based access control, rate limiting, and comprehensive monitoring.

Features:
- Tier-based API access control
- Rate limiting and usage tracking
- Comprehensive compliance analysis endpoints
- Module management API
- Performance monitoring and statistics

Author: bdstest
License: Apache 2.0
Copyright: 2025 CDSI - Compliance Data Systems Insights
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn

from ..core.heuristics_engine import HeuristicsEngine, TierLevel, ProcessingResult, RiskLevel
from ..modules.regulatory_loader import RegulatoryModuleLoader, ModuleType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Global engine and loader instances
heuristics_engine: Optional[HeuristicsEngine] = None
module_loader: Optional[RegulatoryModuleLoader] = None
api_stats: Dict[str, Any] = {
    'total_requests': 0,
    'total_processing_time': 0.0,
    'requests_by_tier': {},
    'errors': 0
}

# Rate limiting storage (in production, use Redis)
rate_limits: Dict[str, List[float]] = {}

class ComplianceRequest(BaseModel):
    """Request model for compliance analysis"""
    content: str = Field(..., min_length=1, max_length=1000000, description="Content to analyze")
    content_id: Optional[str] = Field(None, description="Optional unique identifier for content")
    modules: Optional[List[str]] = Field(None, description="Specific modules to use for analysis")
    
    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty or whitespace only')
        return v

class ComplianceResponse(BaseModel):
    """Response model for compliance analysis"""
    content_id: str
    risk_level: str
    overall_score: float
    total_matches: int
    unique_patterns: int
    processing_time_ms: float
    categories_detected: List[str]
    tier_level: str
    matches: List[Dict[str, Any]]
    timestamp: str

class ModuleInfo(BaseModel):
    """Module information response"""
    id: str
    name: str
    module_type: str
    jurisdiction: str
    tier_level: str
    active: bool
    pattern_count: int

class StatsResponse(BaseModel):
    """Statistics response model"""
    engine_stats: Dict[str, Any]
    module_stats: Dict[str, Any]
    api_stats: Dict[str, Any]

class TierConfig(BaseModel):
    """Tier configuration model"""
    tier_level: str
    rate_limit_per_minute: int
    max_content_size: int
    available_modules: List[str]

# Startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    global heuristics_engine, module_loader
    
    # Startup
    logger.info("Starting CDSI Compliance API...")
    
    try:
        # Initialize heuristics engine
        heuristics_engine = HeuristicsEngine()
        logger.info("Heuristics engine initialized")
        
        # Initialize module loader
        module_loader = RegulatoryModuleLoader()
        logger.info("Module loader initialized")
        
        # Load default modules for free tier
        default_modules = ['us_federal', 'eu_gdpr']
        for module_id in default_modules:
            try:
                module_loader.load_module(module_id)
            except Exception as e:
                logger.warning(f"Failed to load default module {module_id}: {e}")
        
        logger.info("CDSI Compliance API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start CDSI Compliance API: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down CDSI Compliance API...")

# Create FastAPI app
app = FastAPI(
    title="CDSI Compliance API",
    description="Advanced heuristics-based compliance analysis API",
    version="1.0.0",
    contact={
        "name": "CDSI Support",
        "email": "consulting@getcdsi.com"
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html"
    },
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Authentication and authorization
async def get_current_tier(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TierLevel:
    """Extract tier level from authentication token"""
    # In production, validate JWT token and extract tier information
    # For now, use a simple mapping based on token content
    
    token = credentials.credentials
    
    # Simple tier extraction (replace with proper JWT validation)
    if token.startswith("aware_"):
        return TierLevel.AWARE
    elif token.startswith("builder_"):
        return TierLevel.BUILDER
    elif token.startswith("accelerator_"):
        return TierLevel.ACCELERATOR
    elif token.startswith("transformer_"):
        return TierLevel.TRANSFORMER
    elif token.startswith("champion_"):
        return TierLevel.CHAMPION
    else:
        # Default to free tier for invalid tokens
        return TierLevel.AWARE

async def check_rate_limit(tier: TierLevel, client_ip: str = "127.0.0.1"):
    """Check and enforce rate limits based on tier level"""
    tier_limits = {
        TierLevel.AWARE: 60,  # 60 requests per minute
        TierLevel.BUILDER: 300,
        TierLevel.ACCELERATOR: 1500, 
        TierLevel.TRANSFORMER: 10000,
        TierLevel.CHAMPION: -1  # Unlimited
    }
    
    limit = tier_limits[tier]
    if limit == -1:  # Unlimited
        return
    
    now = time.time()
    minute_ago = now - 60
    
    # Clean old entries
    if client_ip in rate_limits:
        rate_limits[client_ip] = [t for t in rate_limits[client_ip] if t > minute_ago]
    else:
        rate_limits[client_ip] = []
    
    # Check current count
    if len(rate_limits[client_ip]) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for tier {tier.value}. Limit: {limit} requests per minute."
        )
    
    # Add current request
    rate_limits[client_ip].append(now)

def update_api_stats(tier: TierLevel, processing_time: float, error: bool = False):
    """Update API usage statistics"""
    api_stats['total_requests'] += 1
    api_stats['total_processing_time'] += processing_time
    
    tier_key = tier.value
    if tier_key not in api_stats['requests_by_tier']:
        api_stats['requests_by_tier'][tier_key] = 0
    api_stats['requests_by_tier'][tier_key] += 1
    
    if error:
        api_stats['errors'] += 1

# API Routes

@app.get("/", tags=["Health"])
async def root():
    """API health check"""
    return {
        "service": "CDSI Compliance API", 
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    global heuristics_engine, module_loader
    
    health_status = {
        "service": "healthy",
        "engine": "healthy" if heuristics_engine else "unhealthy",
        "loader": "healthy" if module_loader else "unhealthy",
        "timestamp": datetime.now().isoformat()
    }
    
    # Check engine health
    if heuristics_engine:
        try:
            stats = heuristics_engine.get_performance_stats()
            health_status["engine_stats"] = stats
        except Exception as e:
            health_status["engine"] = f"error: {str(e)}"
    
    status_code = status.HTTP_200_OK
    if health_status["engine"] != "healthy" or health_status["loader"] != "healthy":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return health_status

@app.post("/analyze", response_model=ComplianceResponse, tags=["Compliance"])
async def analyze_content(
    request: ComplianceRequest,
    background_tasks: BackgroundTasks,
    tier: TierLevel = Depends(get_current_tier)
):
    """Analyze content for compliance patterns"""
    start_time = time.time()
    
    try:
        # Check rate limits
        await check_rate_limit(tier)
        
        # Validate content size for tier
        tier_limits = {
            TierLevel.AWARE: 1024 * 1024,  # 1MB
            TierLevel.BUILDER: 10 * 1024 * 1024,  # 10MB
            TierLevel.ACCELERATOR: 100 * 1024 * 1024,  # 100MB
            TierLevel.TRANSFORMER: 1024 * 1024 * 1024,  # 1GB
            TierLevel.CHAMPION: -1  # Unlimited
        }
        
        max_size = tier_limits[tier]
        if max_size != -1 and len(request.content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Content size exceeds tier limit. Max size for {tier.value}: {max_size} bytes"
            )
        
        # Set engine tier level
        heuristics_engine.set_tier_level(tier)
        
        # Load requested modules if specified
        if request.modules:
            for module_id in request.modules:
                try:
                    module_loader.load_module(module_id)
                except Exception as e:
                    logger.warning(f"Failed to load requested module {module_id}: {e}")
        
        # Update engine with current patterns
        all_patterns = module_loader.get_all_patterns()
        heuristics_engine.patterns.update(all_patterns)
        
        # Process content
        result = await heuristics_engine.process_content(
            request.content, 
            request.content_id
        )
        
        # Convert result to response format
        response = ComplianceResponse(
            content_id=result.content_id,
            risk_level=result.risk_level.value,
            overall_score=result.overall_score,
            total_matches=result.total_matches,
            unique_patterns=result.unique_patterns,
            processing_time_ms=result.processing_time_ms,
            categories_detected=result.categories_detected,
            tier_level=result.tier_level.value,
            matches=[
                {
                    "pattern_id": match.pattern_id,
                    "pattern_text": match.pattern_text,
                    "category": match.category,
                    "confidence": match.confidence,
                    "risk_score": match.risk_score,
                    "context": match.context
                }
                for match in result.matches
            ],
            timestamp=result.timestamp
        )
        
        # Update statistics in background
        processing_time = time.time() - start_time
        background_tasks.add_task(update_api_stats, tier, processing_time)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        background_tasks.add_task(update_api_stats, tier, processing_time, error=True)
        
        logger.error(f"Content analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content analysis failed: {str(e)}"
        )

@app.get("/modules", response_model=List[ModuleInfo], tags=["Modules"])
async def get_available_modules(tier: TierLevel = Depends(get_current_tier)):
    """Get available modules for current tier"""
    try:
        module_loader.set_tier_level(tier)
        available_modules = module_loader.get_available_modules()
        
        module_info = []
        for module_def in available_modules:
            # Get pattern count for loaded modules
            pattern_count = 0
            if module_def.id in module_loader.loaded_modules:
                loaded_module = module_loader.loaded_modules[module_def.id]
                pattern_count = len(loaded_module.patterns)
            
            module_info.append(ModuleInfo(
                id=module_def.id,
                name=module_def.name,
                module_type=module_def.module_type.value,
                jurisdiction=module_def.jurisdiction,
                tier_level=module_def.tier_level.value,
                active=module_def.active,
                pattern_count=pattern_count
            ))
        
        return module_info
        
    except Exception as e:
        logger.error(f"Failed to get modules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get modules: {str(e)}"
        )

@app.post("/modules/{module_id}/load", tags=["Modules"])
async def load_module(
    module_id: str,
    tier: TierLevel = Depends(get_current_tier)
):
    """Load a specific regulatory module"""
    try:
        module_loader.set_tier_level(tier)
        loaded_module = module_loader.load_module(module_id)
        
        if not loaded_module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module {module_id} not found"
            )
        
        if loaded_module.status.value != "loaded":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to load module {module_id}: {loaded_module.error_message}"
            )
        
        return {
            "module_id": module_id,
            "status": loaded_module.status.value,
            "pattern_count": len(loaded_module.patterns),
            "load_time": loaded_module.load_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load module {module_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load module: {str(e)}"
        )

@app.get("/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_statistics(tier: TierLevel = Depends(get_current_tier)):
    """Get system performance and usage statistics"""
    try:
        # Only allow certain tiers to access detailed stats
        if tier in [TierLevel.AWARE, TierLevel.BUILDER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Statistics access not available for this tier"
            )
        
        engine_stats = heuristics_engine.get_performance_stats()
        module_stats = module_loader.get_module_stats()
        
        return StatsResponse(
            engine_stats=engine_stats,
            module_stats=module_stats,
            api_stats=api_stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )

@app.get("/tier-info", response_model=TierConfig, tags=["Configuration"])
async def get_tier_info(tier: TierLevel = Depends(get_current_tier)):
    """Get current tier configuration and limits"""
    tier_configs = {
        TierLevel.AWARE: {
            "rate_limit_per_minute": 60,
            "max_content_size": 1024 * 1024
        },
        TierLevel.BUILDER: {
            "rate_limit_per_minute": 300,
            "max_content_size": 10 * 1024 * 1024
        },
        TierLevel.ACCELERATOR: {
            "rate_limit_per_minute": 1500,
            "max_content_size": 100 * 1024 * 1024
        },
        TierLevel.TRANSFORMER: {
            "rate_limit_per_minute": 10000,
            "max_content_size": 1024 * 1024 * 1024
        },
        TierLevel.CHAMPION: {
            "rate_limit_per_minute": -1,  # Unlimited
            "max_content_size": -1  # Unlimited
        }
    }
    
    config = tier_configs[tier]
    available_modules = [m.id for m in module_loader.get_available_modules(tier)]
    
    return TierConfig(
        tier_level=tier.value,
        rate_limit_per_minute=config["rate_limit_per_minute"],
        max_content_size=config["max_content_size"],
        available_modules=available_modules
    )

# Background tasks for maintenance
async def cleanup_rate_limits():
    """Periodic cleanup of rate limit data"""
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes
        try:
            now = time.time()
            hour_ago = now - 3600
            
            # Clean entries older than 1 hour
            for client_ip in list(rate_limits.keys()):
                rate_limits[client_ip] = [t for t in rate_limits[client_ip] if t > hour_ago]
                if not rate_limits[client_ip]:
                    del rate_limits[client_ip]
                    
            logger.debug(f"Rate limit cleanup complete. Active clients: {len(rate_limits)}")
        except Exception as e:
            logger.error(f"Rate limit cleanup failed: {e}")

# Start background tasks on startup
@app.on_event("startup")
async def start_background_tasks():
    """Start background maintenance tasks"""
    asyncio.create_task(cleanup_rate_limits())

def main():
    """Run the API server"""
    uvicorn.run(
        "src.api.compliance_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()