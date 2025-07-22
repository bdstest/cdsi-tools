#!/usr/bin/env python3
"""
CDSI Free Tier Restrictions & Enforcement

Implements comprehensive free tier limitations based on documented strategy.
Provides upgrade prompts and enforcement mechanisms.

Features:
- File scanning limits (10K files)
- User limits (5 users)
- Device limits (15 devices)
- Single jurisdiction enforcement
- API rate limiting
- Storage restrictions
- Upgrade pathway integration

Author: bdstest
License: Apache 2.0
Copyright: 2025 CDSI - Compliance Data Systems Insights
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .heuristics_engine import TierLevel

# Configure logging
logger = logging.getLogger(__name__)

class LimitType(Enum):
    """Types of free tier limits"""
    FILES_SCANNED = "files_scanned"
    USERS = "users"
    DEVICES = "devices"
    API_CALLS = "api_calls"
    STORAGE = "storage"
    JURISDICTIONS = "jurisdictions"
    RETENTION_DAYS = "retention_days"

class UpgradeReason(Enum):
    """Reasons for upgrade prompts"""
    LIMIT_EXCEEDED = "limit_exceeded"
    FEATURE_RESTRICTED = "feature_restricted"
    USAGE_THRESHOLD = "usage_threshold"
    PREMIUM_FEATURE = "premium_feature"

@dataclass
class FreeTierLimits:
    """Free tier limitations based on documented strategy"""
    files_per_month: int = 10000  # 10K file scans per month
    max_users: int = 5  # Maximum 5 users
    max_devices: int = 15  # Maximum 15 devices
    api_calls_per_day: int = 1000  # API rate limit
    storage_mb: int = 100  # 100MB storage
    jurisdictions: int = 1  # Single jurisdiction only
    retention_days: int = 30  # 30-day data retention
    support_level: str = "community"  # Community support only
    reporting_features: List[str] = None  # Limited reporting
    
    def __post_init__(self):
        if self.reporting_features is None:
            self.reporting_features = ["basic_summary", "csv_export"]

@dataclass 
class UsageMetrics:
    """Current usage tracking for free tier"""
    files_scanned_this_month: int = 0
    active_users: int = 0
    registered_devices: int = 0
    api_calls_today: int = 0
    storage_used_mb: float = 0.0
    active_jurisdictions: int = 0
    oldest_data_days: int = 0
    last_reset: str = ""

class FreeTierEnforcer:
    """
    Enforces free tier restrictions and provides upgrade prompts
    
    Implements the documented free tier strategy:
    - 10K file scans per month
    - 5 users maximum
    - 15 devices maximum
    - Single jurisdiction
    - Community support only
    """
    
    def __init__(self):
        self.limits = FreeTierLimits()
        self.current_usage = UsageMetrics()
        self.upgrade_prompts_shown = set()
        self.last_metrics_update = datetime.now()
        
        logger.info("Free Tier Enforcer initialized")
    
    def check_limit(self, limit_type: LimitType, requested_amount: int = 1) -> Tuple[bool, str]:
        """
        Check if a requested action would exceed free tier limits
        
        Args:
            limit_type: Type of limit to check
            requested_amount: Amount being requested (default: 1)
            
        Returns:
            Tuple of (allowed: bool, message: str)
        """
        try:
            if limit_type == LimitType.FILES_SCANNED:
                new_total = self.current_usage.files_scanned_this_month + requested_amount
                if new_total > self.limits.files_per_month:
                    return False, f"Monthly file scanning limit ({self.limits.files_per_month:,}) would be exceeded. Current: {self.current_usage.files_scanned_this_month:,}"
                
                # Show warning at 80% usage
                if new_total >= (self.limits.files_per_month * 0.8):
                    self._show_upgrade_prompt(UpgradeReason.USAGE_THRESHOLD, limit_type)
                
                return True, "Within file scanning limits"
            
            elif limit_type == LimitType.USERS:
                if self.current_usage.active_users >= self.limits.max_users:
                    return False, f"Maximum user limit ({self.limits.max_users}) reached. Upgrade to add more users."
                return True, "Within user limits"
            
            elif limit_type == LimitType.DEVICES:
                new_total = self.current_usage.registered_devices + requested_amount
                if new_total > self.limits.max_devices:
                    return False, f"Maximum device limit ({self.limits.max_devices}) would be exceeded. Current: {self.current_usage.registered_devices}"
                return True, "Within device limits"
            
            elif limit_type == LimitType.API_CALLS:
                new_total = self.current_usage.api_calls_today + requested_amount
                if new_total > self.limits.api_calls_per_day:
                    return False, f"Daily API limit ({self.limits.api_calls_per_day:,}) would be exceeded. Current: {self.current_usage.api_calls_today:,}"
                return True, "Within API limits"
            
            elif limit_type == LimitType.STORAGE:
                if self.current_usage.storage_used_mb >= self.limits.storage_mb:
                    return False, f"Storage limit ({self.limits.storage_mb}MB) reached. Current usage: {self.current_usage.storage_used_mb:.1f}MB"
                return True, "Within storage limits"
            
            elif limit_type == LimitType.JURISDICTIONS:
                if self.current_usage.active_jurisdictions >= self.limits.jurisdictions:
                    return False, f"Free tier limited to {self.limits.jurisdictions} jurisdiction. Upgrade for multi-jurisdiction support."
                return True, "Within jurisdiction limits"
            
            elif limit_type == LimitType.RETENTION_DAYS:
                if self.current_usage.oldest_data_days > self.limits.retention_days:
                    return False, f"Data retention limited to {self.limits.retention_days} days on free tier."
                return True, "Within retention limits"
            
            else:
                return False, f"Unknown limit type: {limit_type}"
        
        except Exception as e:
            logger.error(f"Error checking limit {limit_type}: {e}")
            return False, f"Error checking limits: {str(e)}"
    
    def record_usage(self, limit_type: LimitType, amount: int = 1):
        """
        Record usage against free tier limits
        
        Args:
            limit_type: Type of usage to record
            amount: Amount of usage (default: 1)
        """
        try:
            if limit_type == LimitType.FILES_SCANNED:
                self.current_usage.files_scanned_this_month += amount
                logger.debug(f"Recorded {amount} file scans. Monthly total: {self.current_usage.files_scanned_this_month}")
            
            elif limit_type == LimitType.API_CALLS:
                self.current_usage.api_calls_today += amount
                logger.debug(f"Recorded {amount} API calls. Daily total: {self.current_usage.api_calls_today}")
            
            elif limit_type == LimitType.STORAGE:
                self.current_usage.storage_used_mb += amount
                logger.debug(f"Recorded {amount}MB storage. Total: {self.current_usage.storage_used_mb:.1f}MB")
            
            # Update last metrics update
            self.last_metrics_update = datetime.now()
            
        except Exception as e:
            logger.error(f"Error recording usage for {limit_type}: {e}")
    
    def reset_daily_limits(self):
        """Reset daily usage counters"""
        self.current_usage.api_calls_today = 0
        logger.info("Daily limits reset")
    
    def reset_monthly_limits(self):
        """Reset monthly usage counters"""
        self.current_usage.files_scanned_this_month = 0
        self.current_usage.last_reset = datetime.now().isoformat()
        logger.info("Monthly limits reset")
    
    def get_usage_summary(self) -> Dict[str, any]:
        """Get current usage summary with percentages"""
        return {
            'files_scanned': {
                'current': self.current_usage.files_scanned_this_month,
                'limit': self.limits.files_per_month,
                'percentage': (self.current_usage.files_scanned_this_month / self.limits.files_per_month) * 100,
                'remaining': self.limits.files_per_month - self.current_usage.files_scanned_this_month
            },
            'users': {
                'current': self.current_usage.active_users,
                'limit': self.limits.max_users,
                'percentage': (self.current_usage.active_users / self.limits.max_users) * 100,
                'remaining': self.limits.max_users - self.current_usage.active_users
            },
            'devices': {
                'current': self.current_usage.registered_devices,
                'limit': self.limits.max_devices,
                'percentage': (self.current_usage.registered_devices / self.limits.max_devices) * 100,
                'remaining': self.limits.max_devices - self.current_usage.registered_devices
            },
            'api_calls': {
                'current': self.current_usage.api_calls_today,
                'limit': self.limits.api_calls_per_day,
                'percentage': (self.current_usage.api_calls_today / self.limits.api_calls_per_day) * 100,
                'remaining': self.limits.api_calls_per_day - self.current_usage.api_calls_today
            },
            'storage': {
                'current': self.current_usage.storage_used_mb,
                'limit': self.limits.storage_mb,
                'percentage': (self.current_usage.storage_used_mb / self.limits.storage_mb) * 100,
                'remaining': self.limits.storage_mb - self.current_usage.storage_used_mb
            },
            'jurisdictions': {
                'current': self.current_usage.active_jurisdictions,
                'limit': self.limits.jurisdictions,
                'at_limit': self.current_usage.active_jurisdictions >= self.limits.jurisdictions
            },
            'tier': 'AWARE (Free)',
            'support_level': self.limits.support_level,
            'last_updated': self.last_metrics_update.isoformat()
        }
    
    def _show_upgrade_prompt(self, reason: UpgradeReason, limit_type: Optional[LimitType] = None):
        """
        Show upgrade prompt based on usage or feature request
        
        Args:
            reason: Reason for showing upgrade prompt
            limit_type: Which limit triggered the prompt (if applicable)
        """
        prompt_key = f"{reason.value}_{limit_type.value if limit_type else 'general'}"
        
        # Only show each prompt once per session to avoid spam
        if prompt_key in self.upgrade_prompts_shown:
            return
        
        self.upgrade_prompts_shown.add(prompt_key)
        
        upgrade_messages = {
            UpgradeReason.LIMIT_EXCEEDED: self._get_limit_exceeded_message(limit_type),
            UpgradeReason.FEATURE_RESTRICTED: self._get_feature_restricted_message(limit_type),
            UpgradeReason.USAGE_THRESHOLD: self._get_threshold_message(limit_type),
            UpgradeReason.PREMIUM_FEATURE: self._get_premium_feature_message(limit_type)
        }
        
        message = upgrade_messages.get(reason, "Consider upgrading for additional features.")
        
        logger.info(f"Upgrade prompt: {message}")
        
        # In a full implementation, this would trigger UI notifications
        # For now, we log the upgrade suggestion
    
    def _get_limit_exceeded_message(self, limit_type: Optional[LimitType]) -> str:
        """Generate limit exceeded message"""
        if limit_type == LimitType.FILES_SCANNED:
            return f"📈 You've reached your monthly limit of {self.limits.files_per_month:,} file scans. Upgrade to 🌿 BUILDER for {200000:,} files/month starting at $2,997/month."
        elif limit_type == LimitType.USERS:
            return f"👥 Maximum {self.limits.max_users} users reached. Upgrade to 🌿 BUILDER for up to 25 users and team collaboration features."
        elif limit_type == LimitType.DEVICES:
            return f"📱 Device limit of {self.limits.max_devices} reached. Upgrade to 🌿 BUILDER for 100 devices and centralized management."
        else:
            return "🚀 Upgrade to unlock higher limits and premium features."
    
    def _get_feature_restricted_message(self, limit_type: Optional[LimitType]) -> str:
        """Generate feature restricted message"""
        return "🔒 This feature is not available on the free tier. Upgrade to access advanced compliance tools and reporting."
    
    def _get_threshold_message(self, limit_type: Optional[LimitType]) -> str:
        """Generate usage threshold warning"""
        if limit_type == LimitType.FILES_SCANNED:
            remaining = self.limits.files_per_month - self.current_usage.files_scanned_this_month
            return f"⚠️ You're approaching your monthly file scanning limit. {remaining:,} scans remaining. Consider upgrading to avoid interruption."
        else:
            return "⚠️ You're approaching your usage limits. Consider upgrading for unlimited access."
    
    def _get_premium_feature_message(self, limit_type: Optional[LimitType]) -> str:
        """Generate premium feature message"""
        return "✨ This premium feature requires an upgrade. Unlock advanced compliance analytics and multi-jurisdiction support."
    
    def get_upgrade_options(self) -> List[Dict[str, any]]:
        """
        Get available upgrade options with pricing
        Based on documented progressive pricing strategy
        """
        # Year 1 pricing (72% of market rates)
        return [
            {
                'tier': 'BUILDER',
                'emoji': '🌿',
                'monthly_price': 127,
                'annual_price': 1524,  # 2 months free
                'files_per_month': 200000,
                'max_users': 25,
                'max_devices': 100,
                'jurisdictions': 3,
                'support': 'email',
                'features': [
                    'Advanced filtering algorithms',
                    'Multi-jurisdiction support',
                    'Team collaboration',
                    'Priority email support',
                    'Extended data retention (1 year)'
                ],
                'most_popular': True
            },
            {
                'tier': 'ACCELERATOR',
                'emoji': '🪴',
                'monthly_price': 400,
                'annual_price': 4800,
                'files_per_month': 1000000,
                'max_users': 100,
                'max_devices': 500,
                'jurisdictions': 10,
                'support': 'priority',
                'features': [
                    'All BUILDER features',
                    'Advanced analytics dashboard',
                    'Custom regulatory modules',
                    'API access',
                    'Priority phone support',
                    'Dedicated customer success manager'
                ]
            },
            {
                'tier': 'TRANSFORMER',
                'emoji': '🌲',
                'monthly_price': 650,
                'annual_price': 7800,
                'files_per_month': -1,  # Unlimited
                'max_users': 500,
                'max_devices': 2500,
                'jurisdictions': -1,  # All
                'support': 'premium',
                'features': [
                    'All ACCELERATOR features',
                    'Unlimited file processing',
                    'All global jurisdictions',
                    'White-label options',
                    'Advanced integrations',
                    '24/7 premium support'
                ]
            }
        ]
    
    def is_feature_available(self, feature_name: str) -> Tuple[bool, str]:
        """
        Check if a feature is available on free tier
        
        Args:
            feature_name: Name of feature to check
            
        Returns:
            Tuple of (available: bool, message: str)
        """
        free_tier_features = {
            'basic_scanning': True,
            'csv_export': True,
            'community_support': True,
            'single_jurisdiction': True,
            'basic_reporting': True,
            
            # Restricted features
            'advanced_analytics': False,
            'multi_jurisdiction': False,
            'api_access': False,
            'priority_support': False,
            'custom_modules': False,
            'team_collaboration': False,
            'white_label': False,
            'integrations': False
        }
        
        if feature_name not in free_tier_features:
            return False, f"Unknown feature: {feature_name}"
        
        available = free_tier_features[feature_name]
        
        if available:
            return True, "Feature available on free tier"
        else:
            self._show_upgrade_prompt(UpgradeReason.FEATURE_RESTRICTED)
            return False, f"Feature '{feature_name}' requires upgrade to 🌿 BUILDER or higher"

def main():
    """Test the free tier enforcement system"""
    print("🔒 CDSI Free Tier Enforcement Test")
    print("=" * 50)
    
    # Initialize enforcer
    enforcer = FreeTierEnforcer()
    
    # Test file scanning limits
    print("\n📁 Testing File Scanning Limits:")
    
    # Simulate normal usage
    for i in range(5):
        allowed, message = enforcer.check_limit(LimitType.FILES_SCANNED, 1000)
        if allowed:
            enforcer.record_usage(LimitType.FILES_SCANNED, 1000)
            print(f"  ✅ Scanned 1,000 files. Total: {enforcer.current_usage.files_scanned_this_month:,}")
        else:
            print(f"  ❌ {message}")
            break
    
    # Test approaching limit
    print("\n⚠️ Testing Limit Warnings:")
    allowed, message = enforcer.check_limit(LimitType.FILES_SCANNED, 6000)
    print(f"  Warning check: {message}")
    
    # Test user limits
    print("\n👥 Testing User Limits:")
    enforcer.current_usage.active_users = 4
    allowed, message = enforcer.check_limit(LimitType.USERS, 1)
    print(f"  Adding user: {message} ({'✅' if allowed else '❌'})")
    
    enforcer.current_usage.active_users = 5
    allowed, message = enforcer.check_limit(LimitType.USERS, 1)
    print(f"  Adding user: {message} ({'✅' if allowed else '❌'})")
    
    # Test feature availability
    print("\n🎛️ Testing Feature Availability:")
    features_to_test = ['basic_scanning', 'advanced_analytics', 'multi_jurisdiction', 'api_access']
    
    for feature in features_to_test:
        available, message = enforcer.is_feature_available(feature)
        print(f"  {feature}: {message} ({'✅' if available else '❌'})")
    
    # Show usage summary
    print("\n📊 Usage Summary:")
    summary = enforcer.get_usage_summary()
    
    for metric, data in summary.items():
        if isinstance(data, dict) and 'current' in data:
            print(f"  {metric}: {data['current']}/{data['limit']} ({data['percentage']:.1f}%)")
    
    # Show upgrade options
    print("\n🚀 Available Upgrade Options:")
    options = enforcer.get_upgrade_options()
    
    for option in options:
        popular = " (MOST POPULAR)" if option.get('most_popular') else ""
        print(f"  {option['emoji']} {option['tier']}{popular}: ${option['monthly_price']}/month")
        print(f"    Files: {option['files_per_month']:,} | Users: {option['max_users']} | Devices: {option['max_devices']}")
        print(f"    Features: {len(option['features'])} premium features")
        print()

if __name__ == "__main__":
    main()