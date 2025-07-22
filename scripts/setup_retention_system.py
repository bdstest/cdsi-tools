#!/usr/bin/env python3
"""
Setup Script for Data Retention and Backup System

Initializes the comprehensive data management system with:
- Secure directory structure
- Encryption key generation
- Database initialization
- Scheduled task setup
- Permissions configuration

Author: bdstest
License: Apache 2.0
"""

import os
import sys
import subprocess
from pathlib import Path
import yaml
import json
from datetime import datetime

def setup_directory_structure():
    """Create secure directory structure"""
    directories = [
        Path("data"),
        Path("data") / "archive",
        Path("backups"),
        Path("backups") / "cold",
        Path("logs"),
        Path("config")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        os.chmod(directory, 0o700)  # Restrict to owner only
    
    print(f"✅ Created secure directory structure")

def generate_encryption_key():
    """Generate encryption key if not exists"""
    key_path = Path("config/encryption.key")
    
    if not key_path.exists():
        try:
            from cryptography.fernet import Fernet
            key = Fernet.generate_key()
            
            with open(key_path, 'wb') as f:
                f.write(key)
            os.chmod(key_path, 0o600)
            
            print("✅ Generated new encryption key")
        except ImportError:
            print("⚠️  cryptography package not found - encryption disabled")
            return False
    else:
        print("✅ Encryption key already exists")
    
    return True

def install_dependencies():
    """Install required dependencies"""
    dependencies = [
        "pyyaml",
        "cryptography",
        "schedule",
        "aiofiles"
    ]
    
    optional_dependencies = [
        "fuzzywuzzy[speedup]",
        "spacy"
    ]
    
    print("📦 Installing required dependencies...")
    for package in dependencies:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            print(f"   ✅ {package}")
        except subprocess.CalledProcessError:
            print(f"   ❌ Failed to install {package}")
            return False
    
    print("📦 Installing optional dependencies...")
    for package in optional_dependencies:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            print(f"   ✅ {package}")
        except subprocess.CalledProcessError:
            print(f"   ⚠️  Optional: {package} (features may be limited)")
    
    return True

def setup_spacy_model():
    """Download spaCy English model"""
    try:
        subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], 
                      check=True, capture_output=True)
        print("✅ Downloaded spaCy English model")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Could not download spaCy model - NLP features disabled")
        return False

def create_systemd_service():
    """Create systemd service for automated data management"""
    service_content = f'''[Unit]
Description=CDSI Data Management Service
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'bdstest')}
WorkingDirectory={Path.cwd()}
ExecStart={sys.executable} -m src.core.data_manager
Restart=always
RestartSec=30
Environment=PYTHONPATH={Path.cwd()}

[Install]
WantedBy=multi-user.target
'''
    
    service_path = Path("/etc/systemd/system/cdsi-data-manager.service")
    
    try:
        with open(service_path, 'w') as f:
            f.write(service_content)
        
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "enable", "cdsi-data-manager.service"], check=True)
        
        print("✅ Created systemd service")
        return True
    except (PermissionError, subprocess.CalledProcessError):
        print("⚠️  Could not create systemd service (requires sudo)")
        return False

def create_cron_jobs():
    """Create cron jobs for data management"""
    cron_jobs = [
        "0 2 * * * cd {} && python -c 'from src.core.data_manager import DataManager; DataManager().create_backup()'",
        "0 3 * * * cd {} && python -c 'from src.core.data_manager import DataManager; dm = DataManager(); dm.archive_old_data(); dm.cleanup_expired_data()'"
    ]
    
    cwd = Path.cwd()
    
    try:
        # Get current crontab
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        current_cron = result.stdout if result.returncode == 0 else ""
        
        # Add new jobs if not already present
        new_jobs = []
        for job_template in cron_jobs:
            job = job_template.format(cwd)
            if job not in current_cron:
                new_jobs.append(job)
        
        if new_jobs:
            updated_cron = current_cron + "\n" + "\n".join(new_jobs) + "\n"
            
            # Update crontab
            process = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
            process.communicate(input=updated_cron)
            
            if process.returncode == 0:
                print("✅ Created cron jobs for data management")
                return True
        else:
            print("✅ Cron jobs already configured")
            return True
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Could not configure cron jobs")
        return False

