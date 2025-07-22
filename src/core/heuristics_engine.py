#!/usr/bin/env python3
"""
CDSI Heuristics Engine - Core Pattern Processing System

Advanced heuristics-based compliance pattern detection and evolution system.
Implements proprietary algorithms for regulatory compliance without AI/ML dependencies.

Features:
- Dynamic pattern evolution without machine learning
- Explainable decision making for regulatory compliance
- Multi-tier processing capabilities
- Performance-optimized pattern matching

Author: bdstest
License: Apache 2.0
Copyright: 2025 CDSI - Compliance Data Systems Insights
"""

import asyncio
import json
import logging
import re
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import sqlite3
import yaml
from concurrent.futures import ThreadPoolExecutor
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TierLevel(Enum):
    """CDSI maturity tier levels"""
    AWARE = "aware"
    BUILDER = "builder" 
    ACCELERATOR = "accelerator"
    TRANSFORMER = "transformer"
    CHAMPION = "champion"

class RiskLevel(Enum):
    """Compliance risk levels"""
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class PatternMatch:
    """Single pattern match result"""
    pattern_id: str
    pattern_text: str
    category: str
    algorithm: str
    confidence: float
    position: int
    context: str
    risk_score: float
    tier_level: TierLevel
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ProcessingResult:
    """Complete processing result for content"""
    content_id: str
    content_length: int
    total_matches: int
    unique_patterns: int
    risk_level: RiskLevel
    overall_score: float
    processing_time_ms: float
    matches: List[PatternMatch]
    categories_detected: List[str]
    tier_level: TierLevel
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class PatternDefinition:
    """Pattern definition with metadata"""
    id: str
    text: str
    category: str
    risk_weight: float
    tier_level: TierLevel
    jurisdiction: str
    active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

