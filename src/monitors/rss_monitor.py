#!/usr/bin/env python3
"""
RSS Monitor for AI Regulatory Watch

Monitors official regulatory RSS feeds for AI and privacy compliance updates.
Processes feeds, matches keywords, and creates structured outputs.

⚠️  INFORMATIONAL CONTENT ONLY - NOT LEGAL ADVICE
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import hashlib

import feedparser
import yaml
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class RegulatoryItem:
    """Structured regulatory information item"""
    id: str
    title: str
    description: str
    url: str
    published: str
    source: str
    jurisdiction: str
    keywords_matched: List[str]
    risk_level: str  # informational, medium, high
    timestamp_processed: str

@dataclass
class MonitoringResult:
    """Results of RSS monitoring run"""
    timestamp: str
    sources_checked: int
    items_found: int
    new_items: int
    keywords_matched: Dict[str, int]
    processing_time: float

class RSSMonitor:
    """Professional RSS monitoring for regulatory feeds"""
    
    def __init__(self, config_path: str = "config/rss_sources.yaml"):
        self.config_path = Path(config_path)
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        self.keywords = self._load_keywords()
        
        # Setup HTTP session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Initialize tracking
        self.processed_items = self._load_processed_items()
        
    def _load_config(self) -> Dict:
        """Load RSS source configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_path}")
            return self._get_default_config()
    
    def _load_keywords(self) -> Dict[str, List[str]]:
        """Load regulatory keywords for matching"""
        keyword_path = Path("config/regulatory_keywords.yaml")
        try:
            with open(keyword_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._get_default_keywords()
    
    def _load_processed_items(self) -> Set[str]:
        """Load previously processed item IDs"""
        processed_file = self.data_dir / "processed_items.json"
        if processed_file.exists():
            with open(processed_file, 'r') as f:
                data = json.load(f)
                return set(data.get('processed_ids', []))
        return set()
    
    def _save_processed_items(self):
        """Save processed item IDs to prevent reprocessing"""
        processed_file = self.data_dir / "processed_items.json"
        data = {
            'last_updated': datetime.now().isoformat(),
            'processed_ids': list(self.processed_items)
        }
        with open(processed_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _get_default_config(self) -> Dict:
        """Default RSS feed configuration (official sources only)"""
        return {
            'feeds': {
                'us_federal': [
                    {
                        'name': 'FTC News',
                        'url': 'https://www.ftc.gov/news-events/news/rss',
                        'jurisdiction': 'US_Federal',
                        'priority': 'high'
                    },
                    {
                        'name': 'NIST Publications',
                        'url': 'https://www.nist.gov/news-events/news/rss.xml',
                        'jurisdiction': 'US_Federal',
                        'priority': 'medium'
                    }
                ],
                'us_states': [
                    {
                        'name': 'California AG News',
                        'url': 'https://oag.ca.gov/rss/news.xml',
                        'jurisdiction': 'US_CA',
                        'priority': 'high'
                    }
                ],
                'international': [
                    {
                        'name': 'EU Commission Digital',
                        'url': 'https://ec.europa.eu/commission/presscorner/api/documents.cfm?cl=en&typ=1&cat=59&pag=0&format=rss',
                        'jurisdiction': 'EU',
                        'priority': 'high'
                    }
                ]
            },
            'monitoring': {
                'max_items_per_feed': 50,
                'lookback_days': 30,
                'request_timeout': 30
            }
        }
    
    def _get_default_keywords(self) -> Dict[str, List[str]]:
        """Default regulatory keywords for matching"""
        return {
            'ai_terms': [
                'artificial intelligence', 'AI', 'machine learning', 'ML',
                'deep learning', 'neural network', 'algorithm', 'automated decision',
                'bias', 'fairness', 'explainability', 'transparency'
            ],
            'privacy_terms': [
                'GDPR', 'CCPA', 'CPRA', 'privacy', 'data protection',
                'personal data', 'biometric', 'consent', 'data subject'
            ],
            'compliance_terms': [
                'compliance', 'regulation', 'enforcement', 'penalty',
                'violation', 'audit', 'assessment', 'framework'
            ],
            'high_risk_terms': [
                'enforcement action', 'penalty', 'violation', 'fine',
                'investigation', 'cease and desist', 'settlement'
            ]
        }
    
    def _generate_item_id(self, title: str, url: str, published: str) -> str:
        """Generate unique ID for regulatory item"""
        content = f"{title}{url}{published}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _match_keywords(self, text: str) -> tuple[List[str], str]:
        """Match keywords and determine risk level"""
        text_lower = text.lower()
        matched_keywords = []
        risk_level = "informational"
        
        for category, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matched_keywords.append(keyword)
                    
                    # Determine risk level based on keyword category
                    if category == 'high_risk_terms':
                        risk_level = "high"
                    elif category in ['compliance_terms', 'ai_terms'] and risk_level == "informational":
                        risk_level = "medium"
        
        return matched_keywords, risk_level
    
    async def monitor_feed(self, feed_config: Dict) -> List[RegulatoryItem]:
        """Monitor single RSS feed for regulatory updates"""
        logger.info(f"Monitoring feed: {feed_config['name']}")
        
        try:
            # Fetch feed with timeout
            response = self.session.get(
                feed_config['url'],
                timeout=self.config['monitoring']['request_timeout']
            )
            response.raise_for_status()
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            
            items = []
            max_items = self.config['monitoring']['max_items_per_feed']
            cutoff_date = datetime.now() - timedelta(
                days=self.config['monitoring']['lookback_days']
            )
            
            for entry in feed.entries[:max_items]:
                # Parse publication date
                try:
                    published = datetime(*entry.published_parsed[:6])
                except (AttributeError, ValueError):
                    published = datetime.now()
                
                # Skip old items
                if published < cutoff_date:
                    continue
                
                # Generate unique ID
                item_id = self._generate_item_id(
                    entry.title, entry.link, published.isoformat()
                )
                
                # Skip already processed items
                if item_id in self.processed_items:
                    continue
                
                # Match keywords
                search_text = f"{entry.title} {entry.get('description', '')}"
                keywords_matched, risk_level = self._match_keywords(search_text)
                
                # Only process items with keyword matches
                if keywords_matched:
                    regulatory_item = RegulatoryItem(
                        id=item_id,
                        title=entry.title,
                        description=entry.get('description', '')[:500],
                        url=entry.link,
                        published=published.isoformat(),
                        source=feed_config['name'],
                        jurisdiction=feed_config['jurisdiction'],
                        keywords_matched=keywords_matched,
                        risk_level=risk_level,
                        timestamp_processed=datetime.now().isoformat()
                    )
                    
                    items.append(regulatory_item)
                    self.processed_items.add(item_id)
                    
                    logger.info(f"New regulatory item: {entry.title[:50]}...")
            
            return items
            
        except Exception as e:
            logger.error(f"Error monitoring feed {feed_config['name']}: {str(e)}")
            return []
    
    async def run_monitoring(self) -> MonitoringResult:
        """Run complete regulatory monitoring cycle"""
        start_time = datetime.now()
        logger.info("Starting regulatory monitoring cycle")
        
        all_items = []
        sources_checked = 0
        keyword_matches = {}
        
        # Process all feed categories
        for category, feeds in self.config['feeds'].items():
            for feed_config in feeds:
                sources_checked += 1
                items = await self.monitor_feed(feed_config)
                all_items.extend(items)
                
                # Track keyword matches
                for item in items:
                    for keyword in item.keywords_matched:
                        keyword_matches[keyword] = keyword_matches.get(keyword, 0) + 1
        
        # Save new items
        if all_items:
            await self._save_regulatory_items(all_items)
        
        # Save processed item tracking
        self._save_processed_items()
        
        # Generate monitoring result
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = MonitoringResult(
            timestamp=datetime.now().isoformat(),
            sources_checked=sources_checked,
            items_found=len(all_items),
            new_items=len(all_items),
            keywords_matched=keyword_matches,
            processing_time=processing_time
        )
        
        logger.info(f"Monitoring complete: {len(all_items)} new items from {sources_checked} sources")
        return result
    
    async def _save_regulatory_items(self, items: List[RegulatoryItem]):
        """Save regulatory items to structured storage"""
        # Save as JSON for programmatic access
        items_data = [asdict(item) for item in items]
        
        output_file = self.data_dir / f"regulatory_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'item_count': len(items),
                'items': items_data
            }, f, indent=2)
        
        # Also save as YAML for human readability
        yaml_file = self.data_dir / "latest_regulatory_items.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump({
                'disclaimer': 'INFORMATIONAL CONTENT ONLY - NOT LEGAL ADVICE',
                'timestamp': datetime.now().isoformat(),
                'item_count': len(items),
                'items': items_data
            }, f, default_flow_style=False)
        
        logger.info(f"Saved {len(items)} regulatory items to {output_file}")

async def main():
    """Main monitoring function"""
    print("🔍 AI Regulatory Watch - RSS Monitor")
    print("⚠️  INFORMATIONAL CONTENT ONLY - NOT LEGAL ADVICE")
    print("-" * 60)
    
    monitor = RSSMonitor()
    result = await monitor.run_monitoring()
    
    print(f"Monitoring Results:")
    print(f"  Sources checked: {result.sources_checked}")
    print(f"  Items found: {result.items_found}")
    print(f"  Processing time: {result.processing_time:.2f}s")
    print(f"  Top keywords: {dict(list(result.keywords_matched.items())[:5])}")
    
    # Save monitoring result
    with open("data/last_monitoring_result.json", 'w') as f:
        json.dump(asdict(result), f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())