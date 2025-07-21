#!/usr/bin/env python3
"""
Newsletter Service for AI Regulatory Watch

GDPR/CCPA compliant newsletter system for regulatory information distribution.
Provides professional regulatory intelligence with full privacy protection.

⚠️  INFORMATIONAL CONTENT ONLY - NOT LEGAL ADVICE
"""

import json
import logging
import smtplib
import uuid
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import hashlib
import re

import yaml
from jinja2 import Environment, FileSystemLoader

# Import security components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils import (
    get_secure_logger,
    get_secure_storage,
    pii_protector,
    audit_logger,
    get_rate_limiter,
    InputSanitizer
)

# Configure secure logging
logger = get_secure_logger(__name__)

@dataclass
class Subscriber:
    """GDPR-compliant subscriber data structure"""
    email: str
    subscription_id: str
    subscribed_date: str
    preferences: Dict[str, bool]
    consent_timestamp: str
    unsubscribe_token: str
    last_sent: Optional[str] = None
    status: str = "confirmed"  # pending, confirmed, unsubscribed

@dataclass
class NewsletterContent:
    """Weekly newsletter content structure"""
    week_ending: str
    priority_alerts: List[Dict]
    new_regulations: List[Dict]
    sector_updates: Dict[str, List[Dict]]
    international_updates: List[Dict]
    implementation_tips: List[Dict]

