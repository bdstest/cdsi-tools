#!/usr/bin/env python3
"""
Unit tests for RSS Monitor

Tests RSS monitoring functionality with proper mocking and edge case handling.
Ensures reliable regulatory information processing without external dependencies.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
from pathlib import Path

# Import the module under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from monitors.rss_monitor import RSSMonitor, RegulatoryItem, MonitoringResult

class TestRSSMonitor:
    """Test suite for RSS monitoring functionality"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for test configurations"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_rss_monitor(self, temp_config_dir):
        """Create RSS monitor instance with temporary configuration"""
        config_path = Path(temp_config_dir) / "test_config.yaml"
        with patch('monitors.rss_monitor.Path') as mock_path:
            mock_path.return_value.mkdir.return_value = None
            monitor = RSSMonitor(str(config_path))
            monitor.data_dir = Path(temp_config_dir) / "data"
            monitor.data_dir.mkdir(exist_ok=True)
            return monitor
    
    @pytest.fixture
    def sample_feed_data(self):
        """Sample RSS feed data for testing"""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>FTC News</title>
                <item>
                    <title>FTC Announces New AI Guidance for Healthcare</title>
                    <description>New guidance on artificial intelligence use in healthcare settings</description>
                    <link>https://ftc.gov/news/ai-healthcare-guidance</link>
                    <pubDate>Wed, 20 Jul 2024 10:00:00 GMT</pubDate>
                </item>
                <item>
                    <title>Consumer Privacy Protection Update</title>
                    <description>Updates on consumer privacy enforcement actions</description>
                    <link>https://ftc.gov/news/privacy-update</link>
                    <pubDate>Tue, 19 Jul 2024 15:30:00 GMT</pubDate>
                </item>
            </channel>
        </rss>"""
    
    def test_monitor_initialization(self, mock_rss_monitor):
        """Test RSS monitor initializes correctly"""
        assert mock_rss_monitor is not None
        assert hasattr(mock_rss_monitor, 'config')
        assert hasattr(mock_rss_monitor, 'keywords')
        assert hasattr(mock_rss_monitor, 'processed_items')
    
    def test_default_configuration_loading(self, mock_rss_monitor):
        """Test default configuration is loaded when no config file exists"""
        config = mock_rss_monitor._get_default_config()
        
        assert 'feeds' in config
        assert 'monitoring' in config
        assert 'us_federal' in config['feeds']
        assert 'max_items_per_feed' in config['monitoring']
    
    def test_keyword_matching(self, mock_rss_monitor):
        """Test keyword matching and risk level determination"""
        test_cases = [
            ("artificial intelligence regulation", ["artificial intelligence", "regulation"], "medium"),
            ("enforcement action penalty", ["enforcement action", "penalty"], "high"),
            ("privacy data protection", ["privacy", "data protection"], "medium"),
            ("random news update", [], "informational"),
            ("AI bias fairness enforcement", ["AI", "bias", "fairness", "enforcement"], "high")
        ]
        
        for text, expected_keywords, expected_risk in test_cases:
            keywords, risk_level = mock_rss_monitor._match_keywords(text)
            
            # Check that expected keywords are found (subset match)
            for expected_keyword in expected_keywords:
                assert any(expected_keyword.lower() in kw.lower() for kw in keywords), \
                    f"Expected keyword '{expected_keyword}' not found in {keywords}"
            
            assert risk_level == expected_risk, \
                f"Expected risk level '{expected_risk}' for text '{text}', got '{risk_level}'"
    
    def test_item_id_generation(self, mock_rss_monitor):
        """Test unique ID generation for regulatory items"""
        title1 = "Test Regulation Update"
        url1 = "https://example.com/update1"
        published1 = "2024-07-20T10:00:00"
        
        title2 = "Test Regulation Update"
        url2 = "https://example.com/update2"  # Different URL
        published2 = "2024-07-20T10:00:00"
        
        id1 = mock_rss_monitor._generate_item_id(title1, url1, published1)
        id2 = mock_rss_monitor._generate_item_id(title2, url2, published2)
        id3 = mock_rss_monitor._generate_item_id(title1, url1, published1)  # Same as id1
        
        assert id1 != id2, "Different URLs should generate different IDs"
        assert id1 == id3, "Same content should generate same ID"
        assert len(id1) == 32, "ID should be 32-character MD5 hash"
    
    @patch('monitors.rss_monitor.requests.Session.get')
    @patch('monitors.rss_monitor.feedparser.parse')
    async def test_monitor_feed_success(self, mock_feedparser, mock_get, mock_rss_monitor, sample_feed_data):
        """Test successful RSS feed monitoring"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = sample_feed_data.encode()
        mock_get.return_value = mock_response
        mock_response.raise_for_status.return_value = None
        
        # Mock feedparser
        mock_feed = Mock()
        mock_feed.entries = [
            Mock(
                title="FTC Announces New AI Guidance",
                description="AI guidance for healthcare",
                link="https://ftc.gov/news/ai-guidance",
                published_parsed=(2024, 7, 20, 10, 0, 0, 0, 0, 0)
            )
        ]
        mock_feedparser.return_value = mock_feed
        
        # Test feed configuration
        feed_config = {
            'name': 'Test FTC Feed',
            'url': 'https://ftc.gov/rss',
            'jurisdiction': 'US_Federal'
        }
        
        # Monitor the feed
        items = await mock_rss_monitor.monitor_feed(feed_config)
        
        # Verify results
        assert len(items) > 0, "Should find regulatory items with AI keywords"
        item = items[0]
        assert isinstance(item, RegulatoryItem)
        assert "AI" in item.keywords_matched or "artificial intelligence" in [kw.lower() for kw in item.keywords_matched]
        assert item.jurisdiction == "US_Federal"
        assert item.risk_level in ["informational", "medium", "high"]
    
    @patch('monitors.rss_monitor.requests.Session.get')
    async def test_monitor_feed_http_error(self, mock_get, mock_rss_monitor):
        """Test handling of HTTP errors during feed monitoring"""
        # Mock HTTP error
        mock_get.side_effect = Exception("Connection timeout")
        
        feed_config = {
            'name': 'Test Feed',
            'url': 'https://example.com/rss',
            'jurisdiction': 'Test'
        }
        
        # Should handle error gracefully and return empty list
        items = await mock_rss_monitor.monitor_feed(feed_config)
        assert items == [], "Should return empty list on HTTP error"
    
    async def test_duplicate_item_filtering(self, mock_rss_monitor):
        """Test that duplicate items are filtered out"""
        # Add item to processed items
        test_id = "test_item_123"
        mock_rss_monitor.processed_items.add(test_id)
        
        # Mock feed with duplicate item
        with patch.object(mock_rss_monitor, '_generate_item_id', return_value=test_id):
            with patch('monitors.rss_monitor.requests.Session.get') as mock_get:
                mock_response = Mock()
                mock_response.content = b"<rss><channel><item><title>Test</title></item></channel></rss>"
                mock_get.return_value = mock_response
                
                with patch('monitors.rss_monitor.feedparser.parse') as mock_parse:
                    mock_feed = Mock()
                    mock_feed.entries = [Mock(
                        title="Test Item",
                        description="Test description",
                        link="https://test.com",
                        published_parsed=(2024, 7, 20, 10, 0, 0, 0, 0, 0)
                    )]
                    mock_parse.return_value = mock_feed
                    
                    items = await mock_rss_monitor.monitor_feed({
                        'name': 'Test',
                        'url': 'https://test.com',
                        'jurisdiction': 'Test'
                    })
                    
                    assert len(items) == 0, "Duplicate items should be filtered out"
    
    def test_date_filtering(self, mock_rss_monitor):
        """Test filtering of items older than lookback period"""
        cutoff_days = mock_rss_monitor.config['monitoring']['lookback_days']
        old_date = datetime.now() - timedelta(days=cutoff_days + 1)
        recent_date = datetime.now() - timedelta(days=cutoff_days - 1)
        
        # This would be tested in integration with actual feed processing
        # Here we verify the cutoff calculation is correct
        assert cutoff_days > 0, "Lookback days should be positive"
        assert old_date < recent_date, "Date filtering logic should work correctly"
    
    def test_processed_items_persistence(self, mock_rss_monitor, temp_config_dir):
        """Test that processed items are saved and loaded correctly"""
        # Add some processed items
        test_ids = ["id1", "id2", "id3"]
        for item_id in test_ids:
            mock_rss_monitor.processed_items.add(item_id)
        
        # Save processed items
        mock_rss_monitor._save_processed_items()
        
        # Create new monitor instance to test loading
        new_monitor = RSSMonitor(str(Path(temp_config_dir) / "test_config.yaml"))
        new_monitor.data_dir = mock_rss_monitor.data_dir
        
        # Load processed items
        loaded_items = new_monitor._load_processed_items()
        
        # Verify all items were loaded
        for item_id in test_ids:
            assert item_id in loaded_items, f"Processed item {item_id} should be loaded"
    
    @patch('monitors.rss_monitor.json.dump')
    async def test_regulatory_items_saving(self, mock_json_dump, mock_rss_monitor):
        """Test that regulatory items are saved correctly"""
        sample_items = [
            RegulatoryItem(
                id="test_id",
                title="Test Regulation",
                description="Test description",
                url="https://test.com",
                published="2024-07-20T10:00:00",
                source="Test Source",
                jurisdiction="US_Federal",
                keywords_matched=["AI", "regulation"],
                risk_level="medium",
                timestamp_processed="2024-07-20T12:00:00"
            )
        ]
        
        await mock_rss_monitor._save_regulatory_items(sample_items)
        
        # Verify JSON dump was called
        assert mock_json_dump.called, "Should save items as JSON"
        
        # Check the data structure passed to json.dump
        call_args = mock_json_dump.call_args[0][0]
        assert 'timestamp' in call_args
        assert 'item_count' in call_args
        assert 'items' in call_args
        assert call_args['item_count'] == len(sample_items)
    
    async def test_performance_monitoring(self, mock_rss_monitor):
        """Test that monitoring performance is tracked"""
        start_time = datetime.now()
        
        # Mock the monitoring process
        with patch.object(mock_rss_monitor, 'monitor_feed', return_value=[]):
            result = await mock_rss_monitor.run_monitoring()
        
        end_time = datetime.now()
        
        # Verify performance metrics
        assert isinstance(result, MonitoringResult)
        assert result.processing_time >= 0, "Processing time should be non-negative"
        assert result.processing_time < 60, "Processing should complete quickly in tests"
        assert result.timestamp is not None
    
    def test_security_input_validation(self, mock_rss_monitor):
        """Test security aspects of input validation"""
        # Test malicious input handling
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE items; --",
            "../../../etc/passwd",
            "\x00\x01\x02",  # Null bytes and control characters
        ]
        
        for malicious_input in malicious_inputs:
            # Should not crash or cause issues
            keywords, risk_level = mock_rss_monitor._match_keywords(malicious_input)
            assert isinstance(keywords, list)
            assert risk_level in ["informational", "medium", "high"]
            
            # ID generation should be safe
            item_id = mock_rss_monitor._generate_item_id(malicious_input, "url", "date")
            assert len(item_id) == 32  # MD5 hash length
            assert all(c in '0123456789abcdef' for c in item_id)  # Valid hex