class HeuristicsEngine:
    """
    Core CDSI Heuristics Engine
    
    Implements proprietary pattern matching and evolution algorithms
    for compliance detection without traditional AI/ML approaches.
    """
    
    def __init__(self, config_path: str = "config/heuristics_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_configuration()
        self.db_path = Path("data/heuristics.db")
        self.tier_level = TierLevel.AWARE
        
        # Initialize components
        self._initialize_database()
        self.patterns = self._load_patterns()
        self.performance_stats = self._initialize_stats()
        
        # Thread pool for concurrent processing
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self._stats_lock = threading.Lock()
        
        logger.info(f"Heuristics Engine initialized with {len(self.patterns)} patterns")
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load heuristics engine configuration"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)
            else:
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration for heuristics engine"""
        return {
            'processing': {
                'max_concurrent': 4,
                'timeout_seconds': 30,
                'batch_size': 100
            },
            'tier_limits': {
                TierLevel.AWARE.value: {
                    'max_patterns': 50,
                    'max_content_size': 1024 * 1024,  # 1MB
                    'rate_limit_per_minute': 60
                },
                TierLevel.BUILDER.value: {
                    'max_patterns': 200,
                    'max_content_size': 10 * 1024 * 1024,  # 10MB
                    'rate_limit_per_minute': 300
                },
                TierLevel.ACCELERATOR.value: {
                    'max_patterns': 1000,
                    'max_content_size': 100 * 1024 * 1024,  # 100MB
                    'rate_limit_per_minute': 1500
                },
                TierLevel.TRANSFORMER.value: {
                    'max_patterns': 5000,
                    'max_content_size': 1024 * 1024 * 1024,  # 1GB
                    'rate_limit_per_minute': 10000
                },
                TierLevel.CHAMPION.value: {
                    'max_patterns': -1,  # Unlimited
                    'max_content_size': -1,  # Unlimited
                    'rate_limit_per_minute': -1  # Unlimited
                }
            },
            'risk_scoring': {
                'category_weights': {
                    'enforcement_risk': 3.0,
                    'privacy_data': 2.0,
                    'ai_tech': 1.8,
                    'compliance_process': 1.5,
                    'jurisdiction_flags': 2.2
                },
                'thresholds': {
                    'low': 2.0,
                    'medium': 5.0,
                    'high': 10.0,
                    'critical': 20.0
                }
            }
        }
    
    def _initialize_database(self):
        """Initialize SQLite database for pattern storage and evolution"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Pattern definitions table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS patterns (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    category TEXT NOT NULL,
                    risk_weight REAL NOT NULL,
                    tier_level TEXT NOT NULL,
                    jurisdiction TEXT NOT NULL,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    match_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0
                )
            ''')
            
            # Pattern evolution tracking
            conn.execute('''
                CREATE TABLE IF NOT EXISTS pattern_evolution (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id TEXT NOT NULL,
                    old_risk_weight REAL,
                    new_risk_weight REAL,
                    old_success_rate REAL,
                    new_success_rate REAL,
                    evolution_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (pattern_id) REFERENCES patterns (id)
                )
            ''')
            
            # Processing results history
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processing_history (
                    id TEXT PRIMARY KEY,
                    content_id TEXT NOT NULL,
                    tier_level TEXT NOT NULL,
                    total_matches INTEGER NOT NULL,
                    risk_level TEXT NOT NULL,
                    overall_score REAL NOT NULL,
                    processing_time_ms REAL NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            # Performance statistics
            conn.execute('''
                CREATE TABLE IF NOT EXISTS performance_stats (
                    metric_name TEXT PRIMARY KEY,
                    metric_value REAL NOT NULL,
                    last_updated TEXT NOT NULL
                )
            ''')
            
            conn.commit()
    
    def _load_patterns(self) -> Dict[str, PatternDefinition]:
        """Load patterns from database and configuration"""
        patterns = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT id, text, category, risk_weight, tier_level, 
                           jurisdiction, active, created_at, last_updated
                    FROM patterns WHERE active = TRUE
                ''')
                
                for row in cursor.fetchall():
                    pattern = PatternDefinition(
                        id=row[0],
                        text=row[1],
                        category=row[2],
                        risk_weight=row[3],
                        tier_level=TierLevel(row[4]),
                        jurisdiction=row[5],
                        active=bool(row[6]),
                        created_at=row[7],
                        last_updated=row[8]
                    )
                    patterns[pattern.id] = pattern
                    
        except sqlite3.Error as e:
            logger.error(f"Failed to load patterns from database: {e}")
        
        # Load default patterns if database is empty
        if not patterns:
            patterns = self._load_default_patterns()
            self._save_patterns_to_db(patterns)
        
        return patterns
    
    def _load_default_patterns(self) -> Dict[str, PatternDefinition]:
        """Load default compliance patterns"""
        default_patterns = {
            # Privacy & Data Protection
            'gdpr_001': PatternDefinition(
                id='gdpr_001',
                text=r'\bGDPR\b|\bGeneral Data Protection Regulation\b',
                category='privacy_data',
                risk_weight=2.5,
                tier_level=TierLevel.AWARE,
                jurisdiction='EU'
            ),
            'ccpa_001': PatternDefinition(
                id='ccpa_001', 
                text=r'\bCCPA\b|\bCalifornia Consumer Privacy Act\b',
                category='privacy_data',
                risk_weight=2.3,
                tier_level=TierLevel.AWARE,
                jurisdiction='US_CA'
            ),
            'pii_001': PatternDefinition(
                id='pii_001',
                text=r'\bpersonal\s+information\b|\bPII\b|\bpersonal\s+data\b',
                category='privacy_data',
                risk_weight=1.8,
                tier_level=TierLevel.AWARE,
                jurisdiction='GLOBAL'
            ),
            
            # AI & Technology
            'ai_001': PatternDefinition(
                id='ai_001',
                text=r'\bartificial\s+intelligence\b|\bmachine\s+learning\b|\bAI\s+system\b',
                category='ai_tech',
                risk_weight=2.0,
                tier_level=TierLevel.AWARE,
                jurisdiction='GLOBAL'
            ),
            'automated_decision': PatternDefinition(
                id='auto_001',
                text=r'\bautomated\s+decision\b|\balgorithmic\s+decision\b',
                category='ai_tech', 
                risk_weight=2.2,
                tier_level=TierLevel.BUILDER,
                jurisdiction='GLOBAL'
            ),
            
            # Enforcement & Risk
            'enforcement_001': PatternDefinition(
                id='enf_001',
                text=r'\benforcement\s+action\b|\bpenalty\b|\bfine\b|\bviolation\b',
                category='enforcement_risk',
                risk_weight=3.5,
                tier_level=TierLevel.AWARE,
                jurisdiction='GLOBAL'
            ),
            'investigation': PatternDefinition(
                id='inv_001',
                text=r'\binvestigation\b|\bsubpoena\b|\bcease\s+and\s+desist\b',
                category='enforcement_risk',
                risk_weight=4.0,
                tier_level=TierLevel.BUILDER,
                jurisdiction='GLOBAL'
            ),
            
            # Compliance Process
            'audit_001': PatternDefinition(
                id='aud_001',
                text=r'\bcompliance\s+audit\b|\brisk\s+assessment\b|\bDPIA\b',
                category='compliance_process',
                risk_weight=1.5,
                tier_level=TierLevel.BUILDER,
                jurisdiction='GLOBAL'
            )
        }
        
        return default_patterns
    
    def _save_patterns_to_db(self, patterns: Dict[str, PatternDefinition]):
        """Save patterns to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for pattern in patterns.values():
                    conn.execute('''
                        INSERT OR REPLACE INTO patterns 
                        (id, text, category, risk_weight, tier_level, jurisdiction, 
                         active, created_at, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        pattern.id, pattern.text, pattern.category,
                        pattern.risk_weight, pattern.tier_level.value,
                        pattern.jurisdiction, pattern.active,
                        pattern.created_at, pattern.last_updated
                    ))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to save patterns to database: {e}")
    
    def _initialize_stats(self) -> Dict[str, float]:
        """Initialize performance statistics"""
        return {
            'total_processed': 0,
            'total_matches': 0,
            'avg_processing_time': 0.0,
            'patterns_evolved': 0,
            'accuracy_rate': 0.0
        }
    
    def set_tier_level(self, tier: TierLevel):
        """Set the current processing tier level"""
        self.tier_level = tier
        logger.info(f"Tier level set to: {tier.value}")
    
    def _check_tier_limits(self, content_length: int) -> bool:
        """Check if content size is within tier limits"""
        tier_config = self.config['tier_limits'][self.tier_level.value]
        max_size = tier_config['max_content_size']
        
        if max_size == -1:  # Unlimited
            return True
        
        return content_length <= max_size
    
    def _get_available_patterns(self) -> List[PatternDefinition]:
        """Get patterns available for current tier level"""
        available_patterns = []
        tier_hierarchy = [
            TierLevel.AWARE,
            TierLevel.BUILDER,
            TierLevel.ACCELERATOR, 
            TierLevel.TRANSFORMER,
            TierLevel.CHAMPION
        ]
        
        current_tier_index = tier_hierarchy.index(self.tier_level)
        
        for pattern in self.patterns.values():
            pattern_tier_index = tier_hierarchy.index(pattern.tier_level)
            if pattern_tier_index <= current_tier_index:
                available_patterns.append(pattern)
        
        # Apply pattern count limits
        tier_config = self.config['tier_limits'][self.tier_level.value]
        max_patterns = tier_config['max_patterns']
        
        if max_patterns != -1 and len(available_patterns) > max_patterns:
            # Sort by risk weight and take top patterns
            available_patterns.sort(key=lambda p: p.risk_weight, reverse=True)
            available_patterns = available_patterns[:max_patterns]
        
        return available_patterns
    
    async def process_content(self, content: str, content_id: Optional[str] = None) -> ProcessingResult:
        """
        Process content using heuristics engine
        
        Args:
            content: Text content to analyze
            content_id: Optional unique identifier for content
            
        Returns:
            ProcessingResult with detected patterns and risk assessment
        """
        start_time = time.time()
        
        if content_id is None:
            content_id = hashlib.md5(content.encode()).hexdigest()[:12]
        
        # Check tier limits
        if not self._check_tier_limits(len(content)):
            raise ValueError(f"Content size exceeds tier limit for {self.tier_level.value}")
        
        # Get available patterns for current tier
        available_patterns = self._get_available_patterns()
        
        # Process content with available patterns
        matches = await self._match_patterns(content, available_patterns)
        
        # Calculate risk score and level
        overall_score, risk_level = self._calculate_risk_score(matches)
        
        # Extract unique categories
        categories_detected = list(set(match.category for match in matches))
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Create result
        result = ProcessingResult(
            content_id=content_id,
            content_length=len(content),
            total_matches=len(matches),
            unique_patterns=len(set(match.pattern_id for match in matches)),
            risk_level=risk_level,
            overall_score=overall_score,
            processing_time_ms=processing_time_ms,
            matches=matches,
            categories_detected=categories_detected,
            tier_level=self.tier_level
        )
        
        # Update statistics and store result
        await self._update_statistics(result)
        await self._store_result(result)
        
        return result
    
    async def _match_patterns(self, content: str, patterns: List[PatternDefinition]) -> List[PatternMatch]:
        """Match patterns against content using proprietary heuristics"""
        
        matches = []
        content_lower = content.lower()
        
        # Process patterns concurrently for performance
        async def process_pattern(pattern: PatternDefinition) -> List[PatternMatch]:
            pattern_matches = []
            
            try:
                # Compile regex pattern
                regex = re.compile(pattern.text, re.IGNORECASE | re.MULTILINE)
                
                # Find all matches
                for match in regex.finditer(content):
                    # Extract context around match
                    context_start = max(0, match.start() - 50)
                    context_end = min(len(content), match.end() + 50)
                    context = content[context_start:context_end].replace('\n', ' ').strip()
                    
                    # Calculate confidence based on pattern quality
                    confidence = self._calculate_pattern_confidence(pattern, match, content)
                    
                    # Calculate risk score for this match
                    category_weight = self.config['risk_scoring']['category_weights'].get(
                        pattern.category, 1.0
                    )
                    risk_score = pattern.risk_weight * category_weight * confidence
                    
                    pattern_match = PatternMatch(
                        pattern_id=pattern.id,
                        pattern_text=match.group(),
                        category=pattern.category,
                        algorithm="heuristic_regex",
                        confidence=confidence,
                        position=match.start(),
                        context=context,
                        risk_score=risk_score,
                        tier_level=pattern.tier_level
                    )
                    
                    pattern_matches.append(pattern_match)
                    
            except re.error as e:
                logger.warning(f"Invalid regex pattern {pattern.id}: {e}")
            
            return pattern_matches
        
        # Process patterns concurrently
        tasks = [process_pattern(pattern) for pattern in patterns]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect all matches
        for result in results:
            if isinstance(result, list):
                matches.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Pattern processing error: {result}")
        
        # Deduplicate overlapping matches
        matches = self._deduplicate_matches(matches)
        
        return matches
    
    def _calculate_pattern_confidence(self, pattern: PatternDefinition, 
                                    match: re.Match, content: str) -> float:
        """Calculate confidence score for a pattern match"""
        confidence = 0.8  # Base confidence
        
        # Boost confidence for exact matches
        if match.group().lower() in pattern.text.lower():
            confidence += 0.15
        
        # Boost confidence for context quality
        context_start = max(0, match.start() - 20)
        context_end = min(len(content), match.end() + 20)
        context = content[context_start:context_end].lower()
        
        # Look for supporting context keywords
        support_keywords = {
            'privacy_data': ['privacy', 'data', 'personal', 'information'],
            'ai_tech': ['technology', 'system', 'algorithm', 'automated'],
            'enforcement_risk': ['regulatory', 'legal', 'compliance', 'violation'],
            'compliance_process': ['audit', 'assessment', 'review', 'evaluation']
        }
        
        category_keywords = support_keywords.get(pattern.category, [])
        support_found = sum(1 for keyword in category_keywords if keyword in context)
        confidence += min(0.1, support_found * 0.025)
        
        # Cap confidence at 1.0
        return min(1.0, confidence)
    
    def _deduplicate_matches(self, matches: List[PatternMatch]) -> List[PatternMatch]:
        """Remove duplicate and overlapping matches"""
        if not matches:
            return []
        
        # Sort by position
        matches.sort(key=lambda x: x.position)
        
        unique_matches = []
        for match in matches:
            # Check for overlaps with existing matches
            overlap = False
            for existing in unique_matches:
                # Check if positions overlap significantly
                if abs(match.position - existing.position) < 10:
                    # Keep the match with higher risk score
                    if match.risk_score > existing.risk_score:
                        unique_matches.remove(existing)
                        unique_matches.append(match)
                    overlap = True
                    break
            
            if not overlap:
                unique_matches.append(match)
        
        return unique_matches
    
    def _calculate_risk_score(self, matches: List[PatternMatch]) -> Tuple[float, RiskLevel]:
        """Calculate overall risk score and level"""
        if not matches:
            return 0.0, RiskLevel.INFORMATIONAL
        
        # Sum all match risk scores
        total_score = sum(match.risk_score for match in matches)
        
        # Apply category diversity bonus
        unique_categories = set(match.category for match in matches)
        diversity_bonus = len(unique_categories) * 0.5
        total_score += diversity_bonus
        
        # Apply tier-based multipliers
        tier_multipliers = {
            TierLevel.AWARE: 1.0,
            TierLevel.BUILDER: 1.1,
            TierLevel.ACCELERATOR: 1.2,
            TierLevel.TRANSFORMER: 1.3,
            TierLevel.CHAMPION: 1.5
        }
        total_score *= tier_multipliers[self.tier_level]
        
        # Determine risk level
        thresholds = self.config['risk_scoring']['thresholds']
        
        if total_score >= thresholds['critical']:
            risk_level = RiskLevel.CRITICAL
        elif total_score >= thresholds['high']:
            risk_level = RiskLevel.HIGH
        elif total_score >= thresholds['medium']:
            risk_level = RiskLevel.MEDIUM
        elif total_score >= thresholds['low']:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.INFORMATIONAL
        
        return total_score, risk_level
    
    async def _update_statistics(self, result: ProcessingResult):
        """Update engine performance statistics"""
        with self._stats_lock:
            self.performance_stats['total_processed'] += 1
            self.performance_stats['total_matches'] += result.total_matches
            
            # Update average processing time
            current_avg = self.performance_stats['avg_processing_time']
            total_processed = self.performance_stats['total_processed']
            new_avg = ((current_avg * (total_processed - 1)) + result.processing_time_ms) / total_processed
            self.performance_stats['avg_processing_time'] = new_avg
        
        # Store stats in database periodically
        if self.performance_stats['total_processed'] % 100 == 0:
            await self._store_statistics()
    
    async def _store_result(self, result: ProcessingResult):
        """Store processing result in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO processing_history
                    (id, content_id, tier_level, total_matches, risk_level,
                     overall_score, processing_time_ms, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"{result.content_id}_{result.timestamp}",
                    result.content_id,
                    result.tier_level.value,
                    result.total_matches,
                    result.risk_level.value,
                    result.overall_score,
                    result.processing_time_ms,
                    result.timestamp
                ))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to store processing result: {e}")
    
    async def _store_statistics(self):
        """Store performance statistics in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                timestamp = datetime.now().isoformat()
                for metric_name, metric_value in self.performance_stats.items():
                    conn.execute('''
                        INSERT OR REPLACE INTO performance_stats
                        (metric_name, metric_value, last_updated)
                        VALUES (?, ?, ?)
                    ''', (metric_name, metric_value, timestamp))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to store statistics: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        with self._stats_lock:
            return self.performance_stats.copy()
    
    def get_pattern_stats(self) -> Dict[str, Any]:
        """Get pattern usage statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get pattern match counts
                cursor = conn.execute('''
                    SELECT category, COUNT(*) as pattern_count,
                           AVG(risk_weight) as avg_risk_weight
                    FROM patterns WHERE active = TRUE
                    GROUP BY category
                ''')
                
                category_stats = {}
                for row in cursor.fetchall():
                    category_stats[row[0]] = {
                        'pattern_count': row[1],
                        'avg_risk_weight': row[2]
                    }
                
                return {
                    'total_patterns': len(self.patterns),
                    'active_patterns': len([p for p in self.patterns.values() if p.active]),
                    'category_breakdown': category_stats,
                    'tier_level': self.tier_level.value
                }
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get pattern statistics: {e}")
            return {}
    
    async def evolve_patterns(self, feedback_data: Dict[str, Any]):
        """
        Evolve patterns based on feedback data
        
        This implements proprietary pattern evolution algorithms
        without traditional machine learning approaches.
        """
        logger.info("Starting pattern evolution process")
        
        # Extract feedback metrics
        pattern_performance = feedback_data.get('pattern_performance', {})
        false_positives = feedback_data.get('false_positives', [])
        missed_detections = feedback_data.get('missed_detections', [])
        
        evolution_count = 0
        
        # Evolve existing patterns based on performance
        for pattern_id, performance in pattern_performance.items():
            if pattern_id in self.patterns:
                pattern = self.patterns[pattern_id]
                old_weight = pattern.risk_weight
                
                # Calculate new risk weight based on performance
                success_rate = performance.get('success_rate', 0.5)
                false_positive_rate = performance.get('false_positive_rate', 0.1)
                
                # Proprietary evolution algorithm
                adjustment_factor = (success_rate - false_positive_rate) * 0.2
                new_weight = old_weight * (1 + adjustment_factor)
                
                # Clamp weight within reasonable bounds
                new_weight = max(0.1, min(5.0, new_weight))
                
                if abs(new_weight - old_weight) > 0.05:  # Meaningful change threshold
                    pattern.risk_weight = new_weight
                    pattern.last_updated = datetime.now().isoformat()
                    
                    # Log evolution
                    await self._log_pattern_evolution(
                        pattern_id, old_weight, new_weight, 
                        success_rate, success_rate, "weight_adjustment"
                    )
                    
                    evolution_count += 1
        
        # Handle false positives by reducing pattern weights
        for fp_data in false_positives:
            pattern_id = fp_data.get('pattern_id')
            if pattern_id in self.patterns:
                pattern = self.patterns[pattern_id]
                old_weight = pattern.risk_weight
                
                # Reduce weight for false positive patterns
                new_weight = old_weight * 0.9
                pattern.risk_weight = max(0.1, new_weight)
                pattern.last_updated = datetime.now().isoformat()
                
                await self._log_pattern_evolution(
                    pattern_id, old_weight, new_weight, 
                    0, 0, "false_positive_reduction"
                )
                
                evolution_count += 1
        
        # Save evolved patterns
        if evolution_count > 0:
            self._save_patterns_to_db(self.patterns)
            self.performance_stats['patterns_evolved'] += evolution_count
            
        logger.info(f"Pattern evolution complete: {evolution_count} patterns evolved")
        
        return {
            'patterns_evolved': evolution_count,
            'total_patterns': len(self.patterns),
            'evolution_timestamp': datetime.now().isoformat()
        }
    
    async def _log_pattern_evolution(self, pattern_id: str, old_weight: float, 
                                   new_weight: float, old_success: float, 
                                   new_success: float, evolution_type: str):
        """Log pattern evolution event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO pattern_evolution
                    (pattern_id, old_risk_weight, new_risk_weight, old_success_rate,
                     new_success_rate, evolution_type, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pattern_id, old_weight, new_weight, old_success,
                    new_success, evolution_type, datetime.now().isoformat()
                ))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to log pattern evolution: {e}")
    
    def export_results(self, result: ProcessingResult, format: str = "json") -> str:
        """Export processing results in specified format"""
        data = asdict(result)
        
        if format.lower() == "json":
            return json.dumps(data, indent=2, ensure_ascii=False, default=str)
        elif format.lower() == "yaml":
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'thread_pool'):
            self.thread_pool.shutdown(wait=True)

async def main():
    """Test the heuristics engine"""
    print("🧠 CDSI Heuristics Engine Test")
    print("=" * 50)
    
    # Initialize engine
    engine = HeuristicsEngine()
    
    # Set tier level for testing
    engine.set_tier_level(TierLevel.BUILDER)
    
    # Test content with various compliance patterns
    test_content = """
    Our company processes personal information under GDPR compliance requirements.
    We use artificial intelligence and machine learning systems for automated decision-making
    in our hiring processes. Recent enforcement actions by regulatory authorities have
    resulted in significant penalties for CCPA violations. We conduct regular compliance
    audits and risk assessments to ensure data protection compliance.
    
    The Texas Attorney General has issued new guidance on AI systems, and the FTC
    has announced investigation procedures for algorithmic bias. Companies must now
    implement comprehensive DPIA processes for any automated processing of biometric data.
    """
    
    # Process content
    print("Processing test content...")
    result = await engine.process_content(test_content, "test_content_001")
    
    # Display results
    print(f"\n📊 Processing Results:")
    print(f"Content ID: {result.content_id}")
    print(f"Risk Level: {result.risk_level.value}")
    print(f"Overall Score: {result.overall_score:.2f}")
    print(f"Total Matches: {result.total_matches}")
    print(f"Unique Patterns: {result.unique_patterns}")
    print(f"Categories: {', '.join(result.categories_detected)}")
    print(f"Processing Time: {result.processing_time_ms:.1f}ms")
    print(f"Tier Level: {result.tier_level.value}")
    
    # Display detailed matches
    print(f"\n🔍 Pattern Matches:")
    for i, match in enumerate(result.matches[:10], 1):  # Show first 10 matches
        print(f"  {i}. {match.pattern_text} ({match.algorithm})")
        print(f"     Category: {match.category}")
        print(f"     Risk Score: {match.risk_score:.2f}")
        print(f"     Confidence: {match.confidence:.2f}")
        print(f"     Context: {match.context[:80]}...")
        print()
    
    # Display performance statistics
    print("📈 Performance Statistics:")
    stats = engine.get_performance_stats()
    for metric, value in stats.items():
        print(f"   {metric}: {value}")
    
    # Display pattern statistics
    print("\n📋 Pattern Statistics:")
    pattern_stats = engine.get_pattern_stats()
    for key, value in pattern_stats.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())