#!/usr/bin/env python3
"""
Data Management System with Retention, Backup, and Audit Trail

Handles secure storage, automated retention policies, backup management,
and comprehensive audit logging for compliance monitoring data.

Features:
- Automated data retention and archival
- Encrypted backup system
- Comprehensive audit trails
- Storage tier management
- Performance monitoring

Author: bdstest
License: Apache 2.0
"""

import os
import json
import gzip
import shutil
import sqlite3
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import asyncio
import aiofiles
from cryptography.fernet import Fernet
import schedule
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataRecord:
    """Structured data record for storage"""
    id: str
    record_type: str
    data: Dict[str, Any]
    classification: str  # public, internal, confidential, restricted
    created_at: str
    expires_at: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class AuditEvent:
    """Audit event record"""
    event_id: str
    timestamp: str
    event_type: str  # create, read, update, delete, archive, backup
    user_id: str
    resource_id: str
    resource_type: str
    action_details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class EncryptionManager:
    """Handle data encryption and decryption"""
    
    def __init__(self, key_path: str = "config/encryption.key"):
        self.key_path = Path(key_path)
        self.key = self._load_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _load_or_create_key(self) -> bytes:
        """Load existing encryption key or create new one"""
        if self.key_path.exists():
            with open(self.key_path, 'rb') as f:
                return f.read()
        else:
            # Create new key
            key = Fernet.generate_key()
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.key_path, 'wb') as f:
                f.write(key)
            os.chmod(self.key_path, 0o600)  # Restrict access
            return key
    
    def encrypt(self, data: str) -> bytes:
        """Encrypt string data"""
        return self.cipher.encrypt(data.encode())
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt data back to string"""
        return self.cipher.decrypt(encrypted_data).decode()

class AuditTrailManager:
    """Manage comprehensive audit trails"""
    
    def __init__(self, db_path: str = "data/audit_trail.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize audit trail database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    action_details TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON audit_events(timestamp)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_resource 
                ON audit_events(resource_id, resource_type)
            ''')
    
    def log_event(self, event: AuditEvent):
        """Log audit event"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO audit_events 
                (event_id, timestamp, event_type, user_id, resource_id, 
                 resource_type, action_details, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id,
                event.timestamp,
                event.event_type,
                event.user_id,
                event.resource_id,
                event.resource_type,
                json.dumps(event.action_details),
                event.ip_address,
                event.user_agent
            ))
    
    def get_events(self, resource_id: Optional[str] = None, 
                   event_type: Optional[str] = None,
                   days_back: int = 30) -> List[AuditEvent]:
        """Retrieve audit events with filtering"""
        query = '''
            SELECT * FROM audit_events 
            WHERE timestamp >= ?
        '''
        params = [(datetime.now() - timedelta(days=days_back)).isoformat()]
        
        if resource_id:
            query += ' AND resource_id = ?'
            params.append(resource_id)
        
        if event_type:
            query += ' AND event_type = ?'
            params.append(event_type)
        
        query += ' ORDER BY timestamp DESC'
        
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()
            
        events = []
        for row in rows:
            events.append(AuditEvent(
                event_id=row[0],
                timestamp=row[1],
                event_type=row[2],
                user_id=row[3],
                resource_id=row[4],
                resource_type=row[5],
                action_details=json.loads(row[6]),
                ip_address=row[7],
                user_agent=row[8]
            ))
        
        return events