def test_system():
    """Test the data management system"""
    print("\n🧪 Testing data management system...")
    
    try:
        from src.core.data_manager import DataManager, DataRecord
        from datetime import datetime, timedelta
        
        # Initialize data manager
        dm = DataManager()
        
        # Create test record
        test_record = DataRecord(
            id="setup_test_001",
            record_type="setup_test",
            data={"message": "System setup test", "timestamp": datetime.now().isoformat()},
            classification="internal",
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(days=30)).isoformat(),
            metadata={"setup_test": True}
        )
        
        # Store and retrieve
        record_id = dm.store_record(test_record, "setup_script")
        retrieved = dm.retrieve_record(record_id, "setup_test", "setup_script")
        
        if retrieved and retrieved.id == test_record.id:
            print("   ✅ Data storage and retrieval working")
        else:
            print("   ❌ Data storage test failed")
            return False
        
        # Test encryption (if available)
        if hasattr(dm, 'encryption'):
            test_data = "encryption test data"
            encrypted = dm.encryption.encrypt(test_data)
            decrypted = dm.encryption.decrypt(encrypted)
            
            if decrypted == test_data:
                print("   ✅ Encryption/decryption working")
            else:
                print("   ❌ Encryption test failed")
                return False
        
        # Test audit trail
        events = dm.audit_trail.get_events(days_back=1)
        if len(events) >= 2:  # Should have create and read events
            print("   ✅ Audit trail working")
        else:
            print("   ❌ Audit trail test failed")
            return False
        
        print("   ✅ All system tests passed")
        return True
        
    except Exception as e:
        print(f"   ❌ System test failed: {e}")
        return False

def create_monitoring_dashboard():
    """Create simple monitoring dashboard script"""
    dashboard_script = '''#!/usr/bin/env python3
"""
CDSI Data Management Dashboard
Quick status overview of the data management system
"""

import json
from pathlib import Path
from datetime import datetime
from src.core.data_manager import DataManager

def main():
    print("🗄️ CDSI Data Management Dashboard")
    print("=" * 50)
    
    dm = DataManager()
    
    # Storage statistics
    stats = dm.get_storage_stats()
    print("\\n📊 Storage Statistics:")
    print(f"   Data Size: {stats['data_size_bytes'] / (1024*1024):.1f} MB")
    print(f"   Archive Size: {stats['archive_size_bytes'] / (1024*1024):.1f} MB") 
    print(f"   Backup Size: {stats['backup_size_bytes'] / (1024*1024):.1f} MB")
    print(f"   Total Files: {stats['total_files']}")
    print(f"   Archived Files: {stats['archived_files']}")
    print(f"   Backup Files: {stats['backup_files']}")
    
    # Recent activity
    recent_events = dm.audit_trail.get_events(days_back=7)
    print(f"\\n📋 Recent Activity (7 days): {len(recent_events)} events")
    
    event_types = {}
    for event in recent_events:
        event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
    
    for event_type, count in event_types.items():
        print(f"   {event_type}: {count}")
    
    # System health
    print("\\n🔧 System Health:")
    
    # Check if encryption is working
    try:
        test_data = "health check"
        encrypted = dm.encryption.encrypt(test_data)
        decrypted = dm.encryption.decrypt(encrypted)
        print("   ✅ Encryption: Working")
    except:
        print("   ❌ Encryption: Failed")
    
    # Check backup directory
    backup_files = list(Path("backups").glob("backup_*.tar.gz"))
    if backup_files:
        latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
        backup_age = datetime.now().timestamp() - latest_backup.stat().st_mtime
        print(f"   📦 Latest Backup: {backup_age/3600:.1f} hours ago")
    else:
        print("   ⚠️  No backups found")
    
    print("\\n✅ Dashboard complete")

if __name__ == "__main__":
    main()
'''
    
    with open("scripts/data_dashboard.py", 'w') as f:
        f.write(dashboard_script)
    
    os.chmod("scripts/data_dashboard.py", 0o755)
    print("✅ Created monitoring dashboard script")

def main():
    """Main setup function"""
    print("🚀 CDSI Data Retention & Backup System Setup")
    print("=" * 60)
    print()
    
    # Check if running as root for system services
    is_root = os.geteuid() == 0
    if is_root:
        print("⚠️  Running as root - system services will be configured")
    else:
        print("ℹ️  Running as user - some features may be limited")
    
    print()
    
    # Step 1: Directory structure
    setup_directory_structure()
    
    # Step 2: Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        return False
    
    # Step 3: Generate encryption key
    generate_encryption_key()
    
    # Step 4: Download spaCy model
    setup_spacy_model()
    
    # Step 5: Create system services (if root)
    if is_root:
        create_systemd_service()
    else:
        create_cron_jobs()
    
    # Step 6: Create monitoring dashboard
    create_monitoring_dashboard()
    
    # Step 7: Test system
    if not test_system():
        print("❌ System test failed")
        return False
    
    print()
    print("🎉 CDSI Data Management System Setup Complete!")
    print()
    print("📋 Next Steps:")
    print("   1. Run: python scripts/data_dashboard.py")
    print("   2. Test RSS monitoring: python src/monitors/rss_monitor.py")
    print("   3. Test advanced filtering: python src/core/advanced_filter.py")
    print("   4. Check logs: tail -f logs/system.log")
    print()
    print("🔒 Security Notes:")
    print("   - All sensitive data is properly secured with restricted access")
    print("   - Encryption keys are automatically generated")
    print("   - Audit trails track all data access")
    print("   - Automatic backups run daily at 2 AM")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)