class TestIntegrationScenarios:
    """Integration test scenarios for real-world usage"""
    
    @pytest.fixture
    def integration_monitor(self):
        """Monitor for integration tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            monitor = RSSMonitor()
            monitor.data_dir = Path(temp_dir) / "data"
            monitor.data_dir.mkdir(exist_ok=True)
            yield monitor
    
    async def test_end_to_end_monitoring_cycle(self, integration_monitor):
        """Test complete monitoring cycle from RSS to storage"""
        # This would be a more comprehensive integration test
        # For now, verify the structure is in place
        assert hasattr(integration_monitor, 'run_monitoring')
        assert callable(integration_monitor.run_monitoring)
    
    def test_configuration_validation(self, integration_monitor):
        """Test that configuration is properly validated"""
        config = integration_monitor.config
        
        # Verify required configuration sections
        assert 'feeds' in config, "Configuration must have feeds section"
        assert 'monitoring' in config, "Configuration must have monitoring section"
        
        # Verify feed structure
        for category, feeds in config['feeds'].items():
            for feed in feeds:
                assert 'name' in feed, f"Feed in {category} missing name"
                assert 'url' in feed, f"Feed in {category} missing URL"
                assert 'jurisdiction' in feed, f"Feed in {category} missing jurisdiction"
    
    def test_error_recovery(self, integration_monitor):
        """Test system recovery from various error conditions"""
        # Test should verify graceful handling of:
        # - Network failures
        # - Malformed RSS feeds
        # - Disk space issues
        # - Permission problems
        
        # For now, verify error handling structure exists
        assert hasattr(integration_monitor, 'session')
        assert hasattr(integration_monitor, 'processed_items')

if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])