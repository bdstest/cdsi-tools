#!/usr/bin/env python3
"""
SIEM Integration Connector for CDSI - DRAFT
Real-time compliance event streaming to Security Information and Event Management systems

Contact: consulting@getcdsi.com
Website: getcdsi.com
"""

import json
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import hmac

class SIEMProvider(str, Enum):
    SPLUNK = "splunk"
    ELASTIC = "elastic"
    QRADAR = "qradar"
    SENTINEL = "sentinel"
    SUMOLOGIC = "sumologic"
    GENERIC = "generic"

class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class ComplianceEvent:
    """Represents a compliance event for SIEM ingestion"""
    event_id: str
    timestamp: datetime
    source: str
    severity: AlertSeverity
    event_type: str
    title: str
    description: str
    affected_resources: List[str]
    compliance_frameworks: List[str]
    risk_score: float
    remediation: str
    raw_data: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

@dataclass
class SIEMConfig:
    """SIEM connection configuration"""
    provider: SIEMProvider
    endpoint_url: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    index_name: Optional[str] = None
    source_type: Optional[str] = None
    verify_ssl: bool = True
    timeout: int = 30
    batch_size: int = 100
    webhook_secret: Optional[str] = None

class SIEMConnector:
    """Universal SIEM connector for compliance events"""
    
    def __init__(self, config: SIEMConfig):
        self.config = config
        self.session = None
        self.event_queue = asyncio.Queue()
        self.running = False
        
        # Setup logging
        self.logger = logging.getLogger(f"siem_connector_{config.provider}")
        
    async def start(self):
        """Start the SIEM connector"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            connector=aiohttp.TCPConnector(ssl=self.config.verify_ssl)
        )
        self.running = True
        
        # Start background event processor
        asyncio.create_task(self._process_event_queue())
        
        self.logger.info(f"SIEM connector started for {self.config.provider}")
    
    async def stop(self):
        """Stop the SIEM connector"""
        self.running = False
        if self.session:
            await self.session.close()
        self.logger.info("SIEM connector stopped")
    
    async def send_event(self, event: ComplianceEvent) -> bool:
        """Send compliance event to SIEM"""
        try:
            # Add to queue for batch processing
            await self.event_queue.put(event)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to queue event {event.event_id}: {e}")
            return False
    
    async def send_batch(self, events: List[ComplianceEvent]) -> bool:
        """Send batch of events to SIEM"""
        if not events:
            return True
            
        try:
            formatted_events = [self._format_event_for_siem(event) for event in events]
            
            if self.config.provider == SIEMProvider.SPLUNK:
                return await self._send_to_splunk(formatted_events)
            elif self.config.provider == SIEMProvider.ELASTIC:
                return await self._send_to_elastic(formatted_events)
            elif self.config.provider == SIEMProvider.QRADAR:
                return await self._send_to_qradar(formatted_events)
            elif self.config.provider == SIEMProvider.SENTINEL:
                return await self._send_to_sentinel(formatted_events)
            elif self.config.provider == SIEMProvider.SUMOLOGIC:
                return await self._send_to_sumologic(formatted_events)
            else:
                return await self._send_generic(formatted_events)
                
        except Exception as e:
            self.logger.error(f"Failed to send batch of {len(events)} events: {e}")
            return False
    
    def _format_event_for_siem(self, event: ComplianceEvent) -> Dict[str, Any]:
        """Format compliance event for SIEM ingestion"""
        base_event = {
            "timestamp": event.timestamp.isoformat(),
            "event_id": event.event_id,
            "source": event.source,
            "severity": event.severity.value,
            "event_type": event.event_type,
            "title": event.title,
            "description": event.description,
            "affected_resources": event.affected_resources,
            "compliance_frameworks": event.compliance_frameworks,
            "risk_score": event.risk_score,
            "remediation": event.remediation,
            "cdsi_version": "1.0.0",
            "vendor": "CDSI",
            "product": "Compliance Data Systems Insights"
        }
        
        # Add optional fields
        if event.tags:
            base_event["tags"] = event.tags
        
        if event.raw_data:
            base_event["raw_data"] = event.raw_data
        
        # Provider-specific formatting
        if self.config.provider == SIEMProvider.SPLUNK:
            return self._format_for_splunk(base_event)
        elif self.config.provider == SIEMProvider.ELASTIC:
            return self._format_for_elastic(base_event)
        elif self.config.provider == SIEMProvider.QRADAR:
            return self._format_for_qradar(base_event)
        elif self.config.provider == SIEMProvider.SENTINEL:
            return self._format_for_sentinel(base_event)
        elif self.config.provider == SIEMProvider.SUMOLOGIC:
            return self._format_for_sumologic(base_event)
        else:
            return base_event
    
    def _format_for_splunk(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Format event for Splunk HEC"""
        return {
            "time": event["timestamp"],
            "source": "cdsi_compliance",
            "sourcetype": self.config.source_type or "cdsi:compliance:event",
            "index": self.config.index_name or "compliance",
            "event": event
        }
    
    def _format_for_elastic(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Format event for Elasticsearch"""
        event["@timestamp"] = event["timestamp"]
        event["log_type"] = "compliance_event"
        return event
    
    def _format_for_qradar(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Format event for IBM QRadar"""
        return {
            "LogSourceName": "CDSI Compliance Monitor",
            "EventTime": event["timestamp"],
            "EventCategory": "Compliance Violation",
            "Severity": event["severity"],
            "Message": f"{event['title']}: {event['description']}",
            "Properties": event
        }
    
    def _format_for_sentinel(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Format event for Microsoft Sentinel"""
        event["TimeGenerated"] = event["timestamp"]
        event["Computer"] = "CDSI-Monitor"
        event["Type"] = "ComplianceEvent_CL"
        return event
    
    def _format_for_sumologic(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Format event for Sumo Logic"""
        return {
            "timestamp": event["timestamp"],
            "category": "compliance",
            "fields": event
        }
    
    async def _send_to_splunk(self, events: List[Dict[str, Any]]) -> bool:
        """Send events to Splunk HEC"""
        try:
            headers = {
                "Authorization": f"Splunk {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            # Splunk HEC expects newline-delimited JSON
            payload = "\n".join(json.dumps(event) for event in events)
            
            async with self.session.post(
                f"{self.config.endpoint_url}/services/collector/event",
                headers=headers,
                data=payload
            ) as response:
                if response.status == 200:
                    self.logger.info(f"Successfully sent {len(events)} events to Splunk")
                    return True
                else:
                    self.logger.error(f"Splunk returned status {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to send to Splunk: {e}")
            return False
    
    async def _send_to_elastic(self, events: List[Dict[str, Any]]) -> bool:
        """Send events to Elasticsearch"""
        try:
            headers = {"Content-Type": "application/x-ndjson"}
            
            if self.config.api_key:
                headers["Authorization"] = f"ApiKey {self.config.api_key}"
            elif self.config.username and self.config.password:
                auth = aiohttp.BasicAuth(self.config.username, self.config.password)
            else:
                auth = None
            
            # Elasticsearch bulk format
            bulk_data = []
            for event in events:
                index_meta = {"index": {"_index": self.config.index_name or "compliance"}}
                bulk_data.append(json.dumps(index_meta))
                bulk_data.append(json.dumps(event))
            
            payload = "\n".join(bulk_data) + "\n"
            
            async with self.session.post(
                f"{self.config.endpoint_url}/_bulk",
                headers=headers,
                data=payload,
                auth=auth if 'auth' in locals() else None
            ) as response:
                if response.status == 200:
                    self.logger.info(f"Successfully sent {len(events)} events to Elasticsearch")
                    return True
                else:
                    self.logger.error(f"Elasticsearch returned status {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to send to Elasticsearch: {e}")
            return False
    
    async def _send_to_qradar(self, events: List[Dict[str, Any]]) -> bool:
        """Send events to IBM QRadar"""
        try:
            headers = {
                "SEC": self.config.api_key,
                "Content-Type": "application/json"
            }
            
            payload = json.dumps(events)
            
            async with self.session.post(
                f"{self.config.endpoint_url}/api/siem/events",
                headers=headers,
                data=payload
            ) as response:
                if response.status in [200, 201]:
                    self.logger.info(f"Successfully sent {len(events)} events to QRadar")
                    return True
                else:
                    self.logger.error(f"QRadar returned status {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to send to QRadar: {e}")
            return False
    
    async def _send_to_sentinel(self, events: List[Dict[str, Any]]) -> bool:
        """Send events to Microsoft Sentinel"""
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = json.dumps(events)
            
            async with self.session.post(
                f"{self.config.endpoint_url}/api/logs",
                headers=headers,
                data=payload
            ) as response:
                if response.status == 200:
                    self.logger.info(f"Successfully sent {len(events)} events to Sentinel")
                    return True
                else:
                    self.logger.error(f"Sentinel returned status {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to send to Sentinel: {e}")
            return False
    
    async def _send_to_sumologic(self, events: List[Dict[str, Any]]) -> bool:
        """Send events to Sumo Logic"""
        try:
            headers = {"Content-Type": "application/json"}
            
            # Sumo Logic HTTP Source expects individual JSON objects
            payload = "\n".join(json.dumps(event) for event in events)
            
            async with self.session.post(
                self.config.endpoint_url,  # HTTP Source URL
                headers=headers,
                data=payload
            ) as response:
                if response.status == 200:
                    self.logger.info(f"Successfully sent {len(events)} events to Sumo Logic")
                    return True
                else:
                    self.logger.error(f"Sumo Logic returned status {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to send to Sumo Logic: {e}")
            return False
    
    async def _send_generic(self, events: List[Dict[str, Any]]) -> bool:
        """Send events to generic webhook endpoint"""
        try:
            headers = {"Content-Type": "application/json"}
            
            # Add HMAC signature if webhook secret is configured
            if self.config.webhook_secret:
                payload = json.dumps(events)
                signature = hmac.new(
                    self.config.webhook_secret.encode(),
                    payload.encode(),
                    hashlib.sha256
                ).hexdigest()
                headers["X-CDSI-Signature"] = f"sha256={signature}"
            else:
                payload = json.dumps(events)
            
            async with self.session.post(
                self.config.endpoint_url,
                headers=headers,
                data=payload
            ) as response:
                if response.status in [200, 201, 202]:
                    self.logger.info(f"Successfully sent {len(events)} events to generic endpoint")
                    return True
                else:
                    self.logger.error(f"Generic endpoint returned status {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to send to generic endpoint: {e}")
            return False
    
    async def _process_event_queue(self):
        """Process queued events in batches"""
        while self.running:
            try:
                events = []
                
                # Collect events up to batch size or timeout
                timeout_task = asyncio.create_task(asyncio.sleep(5))  # 5 second batch timeout
                
                while len(events) < self.config.batch_size and not timeout_task.done():
                    try:
                        event = await asyncio.wait_for(self.event_queue.get(), timeout=0.1)
                        events.append(event)
                    except asyncio.TimeoutError:
                        continue
                
                timeout_task.cancel()
                
                if events:
                    await self.send_batch(events)
                    
            except Exception as e:
                self.logger.error(f"Error in event queue processor: {e}")
                await asyncio.sleep(1)

class ComplianceEventGenerator:
    """Generate compliance events for testing and monitoring"""
    
    @staticmethod
    def create_pii_detection_event(file_path: str, pii_count: int, confidence: float) -> ComplianceEvent:
        """Create PII detection event"""
        severity = AlertSeverity.HIGH if confidence > 0.8 else AlertSeverity.MEDIUM
        
        return ComplianceEvent(
            event_id=f"pii_detection_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.utcnow(),
            source="CDSI PII Scanner",
            severity=severity,
            event_type="pii_detection",
            title="Personal Information Detected",
            description=f"Found {pii_count} instances of PII in {file_path}",
            affected_resources=[file_path],
            compliance_frameworks=["GDPR", "CCPA", "HIPAA"],
            risk_score=confidence * 10,
            remediation="Review and classify detected PII, implement appropriate protection",
            tags=["pii", "data_protection", "privacy"]
        )
    
    @staticmethod
    def create_compliance_violation_event(framework: str, control: str, resource: str) -> ComplianceEvent:
        """Create compliance violation event"""
        return ComplianceEvent(
            event_id=f"violation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.utcnow(),
            source="CDSI Compliance Monitor",
            severity=AlertSeverity.HIGH,
            event_type="compliance_violation",
            title=f"{framework} Compliance Violation",
            description=f"Control {control} violation detected on {resource}",
            affected_resources=[resource],
            compliance_frameworks=[framework],
            risk_score=8.5,
            remediation=f"Implement {framework} control {control} requirements",
            tags=["compliance", "violation", framework.lower()]
        )

async def main():
    """Test SIEM connector functionality"""
    print("CDSI SIEM Connector - DRAFT VERSION")
    print("=" * 50)
    
    # Example configuration for different SIEM providers
    configs = {
        "splunk": SIEMConfig(
            provider=SIEMProvider.SPLUNK,
            endpoint_url="https://splunk.example.com:8088",
            api_key="your-hec-token",
            index_name="compliance",
            source_type="cdsi:compliance"
        ),
        "elastic": SIEMConfig(
            provider=SIEMProvider.ELASTIC,
            endpoint_url="https://elasticsearch.example.com:9200",
            api_key="your-api-key",
            index_name="compliance-events"
        )
    }
    
    # Test with generic webhook
    config = SIEMConfig(
        provider=SIEMProvider.GENERIC,
        endpoint_url="https://webhook.example.com/compliance",
        webhook_secret="your-webhook-secret"
    )
    
    connector = SIEMConnector(config)
    await connector.start()
    
    # Generate test events
    test_events = [
        ComplianceEventGenerator.create_pii_detection_event(
            "/data/customers.csv", 150, 0.95
        ),
        ComplianceEventGenerator.create_compliance_violation_event(
            "GDPR", "Article 32", "database-server-01"
        )
    ]
    
    # Send events
    for event in test_events:
        success = await connector.send_event(event)
        print(f"Event {event.event_id}: {'✓' if success else '✗'}")
    
    # Wait for batch processing
    await asyncio.sleep(6)
    
    await connector.stop()
    print("Contact consulting@getcdsi.com for SIEM integration setup")

if __name__ == "__main__":
    asyncio.run(main())