class PrivacyCompliantSubscriberManager:
    """GDPR/CCPA compliant subscriber management"""
    
    def __init__(self, data_dir: str = "data/subscribers"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.subscribers_file = self.data_dir / "subscribers.json"
        
        # Privacy settings
        self.data_retention_days = 30  # Days after unsubscribe to delete data
        self.consent_required = True
        
    def _generate_tokens(self) -> tuple[str, str]:
        """Generate subscription ID and unsubscribe token"""
        subscription_id = str(uuid.uuid4())
        unsubscribe_token = hashlib.sha256(
            f"{subscription_id}{datetime.now().isoformat()}".encode()
        ).hexdigest()
        return subscription_id, unsubscribe_token
    
    def _validate_email(self, email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def add_subscriber(self, email: str, preferences: Dict[str, bool], 
                      consent_ip: str = None) -> tuple[bool, str]:
        """
        Add new subscriber with double opt-in process
        Returns: (success, message)
        """
        if not self._validate_email(email):
            return False, "Invalid email address format"
        
        # Check if already subscribed
        existing_subscribers = self._load_subscribers()
        if email in existing_subscribers:
            return False, "Email already subscribed"
        
        # Generate tokens
        subscription_id, unsubscribe_token = self._generate_tokens()
        
        # Create subscriber record
        subscriber = Subscriber(
            email=email,
            subscription_id=subscription_id,
            subscribed_date=datetime.now().isoformat(),
            preferences=preferences,
            consent_timestamp=datetime.now().isoformat(),
            unsubscribe_token=unsubscribe_token,
            status="pending"  # Requires confirmation
        )
        
        # Save subscriber
        existing_subscribers[email] = asdict(subscriber)
        self._save_subscribers(existing_subscribers)
        
        # Send confirmation email
        self._send_confirmation_email(subscriber)
        
        logger.info(f"New subscriber pending confirmation: {email}")
        return True, "Confirmation email sent. Please check your inbox."
    
    def confirm_subscription(self, token: str) -> tuple[bool, str]:
        """Confirm subscription via double opt-in"""
        subscribers = self._load_subscribers()
        
        for email, data in subscribers.items():
            if data['unsubscribe_token'] == token and data['status'] == 'pending':
                subscribers[email]['status'] = 'confirmed'
                subscribers[email]['confirmed_date'] = datetime.now().isoformat()
                self._save_subscribers(subscribers)
                logger.info(f"Subscription confirmed: {email}")
                return True, "Subscription confirmed successfully!"
        
        return False, "Invalid or expired confirmation token"
    
    def unsubscribe(self, token: str) -> tuple[bool, str]:
        """One-click unsubscribe with data retention policy"""
        subscribers = self._load_subscribers()
        
        for email, data in subscribers.items():
            if data['unsubscribe_token'] == token:
                subscribers[email]['status'] = 'unsubscribed'
                subscribers[email]['unsubscribed_date'] = datetime.now().isoformat()
                self._save_subscribers(subscribers)
                logger.info(f"Unsubscribed: {email}")
                return True, "Successfully unsubscribed. Data will be deleted within 30 days."
        
        return False, "Invalid unsubscribe token"
    
    def get_active_subscribers(self) -> List[Subscriber]:
        """Get list of confirmed, active subscribers"""
        subscribers = self._load_subscribers()
        active = []
        
        for email, data in subscribers.items():
            if data['status'] == 'confirmed':
                active.append(Subscriber(**data))
        
        return active
    
    def cleanup_expired_data(self):
        """Remove data for subscribers past retention period"""
        subscribers = self._load_subscribers()
        cutoff_date = datetime.now() - timedelta(days=self.data_retention_days)
        
        to_delete = []
        for email, data in subscribers.items():
            if data['status'] == 'unsubscribed' and 'unsubscribed_date' in data:
                unsubscribed = datetime.fromisoformat(data['unsubscribed_date'])
                if unsubscribed < cutoff_date:
                    to_delete.append(email)
        
        for email in to_delete:
            del subscribers[email]
            logger.info(f"Deleted expired data for: {email}")
        
        if to_delete:
            self._save_subscribers(subscribers)
    
    def _load_subscribers(self) -> Dict:
        """Load subscriber data from secure storage"""
        if self.subscribers_file.exists():
            with open(self.subscribers_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_subscribers(self, subscribers: Dict):
        """Save subscriber data securely"""
        # Add metadata
        data = {
            'last_updated': datetime.now().isoformat(),
            'subscriber_count': len([s for s in subscribers.values() if s['status'] == 'confirmed']),
            'privacy_notice': 'Data processed per Privacy Policy - minimal retention, secure storage',
            'subscribers': subscribers
        }
        
        with open(self.subscribers_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Set secure file permissions
        self.subscribers_file.chmod(0o600)
    
    def _send_confirmation_email(self, subscriber: Subscriber):
        """Send double opt-in confirmation email"""
        # This would integrate with your email service
        logger.info(f"Would send confirmation email to: {subscriber.email}")
        # Implementation depends on email service provider

class NewsletterGenerator:
    """Generate professional regulatory newsletters"""
    
    def __init__(self, template_dir: str = "templates/newsletter"):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir)
        )
    
    def generate_weekly_newsletter(self, content: NewsletterContent) -> tuple[str, str]:
        """Generate HTML and text versions of newsletter"""
        
        # Load regulatory data for the week
        regulatory_data = self._load_weekly_data()
        
        # Prepare newsletter context
        context = {
            'week_ending': content.week_ending,
            'generation_date': datetime.now().strftime('%B %d, %Y'),
            'disclaimer': 'INFORMATIONAL CONTENT ONLY - NOT LEGAL ADVICE',
            'priority_alerts': content.priority_alerts,
            'new_regulations': content.new_regulations,
            'sector_updates': content.sector_updates,
            'international_updates': content.international_updates,
            'implementation_tips': content.implementation_tips,
            'professional_contact': 'bdstest@protonmail.com',
            'unsubscribe_info': 'One-click unsubscribe available in email footer'
        }
        
        # Generate HTML version
        try:
            html_template = self.jinja_env.get_template('weekly_digest.html')
            html_content = html_template.render(context)
        except:
            html_content = self._generate_fallback_html(context)
        
        # Generate text version
        try:
            text_template = self.jinja_env.get_template('weekly_digest.txt')
            text_content = text_template.render(context)
        except:
            text_content = self._generate_fallback_text(context)
        
        return html_content, text_content
    
    def _load_weekly_data(self) -> Dict:
        """Load regulatory data from monitoring results"""
        data_dir = Path("data")
        latest_file = data_dir / "latest_regulatory_items.yaml"
        
        if latest_file.exists():
            with open(latest_file, 'r') as f:
                return yaml.safe_load(f)
        return {'items': []}
    
    def _generate_fallback_html(self, context: Dict) -> str:
        """Generate simple HTML newsletter if template fails"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Regulatory Watch Newsletter</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }}
                .header {{ background-color: #1e3a8a; color: white; padding: 20px; text-align: center; }}
                .disclaimer {{ background-color: #fef3c7; padding: 15px; border-left: 4px solid #f59e0b; margin: 20px 0; }}
                .content {{ padding: 20px; }}
                .footer {{ background-color: #f3f4f6; padding: 15px; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔍 AI Regulatory Watch</h1>
                <p>Weekly Regulatory Intelligence - {context['generation_date']}</p>
            </div>
            
            <div class="disclaimer">
                <strong>⚠️ IMPORTANT:</strong> {context['disclaimer']}
            </div>
            
            <div class="content">
                <h2>📋 This Week's Updates</h2>
                <p>Professional regulatory monitoring results for week ending {context['week_ending']}</p>
                
                <h3>🚨 Priority Alerts</h3>
                <ul>
                    {''.join([f"<li>{alert.get('title', 'Alert')}</li>" for alert in context.get('priority_alerts', [])])}
                </ul>
                
                <h3>📊 New Regulations</h3>
                <ul>
                    {''.join([f"<li>{reg.get('title', 'Update')}</li>" for reg in context.get('new_regulations', [])])}
                </ul>
                
                <hr>
                <h3>💬 Need Professional Guidance?</h3>
                <p>Questions about regulatory compliance for your AI systems?</p>
                <p><strong>Contact:</strong> {context['professional_contact']}</p>
                <p><em>Professional compliance consulting available</em></p>
            </div>
            
            <div class="footer">
                <p>AI Regulatory Watch Newsletter</p>
                <p>Professional regulatory intelligence by bdstest</p>
                <p>Unsubscribe: [Unsubscribe link provided in actual email]</p>
                <p>Privacy Policy | Contact | github.com/bdstest/ai-regulatory-watch</p>
            </div>
        </body>
        </html>
        """
    
    def _generate_fallback_text(self, context: Dict) -> str:
        """Generate text newsletter if template fails"""
        return f"""
🔍 AI REGULATORY WATCH NEWSLETTER
Week ending: {context['week_ending']}
Generated: {context['generation_date']}

⚠️  IMPORTANT: {context['disclaimer']}

🚨 PRIORITY ALERTS
{chr(10).join([f"• {alert.get('title', 'Alert')}" for alert in context.get('priority_alerts', [])])}

📊 NEW REGULATIONS & GUIDANCE
{chr(10).join([f"• {reg.get('title', 'Update')}" for reg in context.get('new_regulations', [])])}

💬 PROFESSIONAL SERVICES
Need compliance guidance for your AI systems?
Contact: {context['professional_contact']}
Professional compliance consulting available.

---
AI Regulatory Watch Newsletter
Professional regulatory intelligence by bdstest
github.com/bdstest/ai-regulatory-watch

Unsubscribe: [Link provided in email]
Privacy Policy: [Link provided in email]
        """

class NewsletterService:
    """Complete newsletter service with privacy compliance"""
    
    def __init__(self):
        self.subscriber_manager = PrivacyCompliantSubscriberManager()
        self.newsletter_generator = NewsletterGenerator()
    
    def send_weekly_newsletter(self):
        """Send newsletter to all confirmed subscribers"""
        logger.info("Starting weekly newsletter distribution")
        
        # Cleanup expired subscriber data first
        self.subscriber_manager.cleanup_expired_data()
        
        # Get active subscribers
        subscribers = self.subscriber_manager.get_active_subscribers()
        if not subscribers:
            logger.info("No active subscribers for newsletter")
            return
        
        # Generate newsletter content
        content = self._prepare_newsletter_content()
        html_content, text_content = self.newsletter_generator.generate_weekly_newsletter(content)
        
        # Send to subscribers (implementation depends on email service)
        sent_count = 0
        for subscriber in subscribers:
            try:
                # This would integrate with your email service provider
                self._send_email(subscriber, html_content, text_content)
                sent_count += 1
                logger.info(f"Newsletter sent to: {subscriber.email}")
            except Exception as e:
                logger.error(f"Failed to send newsletter to {subscriber.email}: {str(e)}")
        
        logger.info(f"Newsletter distribution complete: {sent_count}/{len(subscribers)} sent")
    
    def _prepare_newsletter_content(self) -> NewsletterContent:
        """Prepare content for weekly newsletter"""
        # This would analyze the week's regulatory monitoring data
        return NewsletterContent(
            week_ending=datetime.now().strftime('%B %d, %Y'),
            priority_alerts=[],
            new_regulations=[],
            sector_updates={},
            international_updates=[],
            implementation_tips=[]
        )
    
    def _send_email(self, subscriber: Subscriber, html_content: str, text_content: str):
        """Send email to subscriber (placeholder for email service integration)"""
        # This would integrate with your chosen email service provider:
        # - SendGrid, Mailgun, Amazon SES, etc.
        # - Include proper unsubscribe links with tokens
        # - Add required CAN-SPAM headers
        logger.info(f"Email would be sent to: {subscriber.email}")

def main():
    """Test newsletter service functionality"""
    print("📧 AI Regulatory Watch - Newsletter Service")
    print("⚠️  INFORMATIONAL CONTENT ONLY - NOT LEGAL ADVICE")
    print("-" * 60)
    
    service = NewsletterService()
    
    # Example: Add test subscriber (in production, this would be via web form)
    success, message = service.subscriber_manager.add_subscriber(
        email="test@example.com",
        preferences={
            'weekly_digest': True,
            'sector_healthcare': True,
            'sector_finance': False,
            'geographic_us': True,
            'geographic_eu': True
        }
    )
    
    print(f"Test subscription: {message}")
    
    # Generate test newsletter
    content = NewsletterContent(
        week_ending=datetime.now().strftime('%B %d, %Y'),
        priority_alerts=[{'title': 'Test Alert: New AI Regulation Proposed'}],
        new_regulations=[{'title': 'Test Regulation Update'}],
        sector_updates={'healthcare': [{'title': 'Healthcare AI Guidance Updated'}]},
        international_updates=[{'title': 'EU AI Act Implementation Update'}],
        implementation_tips=[{'title': 'Tip: Document Your AI System Inventory'}]
    )
    
    html, text = service.newsletter_generator.generate_weekly_newsletter(content)
    print("Newsletter generated successfully")
    print(f"HTML length: {len(html)} characters")
    print(f"Text length: {len(text)} characters")

if __name__ == "__main__":
    main()