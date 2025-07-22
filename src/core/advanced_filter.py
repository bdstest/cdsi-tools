#!/usr/bin/env python3
"""
Advanced Content Filtering System with Multi-Pattern Matching

Combines regex, spaCy NLP, and fuzzy matching for comprehensive
regulatory content detection and classification.

Features:
- Modular pattern configuration
- Multi-algorithm matching (regex, spaCy, fuzzy)
- Risk-based scoring
- Performance optimization
- Audit trail logging

Author: bdstest
License: Apache 2.0
"""

import re
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import hashlib

import yaml
try:
    from fuzzywuzzy import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    logging.warning("fuzzywuzzy not available - fuzzy matching disabled")

try:
    import spacy
    from spacy.matcher import Matcher
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available - NLP matching disabled")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MatchResult:
    """Single pattern match result"""
    pattern: str
    category: str
    algorithm: str  # regex, spacy, fuzzy
    confidence: float
    position: int
    context: str
    risk_score: float

@dataclass
class FilterResult:
    """Complete filtering result for a text"""
    text_id: str
    text_length: int
    total_matches: int
    unique_patterns: int
    risk_level: str
    overall_score: float
    processing_time_ms: float
    matches: List[MatchResult]
    categories_detected: List[str]
    timestamp: str

class AdvancedContentFilter:
    """Advanced multi-algorithm content filtering system"""
    
    def __init__(self, config_path: str = "config/keyword_patterns.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_configuration()
        
        # Initialize pattern matching systems
        self.regex_patterns = self._compile_regex_patterns()
        self.spacy_matcher = self._initialize_spacy_matcher() if SPACY_AVAILABLE else None
        self.keyword_categories = self.config.get('keyword_categories', {})
        self.risk_scoring = self.config.get('risk_scoring', {})
        
        # Performance tracking
        self.stats = {
            'total_processed': 0,
            'total_matches': 0,
            'avg_processing_time': 0,
            'pattern_hit_rates': {}
        }
        
        logger.info(f"Advanced filter initialized with {len(self.regex_patterns)} regex patterns")
        if self.spacy_matcher:
            logger.info("spaCy NLP matching enabled")
        if FUZZY_AVAILABLE:
            logger.info("Fuzzy matching enabled")
    
    def _load_configuration(self) -> Dict:
        """Load pattern configuration from YAML"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            return self._get_fallback_config()
    
    def _get_fallback_config(self) -> Dict:
        """Fallback configuration if file not found"""
        return {
            'keyword_categories': {
                'ai_tech': ['artificial intelligence', 'machine learning', 'AI'],
                'privacy_data': ['GDPR', 'CCPA', 'privacy'],
                'enforcement_risk': ['penalty', 'fine', 'violation']
            },
            'risk_scoring': {
                'category_multipliers': {
                    'enforcement_risk': 3.0,
                    'ai_tech': 1.5,
                    'privacy_data': 1.5
                },
                'thresholds': {'low': 2.0, 'medium': 5.0, 'high': 8.0}
            },
            'fuzzy_matching': {'threshold': 85}
        }
    
    def _compile_regex_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for efficient matching"""
        compiled_patterns = {}
        regex_config = self.config.get('regex_patterns', {})
        
        for category, patterns in regex_config.items():
            compiled_patterns[category] = []
            for pattern_str in patterns:
                try:
                    pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
                    compiled_patterns[category].append(pattern)
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern_str}': {e}")
        
        return compiled_patterns
    
    def _initialize_spacy_matcher(self) -> Optional[Matcher]:
        """Initialize spaCy matcher with token patterns"""
        if not SPACY_AVAILABLE:
            return None
        
        try:
            # Load small English model for efficiency
            nlp = spacy.load("en_core_web_sm")
            matcher = Matcher(nlp.vocab)
            
            spacy_config = self.config.get('spacy_patterns', {})
            for category, patterns in spacy_config.items():
                matcher.add(f"PATTERN_{category.upper()}", patterns)
            
            self.nlp = nlp
            return matcher
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' not found - install with: python -m spacy download en_core_web_sm")
            return None
    
    def _regex_match(self, text: str) -> List[MatchResult]:
        """Perform regex-based pattern matching"""
        matches = []
        
        for category, patterns in self.regex_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    # Extract context around match
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].replace('\n', ' ').strip()
                    
                    # Calculate risk score
                    multiplier = self.risk_scoring.get('category_multipliers', {}).get(category, 1.0)
                    risk_score = len(match.group()) * multiplier * 0.1
                    
                    matches.append(MatchResult(
                        pattern=pattern.pattern,
                        category=category,
                        algorithm="regex",
                        confidence=1.0,  # Regex matches are exact
                        position=match.start(),
                        context=context,
                        risk_score=risk_score
                    ))
        
        return matches
    
    def _spacy_match(self, text: str) -> List[MatchResult]:
        """Perform spaCy NLP-based pattern matching"""
        if not self.spacy_matcher:
            return []
        
        matches = []
        doc = self.nlp(text)
        spacy_matches = self.spacy_matcher(doc)
        
        for match_id, start, end in spacy_matches:
            span = doc[start:end]
            label = self.nlp.vocab.strings[match_id]
            category = label.replace('PATTERN_', '').lower()
            
            # Extract context
            context_start = max(0, span.start - 10)
            context_end = min(len(doc), span.end + 10)
            context = doc[context_start:context_end].text
            
            # Calculate risk score
            multiplier = self.risk_scoring.get('category_multipliers', {}).get(category, 1.0)
            risk_score = len(span.text) * multiplier * 0.1
            
            matches.append(MatchResult(
                pattern=span.text,
                category=category,
                algorithm="spacy",
                confidence=0.95,  # spaCy confidence
                position=span.start_char,
                context=context,
                risk_score=risk_score
            ))
        
        return matches
    
    def _fuzzy_match(self, text: str) -> List[MatchResult]:
        """Perform fuzzy string matching"""
        if not FUZZY_AVAILABLE:
            return []
        
        matches = []
        fuzzy_config = self.config.get('fuzzy_matching', {})
        threshold = fuzzy_config.get('threshold', 85)
        
        text_lower = text.lower()
        words = text_lower.split()
        
        for category, terms in self.keyword_categories.items():
            for term in terms:
                term_lower = term.lower()
                
                # Check full text partial ratio
                score = fuzz.partial_ratio(term_lower, text_lower)
                if score >= threshold:
                    # Find approximate position
                    position = text_lower.find(term_lower.split()[0]) if term_lower.split() else 0
                    if position == -1:
                        position = 0
                    
                    # Extract context
                    start = max(0, position - 50)
                    end = min(len(text), position + len(term) + 50)
                    context = text[start:end].replace('\n', ' ').strip()
                    
                    # Calculate confidence and risk score
                    confidence = score / 100.0
                    multiplier = self.risk_scoring.get('category_multipliers', {}).get(category, 1.0)
                    risk_score = confidence * len(term) * multiplier * 0.1
                    
                    matches.append(MatchResult(
                        pattern=term,
                        category=category,
                        algorithm="fuzzy",
                        confidence=confidence,
                        position=position,
                        context=context,
                        risk_score=risk_score
                    ))
        
        return matches
    
    def _calculate_overall_score(self, matches: List[MatchResult]) -> Tuple[float, str]:
        """Calculate overall risk score and level"""
        total_score = sum(match.risk_score for match in matches)
        
        # Apply category bonuses for multiple categories
        categories_found = set(match.category for match in matches)
        category_bonus = len(categories_found) * 0.5
        total_score += category_bonus
        
        # Determine risk level
        thresholds = self.risk_scoring.get('thresholds', {
            'low': 2.0, 'medium': 5.0, 'high': 8.0, 'critical': 12.0
        })
        
        if total_score >= thresholds.get('critical', 12.0):
            risk_level = 'critical'
        elif total_score >= thresholds.get('high', 8.0):
            risk_level = 'high'
        elif total_score >= thresholds.get('medium', 5.0):
            risk_level = 'medium'
        elif total_score >= thresholds.get('low', 2.0):
            risk_level = 'low'
        else:
            risk_level = 'informational'
        
        return total_score, risk_level
    
    def filter_text(self, text: str, text_id: Optional[str] = None) -> FilterResult:
        """Perform comprehensive content filtering on text"""
        start_time = time.time()
        
        if text_id is None:
            text_id = hashlib.md5(text.encode()).hexdigest()[:12]
        
        # Perform all matching algorithms
        all_matches = []
        
        # Regex matching
        regex_matches = self._regex_match(text)
        all_matches.extend(regex_matches)
        
        # spaCy matching
        spacy_matches = self._spacy_match(text)
        all_matches.extend(spacy_matches)
        
        # Fuzzy matching
        fuzzy_matches = self._fuzzy_match(text)
        all_matches.extend(fuzzy_matches)
        
        # Deduplicate matches by position and pattern
        unique_matches = self._deduplicate_matches(all_matches)
        
        # Calculate scores
        overall_score, risk_level = self._calculate_overall_score(unique_matches)
        
        # Extract unique categories
        categories_detected = list(set(match.category for match in unique_matches))
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Update statistics
        self._update_stats(unique_matches, processing_time_ms)
        
        return FilterResult(
            text_id=text_id,
            text_length=len(text),
            total_matches=len(unique_matches),
            unique_patterns=len(set(match.pattern for match in unique_matches)),
            risk_level=risk_level,
            overall_score=overall_score,
            processing_time_ms=processing_time_ms,
            matches=unique_matches,
            categories_detected=categories_detected,
            timestamp=datetime.now().isoformat()
        )
    
    def _deduplicate_matches(self, matches: List[MatchResult]) -> List[MatchResult]:
        """Remove duplicate matches based on position and pattern similarity"""
        if not matches:
            return []
        
        # Sort by position
        matches.sort(key=lambda x: x.position)
        
        unique_matches = []
        for match in matches:
            # Check if this match overlaps with existing matches
            overlap = False
            for existing in unique_matches:
                position_diff = abs(match.position - existing.position)
                if position_diff < 10 and match.category == existing.category:
                    # Keep the match with higher confidence
                    if match.confidence > existing.confidence:
                        unique_matches.remove(existing)
                        unique_matches.append(match)
                    overlap = True
                    break
            
            if not overlap:
                unique_matches.append(match)
        
        return unique_matches
    
    def _update_stats(self, matches: List[MatchResult], processing_time_ms: float):
        """Update performance statistics"""
        self.stats['total_processed'] += 1
        self.stats['total_matches'] += len(matches)
        
        # Update average processing time
        total_time = self.stats['avg_processing_time'] * (self.stats['total_processed'] - 1)
        self.stats['avg_processing_time'] = (total_time + processing_time_ms) / self.stats['total_processed']
        
        # Update pattern hit rates
        for match in matches:
            pattern_key = f"{match.category}_{match.algorithm}"
            self.stats['pattern_hit_rates'][pattern_key] = self.stats['pattern_hit_rates'].get(pattern_key, 0) + 1
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        return self.stats.copy()
    
    def export_filter_result(self, result: FilterResult, format: str = "json") -> str:
        """Export filter result in specified format"""
        data = asdict(result)
        
        if format.lower() == "json":
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif format.lower() == "yaml":
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"Unsupported export format: {format}")

def main():
    """Test the advanced content filter"""
    filter_system = AdvancedContentFilter()
    
    # Test text with various patterns
    test_text = """
    The FTC announced a new enforcement action regarding artificial intelligence 
    and machine learning bias in hiring systems. The penalty of $10 million 
    was imposed for GDPR violations related to biometric data processing.
    Companies must disclose their automated decision-making processes.
    """
    
    print("🔍 Advanced Content Filter Test")
    print("-" * 50)
    
    result = filter_system.filter_text(test_text)
    
    print(f"Text ID: {result.text_id}")
    print(f"Risk Level: {result.risk_level}")
    print(f"Overall Score: {result.overall_score:.2f}")
    print(f"Total Matches: {result.total_matches}")
    print(f"Categories: {', '.join(result.categories_detected)}")
    print(f"Processing Time: {result.processing_time_ms:.1f}ms")
    
    print("\nDetailed Matches:")
    for i, match in enumerate(result.matches[:5], 1):
        print(f"  {i}. {match.pattern} ({match.algorithm}) - {match.category}")
        print(f"     Risk Score: {match.risk_score:.2f}, Confidence: {match.confidence:.2f}")
        print(f"     Context: {match.context[:80]}...")
        print()

if __name__ == "__main__":
    main()