class DataManager:
    """Comprehensive data management system"""
    
    def __init__(self, config_path: str = "config/data_retention.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_retention_config()
        
        # Initialize components
        self.base_path = Path("data")
        self.data_path = self.base_path
        self.backup_path = Path("backups")
        self.archive_path = self.data_path / "archive"
        
        # Create directories
        for path in [self.data_path, self.backup_path, self.archive_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Initialize managers
        self.encryption = EncryptionManager()
        self.audit_trail = AuditTrailManager()
        
        # Start background tasks
        self._start_background_tasks()
        
        logger.info("Data Manager initialized with automated retention and backup")
    
    def _load_retention_config(self) -> Dict:
        """Load data retention configuration"""
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except (FileNotFoundError, ImportError):
            return self._get_default_retention_config()
    
    def _get_default_retention_config(self) -> Dict:
        """Default retention configuration"""
        return {
            'retention_policies': {
                'rss_feed_data': {'retention_days': 365},
                'processing_logs': {'retention_days': 180},
                'audit_trails': {'retention_days': 2555},
                'pattern_matches': {'retention_days': 545}
            },
            'backup_config': {
                'enabled': True,
                'backup_frequency': 'daily',
                'retention_copies': 30
            }
        }
    
    def store_record(self, record: DataRecord, user_id: str = "system") -> str:
        """Store data record with audit trail"""
        record_id = record.id
        file_path = self._get_storage_path(record.record_type, record_id)
        
        # Prepare data for storage
        storage_data = {
            'record': asdict(record),
            'stored_at': datetime.now().isoformat(),
            'checksum': self._calculate_checksum(json.dumps(asdict(record)))
        }
        
        # Encrypt sensitive data
        if record.classification in ['confidential', 'restricted']:
            data_json = json.dumps(storage_data, indent=2)
            encrypted_data = self.encryption.encrypt(data_json)
            
            with open(file_path.with_suffix('.enc'), 'wb') as f:
                f.write(encrypted_data)
        else:
            with open(file_path.with_suffix('.json'), 'w') as f:
                json.dump(storage_data, f, indent=2, ensure_ascii=False)
        
        # Log audit event
        self.audit_trail.log_event(AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.now().isoformat(),
            event_type="create",
            user_id=user_id,
            resource_id=record_id,
            resource_type=record.record_type,
            action_details={
                'classification': record.classification,
                'file_path': str(file_path),
                'encrypted': record.classification in ['confidential', 'restricted']
            }
        ))
        
        logger.info(f"Stored record {record_id} ({record.record_type})")
        return record_id
    
    def retrieve_record(self, record_id: str, record_type: str, 
                       user_id: str = "system") -> Optional[DataRecord]:
        """Retrieve data record with audit trail"""
        file_path = self._get_storage_path(record_type, record_id)
        
        # Try encrypted file first
        encrypted_path = file_path.with_suffix('.enc')
        json_path = file_path.with_suffix('.json')
        
        storage_data = None
        
        if encrypted_path.exists():
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            decrypted_json = self.encryption.decrypt(encrypted_data)
            storage_data = json.loads(decrypted_json)
        elif json_path.exists():
            with open(json_path, 'r') as f:
                storage_data = json.load(f)
        else:
            return None
        
        # Verify checksum
        record_data = storage_data['record']
        expected_checksum = storage_data.get('checksum')
        actual_checksum = self._calculate_checksum(json.dumps(record_data))
        
        if expected_checksum and expected_checksum != actual_checksum:
            logger.error(f"Checksum mismatch for record {record_id}")
            return None
        
        # Log audit event
        self.audit_trail.log_event(AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.now().isoformat(),
            event_type="read",
            user_id=user_id,
            resource_id=record_id,
            resource_type=record_type,
            action_details={'file_path': str(file_path)}
        ))
        
        # Convert back to DataRecord
        return DataRecord(**record_data)
    
    def archive_old_data(self, user_id: str = "system"):
        """Archive data based on retention policies"""
        logger.info("Starting data archival process")
        archived_count = 0
        
        retention_policies = self.config.get('retention_policies', {})
        
        for data_type, policy in retention_policies.items():
            archive_days = policy.get('archive_after_days', 90)
            cutoff_date = datetime.now() - timedelta(days=archive_days)
            
            # Find files to archive
            pattern = f"*_{data_type}_*.json"
            for file_path in self.data_path.glob(pattern):
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    # Move to archive
                    archive_path = self.archive_path / file_path.name
                    shutil.move(str(file_path), str(archive_path))
                    
                    # Compress if configured
                    if policy.get('compression', True):
                        self._compress_file(archive_path)
                    
                    archived_count += 1
                    
                    # Log audit event
                    self.audit_trail.log_event(AuditEvent(
                        event_id=self._generate_event_id(),
                        timestamp=datetime.now().isoformat(),
                        event_type="archive",
                        user_id=user_id,
                        resource_id=file_path.stem,
                        resource_type=data_type,
                        action_details={
                            'original_path': str(file_path),
                            'archive_path': str(archive_path)
                        }
                    ))
        
        logger.info(f"Archived {archived_count} files")
        return archived_count
    
    def create_backup(self, user_id: str = "system") -> str:
        """Create comprehensive backup"""
        backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.backup_path / f"backup_{backup_timestamp}"
        backup_dir.mkdir(exist_ok=True)
        
        # Backup data directory
        data_backup = backup_dir / "data"
        shutil.copytree(self.data_path, data_backup, dirs_exist_ok=True)
        
        # Backup configuration
        config_backup = backup_dir / "config"
        shutil.copytree(self.base_path / "config", config_backup, dirs_exist_ok=True)
        
        # Create backup manifest
        manifest = {
            'backup_timestamp': backup_timestamp,
            'created_by': user_id,
            'data_files_count': len(list(data_backup.rglob('*'))),
            'total_size_bytes': sum(f.stat().st_size for f in data_backup.rglob('*') if f.is_file())
        }
        
        with open(backup_dir / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Compress backup
        backup_archive = f"{backup_dir}.tar.gz"
        shutil.make_archive(str(backup_dir), 'gztar', str(backup_dir))
        shutil.rmtree(backup_dir)
        
        # Log audit event
        self.audit_trail.log_event(AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.now().isoformat(),
            event_type="backup",
            user_id=user_id,
            resource_id=backup_timestamp,
            resource_type="full_backup",
            action_details={
                'backup_file': backup_archive,
                'files_count': manifest['data_files_count'],
                'total_size': manifest['total_size_bytes']
            }
        ))
        
        logger.info(f"Created backup: {backup_archive}")
        return backup_archive
    
    def cleanup_expired_data(self, user_id: str = "system"):
        """Clean up expired data based on retention policies"""
        logger.info("Starting data cleanup process")
        cleaned_count = 0
        
        retention_policies = self.config.get('retention_policies', {})
        
        for data_type, policy in retention_policies.items():
            retention_days = policy.get('retention_days', 365)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Clean archived files
            pattern = f"*_{data_type}_*"
            for file_path in self.archive_path.glob(pattern):
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    file_path.unlink()
                    cleaned_count += 1
                    
                    # Log audit event
                    self.audit_trail.log_event(AuditEvent(
                        event_id=self._generate_event_id(),
                        timestamp=datetime.now().isoformat(),
                        event_type="delete",
                        user_id=user_id,
                        resource_id=file_path.stem,
                        resource_type=data_type,
                        action_details={'deleted_path': str(file_path)}
                    ))
        
        logger.info(f"Cleaned up {cleaned_count} expired files")
        return cleaned_count
    
    def _get_storage_path(self, record_type: str, record_id: str) -> Path:
        """Generate storage path for record"""
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{timestamp}_{record_type}_{record_id}"
        return self.data_path / filename
    
    def _calculate_checksum(self, data: str) -> str:
        """Calculate SHA-256 checksum"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return f"evt_{timestamp}"
    
    def _compress_file(self, file_path: Path):
        """Compress file using gzip"""
        with open(file_path, 'rb') as f_in:
            with gzip.open(f"{file_path}.gz", 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        file_path.unlink()  # Remove original
    
    def _start_background_tasks(self):
        """Start scheduled background tasks"""
        if not self.config.get('backup_config', {}).get('enabled', True):
            return
        
        # Schedule daily backup
        schedule.every().day.at("02:00").do(self.create_backup)
        
        # Schedule daily cleanup
        schedule.every().day.at("03:00").do(self.cleanup_expired_data)
        schedule.every().day.at("03:30").do(self.archive_old_data)
        
        # Start scheduler in background thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("Background data management tasks started")
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        def get_dir_size(path: Path) -> int:
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        
        return {
            'data_size_bytes': get_dir_size(self.data_path),
            'archive_size_bytes': get_dir_size(self.archive_path),
            'backup_size_bytes': get_dir_size(self.backup_path),
            'total_files': len(list(self.data_path.rglob('*'))),
            'archived_files': len(list(self.archive_path.rglob('*'))),
            'backup_files': len(list(self.backup_path.glob('backup_*.tar.gz')))
        }

def main():
    """Test data management system"""
    data_manager = DataManager()
    
    # Test record storage
    test_record = DataRecord(
        id="test_001",
        record_type="rss_feed_data",
        data={"title": "Test RSS Item", "content": "Sample content"},
        classification="internal",
        created_at=datetime.now().isoformat(),
        expires_at=(datetime.now() + timedelta(days=90)).isoformat(),
        metadata={"source": "test", "risk_level": "low"}
    )
    
    print("🗄️ Data Management System Test")
    print("-" * 40)
    
    # Store record
    record_id = data_manager.store_record(test_record, "test_user")
    print(f"Stored record: {record_id}")
    
    # Retrieve record
    retrieved = data_manager.retrieve_record(record_id, "rss_feed_data", "test_user")
    print(f"Retrieved record: {retrieved.id if retrieved else 'Not found'}")
    
    # Get storage stats
    stats = data_manager.get_storage_stats()
    print(f"Storage stats: {stats}")
    
    # Get recent audit events
    events = data_manager.audit_trail.get_events(days_back=1)
    print(f"Recent audit events: {len(events)}")

if __name__ == "__main__":
    import time
    main()