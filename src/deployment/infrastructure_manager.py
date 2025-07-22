#!/usr/bin/env python3
"""
CDSI Infrastructure & Deployment Manager

Supports on-premise, hybrid, and cloud deployment architectures
with user profile management and infrastructure-specific configurations.

Deployment Modes:
- On-Premise: Full local deployment with air-gapped options
- Hybrid: Mixed cloud/on-prem with secure connectivity
- Cloud: Multi-cloud support (AWS, Azure, GCP)

Author: bdstest
License: Apache 2.0
Copyright: 2025 CDSI - Compliance Data Systems Insights
"""

import asyncio
import json
import logging
import os
import subprocess
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class DeploymentMode(Enum):
    """Supported deployment modes"""
    ON_PREMISE = "on_premise"
    HYBRID = "hybrid"
    CLOUD_AWS = "cloud_aws"
    CLOUD_AZURE = "cloud_azure"
    CLOUD_GCP = "cloud_gcp"
    MULTI_CLOUD = "multi_cloud"

class SecurityProfile(Enum):
    """Security compliance profiles"""
    STANDARD = "standard"
    GOVERNMENT = "government"
    FINANCIAL = "financial"
    HEALTHCARE = "healthcare"
    AIR_GAPPED = "air_gapped"

@dataclass
class UserProfile:
    """User profile with infrastructure requirements"""
    profile_id: str
    organization: str
    deployment_mode: DeploymentMode
    security_profile: SecurityProfile
    tier_level: str
    compliance_requirements: List[str]
    data_residency: str
    max_users: int
    max_devices: int
    storage_requirements: str
    network_requirements: Dict[str, Any]
    backup_requirements: Dict[str, Any]
    created_at: str
    last_updated: str

@dataclass
class InfrastructureConfig:
    """Infrastructure configuration for deployment"""
    deployment_mode: DeploymentMode
    security_profile: SecurityProfile
    database_config: Dict[str, Any]
    storage_config: Dict[str, Any]
    network_config: Dict[str, Any]
    monitoring_config: Dict[str, Any]
    backup_config: Dict[str, Any]
    scaling_config: Dict[str, Any]
    compliance_config: Dict[str, Any]

class InfrastructureManager:
    """
    Manages infrastructure deployment across on-premise, hybrid, and cloud environments
    with user profile-specific configurations and compliance requirements.
    """
    
    def __init__(self, config_path: str = "config/infrastructure.yaml"):
        self.config_path = Path(config_path)
        self.user_profiles: Dict[str, UserProfile] = {}
        self.infrastructure_configs: Dict[str, InfrastructureConfig] = {}
        
        # Load configuration
        self.load_configuration()
        
        # Initialize deployment templates
        self._initialize_deployment_templates()
        
        logger.info("Infrastructure Manager initialized")
    
    def load_configuration(self):
        """Load infrastructure configuration from files"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                self._parse_configuration(config)
            else:
                self._create_default_configuration()
        except Exception as e:
            logger.error(f"Failed to load infrastructure configuration: {e}")
            self._create_default_configuration()
    
    def _create_default_configuration(self):
        """Create default infrastructure configurations"""
        # Default user profiles for different deployment scenarios
        self.user_profiles = {
            'small_business': UserProfile(
                profile_id='small_business',
                organization='Small Business (< 100 employees)',
                deployment_mode=DeploymentMode.CLOUD_AWS,
                security_profile=SecurityProfile.STANDARD,
                tier_level='builder',
                compliance_requirements=['GDPR', 'CCPA'],
                data_residency='US_WEST',
                max_users=25,
                max_devices=100,
                storage_requirements='100GB',
                network_requirements={'bandwidth': '1Gbps', 'latency': '<100ms'},
                backup_requirements={'frequency': 'daily', 'retention': '90days'},
                created_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat()
            ),
            'enterprise': UserProfile(
                profile_id='enterprise',
                organization='Enterprise (1000+ employees)',
                deployment_mode=DeploymentMode.HYBRID,
                security_profile=SecurityProfile.STANDARD,
                tier_level='transformer',
                compliance_requirements=['GDPR', 'CCPA', 'SOX', 'HIPAA'],
                data_residency='MULTI_REGION',
                max_users=500,
                max_devices=2500,
                storage_requirements='10TB',
                network_requirements={'bandwidth': '10Gbps', 'latency': '<50ms'},
                backup_requirements={'frequency': 'hourly', 'retention': '7years'},
                created_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat()
            ),
            'government': UserProfile(
                profile_id='government',
                organization='Government Agency',
                deployment_mode=DeploymentMode.ON_PREMISE,
                security_profile=SecurityProfile.AIR_GAPPED,
                tier_level='champion',
                compliance_requirements=['FISMA', 'FedRAMP', 'NIST'],
                data_residency='ON_PREMISE_ONLY',
                max_users=1000,
                max_devices=5000,
                storage_requirements='100TB',
                network_requirements={'bandwidth': '100Gbps', 'latency': '<10ms'},
                backup_requirements={'frequency': 'continuous', 'retention': 'permanent'},
                created_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat()
            ),
            'financial_services': UserProfile(
                profile_id='financial_services',
                organization='Financial Services',
                deployment_mode=DeploymentMode.HYBRID,
                security_profile=SecurityProfile.FINANCIAL,
                tier_level='transformer',
                compliance_requirements=['SOX', 'PCI_DSS', 'GDPR', 'BASEL_III'],
                data_residency='REGULATED_REGIONS',
                max_users=200,
                max_devices=1000,
                storage_requirements='50TB',
                network_requirements={'bandwidth': '25Gbps', 'latency': '<25ms'},
                backup_requirements={'frequency': 'real_time', 'retention': '10years'},
                created_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat()
            ),
            'healthcare': UserProfile(
                profile_id='healthcare',
                organization='Healthcare Provider',
                deployment_mode=DeploymentMode.CLOUD_AWS,
                security_profile=SecurityProfile.HEALTHCARE,
                tier_level='accelerator',
                compliance_requirements=['HIPAA', 'HITECH', 'GDPR'],
                data_residency='HIPAA_COMPLIANT',
                max_users=100,
                max_devices=500,
                storage_requirements='5TB',
                network_requirements={'bandwidth': '5Gbps', 'latency': '<75ms'},
                backup_requirements={'frequency': 'hourly', 'retention': '6years'},
                created_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat()
            )
        }
        
        # Create infrastructure configs for each deployment mode
        self._create_infrastructure_configs()
    
    def _create_infrastructure_configs(self):
        """Create infrastructure configurations for each deployment mode"""
        
        # On-Premise Configuration
        self.infrastructure_configs['on_premise'] = InfrastructureConfig(
            deployment_mode=DeploymentMode.ON_PREMISE,
            security_profile=SecurityProfile.AIR_GAPPED,
            database_config={
                'type': 'postgresql',
                'host': 'localhost',
                'port': 5432,
                'encryption': 'AES-256',
                'backup_encryption': True,
                'replication': 'synchronous'
            },
            storage_config={
                'type': 'local_ssd',
                'encryption': 'LUKS',
                'raid_level': 'RAID-10',
                'backup_storage': 'tape_library',
                'retention_policy': 'indefinite'
            },
            network_config={
                'firewall': 'hardware_firewall',
                'vpn': 'site_to_site',
                'intrusion_detection': True,
                'network_segmentation': True,
                'air_gap': True
            },
            monitoring_config={
                'metrics': 'prometheus',
                'logging': 'elk_stack',
                'alerting': 'local_smtp',
                'dashboards': 'grafana',
                'siem': 'splunk_enterprise'
            },
            backup_config={
                'strategy': '3-2-1',
                'frequency': 'continuous',
                'encryption': 'AES-256',
                'offsite': 'secure_facility',
                'testing': 'monthly'
            },
            scaling_config={
                'horizontal': 'kubernetes',
                'vertical': 'auto_scaling',
                'load_balancer': 'f5',
                'cdn': 'none'
            },
            compliance_config={
                'audit_logging': True,
                'data_classification': True,
                'access_controls': 'rbac',
                'vulnerability_scanning': 'nessus'
            }
        )
        
        # Hybrid Configuration
        self.infrastructure_configs['hybrid'] = InfrastructureConfig(
            deployment_mode=DeploymentMode.HYBRID,
            security_profile=SecurityProfile.FINANCIAL,
            database_config={
                'type': 'postgresql_cluster',
                'primary': 'on_premise',
                'replica': 'cloud',
                'encryption': 'TDE',
                'connection_pooling': True,
                'failover': 'automatic'
            },
            storage_config={
                'primary': 'on_premise_ssd',
                'secondary': 'cloud_s3',
                'tiering': 'intelligent',
                'encryption': 'customer_managed_keys',
                'sync_frequency': 'real_time'
            },
            network_config={
                'connectivity': 'direct_connect',
                'vpn_backup': 'ipsec',
                'security_groups': True,
                'private_subnets': True,
                'transit_gateway': True
            },
            monitoring_config={
                'unified_dashboard': 'datadog',
                'cloud_monitoring': 'cloudwatch',
                'on_prem_monitoring': 'nagios',
                'log_aggregation': 'splunk_cloud',
                'alerting': 'pagerduty'
            },
            backup_config={
                'strategy': 'hybrid_3-2-1',
                'on_prem_backup': 'veeam',
                'cloud_backup': 'aws_backup',
                'cross_region': True,
                'testing': 'weekly'
            },
            scaling_config={
                'cloud_burst': True,
                'auto_scaling_groups': True,
                'load_balancer': 'application_lb',
                'cdn': 'cloudfront'
            },
            compliance_config={
                'data_governance': 'collibra',
                'compliance_monitoring': 'rsa_archer',
                'risk_assessment': 'grc_platform',
                'audit_trail': 'immutable_logs'
            }
        )
        
        # Cloud Configuration (AWS)
        self.infrastructure_configs['cloud_aws'] = InfrastructureConfig(
            deployment_mode=DeploymentMode.CLOUD_AWS,
            security_profile=SecurityProfile.STANDARD,
            database_config={
                'type': 'rds_postgresql',
                'multi_az': True,
                'read_replicas': 3,
                'encryption': 'kms',
                'backup_retention': 35,
                'performance_insights': True
            },
            storage_config={
                'primary': 'ebs_gp3',
                'backup': 's3_ia',
                'archive': 'glacier_deep_archive',
                'lifecycle_policy': True,
                'versioning': True
            },
            network_config={
                'vpc': 'multi_az',
                'security_groups': True,
                'nacls': True,
                'nat_gateway': True,
                'internet_gateway': True
            },
            monitoring_config={
                'cloudwatch': True,
                'x_ray': True,
                'cloudtrail': True,
                'config': True,
                'guardduty': True
            },
            backup_config={
                'aws_backup': True,
                'cross_region': True,
                'point_in_time_recovery': True,
                'automated_backups': True,
                'backup_vault': True
            },
            scaling_config={
                'auto_scaling': True,
                'elastic_load_balancer': True,
                'cloudfront': True,
                'route53': True,
                'api_gateway': True
            },
            compliance_config={
                'aws_config': True,
                'security_hub': True,
                'inspector': True,
                'macie': True,
                'well_architected': True
            }
        )
    
    def get_user_profile(self, profile_id: str) -> Optional[UserProfile]:
        """Get user profile by ID"""
        return self.user_profiles.get(profile_id)
    
    def create_user_profile(self, profile_data: Dict[str, Any]) -> UserProfile:
        """Create a new user profile"""
        profile = UserProfile(
            profile_id=profile_data['profile_id'],
            organization=profile_data['organization'],
            deployment_mode=DeploymentMode(profile_data['deployment_mode']),
            security_profile=SecurityProfile(profile_data['security_profile']),
            tier_level=profile_data['tier_level'],
            compliance_requirements=profile_data['compliance_requirements'],
            data_residency=profile_data['data_residency'],
            max_users=profile_data['max_users'],
            max_devices=profile_data['max_devices'],
            storage_requirements=profile_data['storage_requirements'],
            network_requirements=profile_data['network_requirements'],
            backup_requirements=profile_data['backup_requirements'],
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat()
        )
        
        self.user_profiles[profile.profile_id] = profile
        return profile
    
    def get_infrastructure_config(self, deployment_mode: DeploymentMode) -> Optional[InfrastructureConfig]:
        """Get infrastructure configuration for deployment mode"""
        return self.infrastructure_configs.get(deployment_mode.value)
    
    def generate_deployment_manifest(self, profile_id: str) -> Dict[str, Any]:
        """Generate deployment manifest for user profile"""
        profile = self.get_user_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")
        
        config = self.get_infrastructure_config(profile.deployment_mode)
        if not config:
            raise ValueError(f"No infrastructure config for {profile.deployment_mode}")
        
        # Generate comprehensive deployment manifest
        manifest = {
            'metadata': {
                'profile_id': profile.profile_id,
                'organization': profile.organization,
                'deployment_mode': profile.deployment_mode.value,
                'security_profile': profile.security_profile.value,
                'tier_level': profile.tier_level,
                'generated_at': datetime.now().isoformat()
            },
            'requirements': {
                'compliance': profile.compliance_requirements,
                'data_residency': profile.data_residency,
                'scaling': {
                    'max_users': profile.max_users,
                    'max_devices': profile.max_devices,
                    'storage': profile.storage_requirements
                },
                'performance': profile.network_requirements,
                'backup': profile.backup_requirements
            },
            'infrastructure': asdict(config),
            'deployment_steps': self._generate_deployment_steps(profile, config),
            'security_controls': self._generate_security_controls(profile, config),
            'monitoring_setup': self._generate_monitoring_setup(profile, config),
            'compliance_validation': self._generate_compliance_validation(profile)
        }
        
        return manifest
    
    def _generate_deployment_steps(self, profile: UserProfile, config: InfrastructureConfig) -> List[Dict[str, Any]]:
        """Generate deployment steps based on infrastructure config"""
        steps = []
        
        if config.deployment_mode == DeploymentMode.ON_PREMISE:
            steps.extend([
                {
                    'step': 1,
                    'action': 'Prepare hardware infrastructure',
                    'details': 'Install servers, storage, and network equipment',
                    'estimated_time': '2-4 weeks',
                    'dependencies': ['hardware_procurement', 'datacenter_space']
                },
                {
                    'step': 2,
                    'action': 'Install base operating system',
                    'details': 'Deploy hardened Linux with security configurations',
                    'estimated_time': '1 week',
                    'dependencies': ['hardware_ready']
                },
                {
                    'step': 3,
                    'action': 'Configure database cluster',
                    'details': 'Deploy PostgreSQL with replication and encryption',
                    'estimated_time': '3 days',
                    'dependencies': ['os_installed']
                },
                {
                    'step': 4,
                    'action': 'Deploy CDSI application',
                    'details': 'Install and configure CDSI platform components',
                    'estimated_time': '2 days',
                    'dependencies': ['database_ready']
                },
                {
                    'step': 5,
                    'action': 'Configure monitoring and alerting',
                    'details': 'Set up Prometheus, Grafana, and ELK stack',
                    'estimated_time': '1 week',
                    'dependencies': ['application_deployed']
                },
                {
                    'step': 6,
                    'action': 'Security hardening and testing',
                    'details': 'Vulnerability scanning and penetration testing',
                    'estimated_time': '1-2 weeks',
                    'dependencies': ['monitoring_configured']
                },
                {
                    'step': 7,
                    'action': 'User acceptance testing',
                    'details': 'End-to-end testing with real regulatory data',
                    'estimated_time': '2 weeks',
                    'dependencies': ['security_validated']
                },
                {
                    'step': 8,
                    'action': 'Production cutover',
                    'details': 'Go-live with monitoring and support procedures',
                    'estimated_time': '1 week',
                    'dependencies': ['uat_completed']
                }
            ])
        
        elif config.deployment_mode == DeploymentMode.HYBRID:
            steps.extend([
                {
                    'step': 1,
                    'action': 'Establish cloud connectivity',
                    'details': 'Set up Direct Connect or ExpressRoute',
                    'estimated_time': '2-3 weeks',
                    'dependencies': ['network_design_approved']
                },
                {
                    'step': 2,
                    'action': 'Deploy cloud infrastructure',
                    'details': 'Provision VPC, subnets, and security groups',
                    'estimated_time': '1 week',
                    'dependencies': ['connectivity_established']
                },
                {
                    'step': 3,
                    'action': 'Configure hybrid database',
                    'details': 'Set up primary on-prem, replica in cloud',
                    'estimated_time': '1 week',
                    'dependencies': ['cloud_infrastructure_ready']
                },
                {
                    'step': 4,
                    'action': 'Deploy application tier',
                    'details': 'Install CDSI on both on-prem and cloud',
                    'estimated_time': '1 week',
                    'dependencies': ['database_configured']
                },
                {
                    'step': 5,
                    'action': 'Configure unified monitoring',
                    'details': 'Set up cross-environment monitoring',
                    'estimated_time': '1 week',
                    'dependencies': ['applications_deployed']
                },
                {
                    'step': 6,
                    'action': 'Test failover procedures',
                    'details': 'Validate disaster recovery capabilities',
                    'estimated_time': '1 week',
                    'dependencies': ['monitoring_operational']
                }
            ])
        
        elif config.deployment_mode in [DeploymentMode.CLOUD_AWS, DeploymentMode.CLOUD_AZURE, DeploymentMode.CLOUD_GCP]:
            steps.extend([
                {
                    'step': 1,
                    'action': 'Provision cloud infrastructure',
                    'details': 'Create VPC, subnets, security groups via Terraform',
                    'estimated_time': '2 days',
                    'dependencies': ['terraform_templates_ready']
                },
                {
                    'step': 2,
                    'action': 'Deploy managed database',
                    'details': 'Set up RDS/Cloud SQL with Multi-AZ',
                    'estimated_time': '1 day',
                    'dependencies': ['network_configured']
                },
                {
                    'step': 3,
                    'action': 'Deploy containerized application',
                    'details': 'Deploy CDSI via EKS/AKS/GKE',
                    'estimated_time': '2 days',
                    'dependencies': ['database_ready']
                },
                {
                    'step': 4,
                    'action': 'Configure auto-scaling',
                    'details': 'Set up horizontal pod autoscaler',
                    'estimated_time': '1 day',
                    'dependencies': ['application_deployed']
                },
                {
                    'step': 5,
                    'action': 'Set up monitoring and logging',
                    'details': 'Configure CloudWatch/Azure Monitor/Stackdriver',
                    'estimated_time': '1 day',
                    'dependencies': ['scaling_configured']
                },
                {
                    'step': 6,
                    'action': 'Security and compliance validation',
                    'details': 'Run security scans and compliance checks',
                    'estimated_time': '3 days',
                    'dependencies': ['monitoring_operational']
                }
            ])
        
        return steps
    
    def _generate_security_controls(self, profile: UserProfile, config: InfrastructureConfig) -> Dict[str, Any]:
        """Generate security controls based on security profile"""
        controls = {
            'access_control': {
                'multi_factor_authentication': True,
                'role_based_access': True,
                'privileged_access_management': True,
                'session_monitoring': True
            },
            'data_protection': {
                'encryption_at_rest': True,
                'encryption_in_transit': True,
                'key_management': 'customer_managed',
                'data_loss_prevention': True
            },
            'network_security': {
                'firewall': True,
                'intrusion_detection': True,
                'network_segmentation': True,
                'ddos_protection': True
            },
            'monitoring': {
                'security_information_event_management': True,
                'vulnerability_scanning': True,
                'security_orchestration': True,
                'incident_response': True
            }
        }
        
        # Enhance controls based on security profile
        if profile.security_profile == SecurityProfile.AIR_GAPPED:
            controls['additional_controls'] = {
                'air_gap_enforcement': True,
                'removable_media_controls': True,
                'physical_security': True,
                'electromagnetic_shielding': True
            }
        elif profile.security_profile == SecurityProfile.FINANCIAL:
            controls['additional_controls'] = {
                'fraud_detection': True,
                'transaction_monitoring': True,
                'regulatory_reporting': True,
                'audit_trail_immutability': True
            }
        elif profile.security_profile == SecurityProfile.HEALTHCARE:
            controls['additional_controls'] = {
                'phi_protection': True,
                'access_logging': True,
                'breach_detection': True,
                'patient_consent_management': True
            }
        
        return controls
    
    def _generate_monitoring_setup(self, profile: UserProfile, config: InfrastructureConfig) -> Dict[str, Any]:
        """Generate monitoring configuration"""
        return {
            'metrics': {
                'infrastructure': ['cpu', 'memory', 'disk', 'network'],
                'application': ['response_time', 'throughput', 'error_rate'],
                'business': ['user_activity', 'compliance_scans', 'alerts']
            },
            'alerting': {
                'channels': ['email', 'slack', 'pagerduty'],
                'escalation_policies': True,
                'alert_correlation': True
            },
            'logging': {
                'application_logs': True,
                'audit_logs': True,
                'security_logs': True,
                'retention_period': '7_years'
            },
            'dashboards': {
                'executive': True,
                'operational': True,
                'security': True,
                'compliance': True
            }
        }
    
    def _generate_compliance_validation(self, profile: UserProfile) -> Dict[str, Any]:
        """Generate compliance validation checklist"""
        validations = {}
        
        for requirement in profile.compliance_requirements:
            if requirement == 'GDPR':
                validations['GDPR'] = {
                    'data_processing_records': True,
                    'consent_management': True,
                    'data_subject_rights': True,
                    'breach_notification': True,
                    'privacy_by_design': True
                }
            elif requirement == 'HIPAA':
                validations['HIPAA'] = {
                    'administrative_safeguards': True,
                    'physical_safeguards': True,
                    'technical_safeguards': True,
                    'risk_assessment': True,
                    'workforce_training': True
                }
            elif requirement == 'SOX':
                validations['SOX'] = {
                    'financial_reporting_controls': True,
                    'audit_trail': True,
                    'change_management': True,
                    'access_controls': True
                }
        
        return validations
    
    def _initialize_deployment_templates(self):
        """Initialize deployment templates for different platforms"""
        templates_dir = Path("deployment/templates")
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Terraform templates for cloud deployments
        # Create Ansible playbooks for on-premise deployments
        # Create Docker Compose files for development
        # Create Kubernetes manifests for container deployments
        
        logger.info("Deployment templates initialized")
    
    def list_user_profiles(self) -> List[str]:
        """List available user profiles"""
        return list(self.user_profiles.keys())
    
    def get_deployment_recommendations(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get deployment recommendations based on requirements"""
        recommendations = []
        
        # Analyze requirements and suggest appropriate profiles
        org_size = requirements.get('organization_size', 'small')
        compliance_needs = requirements.get('compliance_requirements', [])
        security_level = requirements.get('security_level', 'standard')
        budget_range = requirements.get('budget_range', 'low')
        
        # Generate recommendations based on criteria
        for profile_id, profile in self.user_profiles.items():
            score = self._calculate_recommendation_score(profile, requirements)
            if score > 0.6:  # 60% match threshold
                recommendations.append({
                    'profile_id': profile_id,
                    'score': score,
                    'profile': profile,
                    'estimated_cost': self._estimate_deployment_cost(profile),
                    'deployment_time': self._estimate_deployment_time(profile)
                })
        
        # Sort by score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations
    
    def _calculate_recommendation_score(self, profile: UserProfile, requirements: Dict[str, Any]) -> float:
        """Calculate how well a profile matches requirements"""
        score = 0.0
        factors = 0
        
        # Organization size match
        org_size = requirements.get('organization_size', 'small')
        if (org_size == 'small' and profile.max_users <= 100) or \
           (org_size == 'medium' and 100 < profile.max_users <= 500) or \
           (org_size == 'large' and profile.max_users > 500):
            score += 1.0
        factors += 1
        
        # Compliance requirements match
        required_compliance = set(requirements.get('compliance_requirements', []))
        profile_compliance = set(profile.compliance_requirements)
        if required_compliance:
            overlap = len(required_compliance.intersection(profile_compliance))
            score += overlap / len(required_compliance)
            factors += 1
        
        # Security level match
        security_mapping = {
            'standard': SecurityProfile.STANDARD,
            'high': SecurityProfile.FINANCIAL,
            'maximum': SecurityProfile.AIR_GAPPED
        }
        required_security = security_mapping.get(requirements.get('security_level', 'standard'))
        if profile.security_profile == required_security:
            score += 1.0
        factors += 1
        
        return score / factors if factors > 0 else 0.0
    
    def _estimate_deployment_cost(self, profile: UserProfile) -> Dict[str, Any]:
        """Estimate deployment costs for a profile"""
        # Cost estimation based on deployment mode and requirements
        base_costs = {
            DeploymentMode.ON_PREMISE: {'setup': 100000, 'monthly': 5000},
            DeploymentMode.HYBRID: {'setup': 50000, 'monthly': 8000},
            DeploymentMode.CLOUD_AWS: {'setup': 5000, 'monthly': 3000}
        }
        
        base = base_costs.get(profile.deployment_mode, {'setup': 10000, 'monthly': 2000})
        
        # Scale based on user and device count
        user_multiplier = max(1.0, profile.max_users / 100)
        device_multiplier = max(1.0, profile.max_devices / 500)
        
        return {
            'setup_cost': int(base['setup'] * user_multiplier),
            'monthly_cost': int(base['monthly'] * user_multiplier * device_multiplier),
            'annual_cost': int(base['monthly'] * user_multiplier * device_multiplier * 12),
            'currency': 'USD'
        }
    
    def _estimate_deployment_time(self, profile: UserProfile) -> Dict[str, str]:
        """Estimate deployment timeline for a profile"""
        timelines = {
            DeploymentMode.ON_PREMISE: {'planning': '4-6 weeks', 'deployment': '8-12 weeks', 'total': '3-4 months'},
            DeploymentMode.HYBRID: {'planning': '3-4 weeks', 'deployment': '6-8 weeks', 'total': '2-3 months'},
            DeploymentMode.CLOUD_AWS: {'planning': '1-2 weeks', 'deployment': '2-3 weeks', 'total': '1 month'}
        }
        
        return timelines.get(profile.deployment_mode, {'total': '1-2 months'})

def main():
    """Test the infrastructure manager"""
    print("🏗️ CDSI Infrastructure Manager Test")
    print("=" * 50)
    
    # Initialize manager
    manager = InfrastructureManager()
    
    # List available profiles
    print("\n📋 Available User Profiles:")
    for profile_id in manager.list_user_profiles():
        profile = manager.get_user_profile(profile_id)
        print(f"  - {profile_id}: {profile.organization}")
        print(f"    Deployment: {profile.deployment_mode.value}")
        print(f"    Security: {profile.security_profile.value}")
        print(f"    Tier: {profile.tier_level}")
        print()
    
    # Generate deployment manifest for enterprise profile
    print("\n🚀 Generating Deployment Manifest for Enterprise:")
    manifest = manager.generate_deployment_manifest('enterprise')
    
    print(f"Deployment Mode: {manifest['metadata']['deployment_mode']}")
    print(f"Security Profile: {manifest['metadata']['security_profile']}")
    print(f"Compliance Requirements: {', '.join(manifest['requirements']['compliance'])}")
    print(f"Deployment Steps: {len(manifest['deployment_steps'])} steps")
    
    # Show first few deployment steps
    print("\n📝 Deployment Steps (first 3):")
    for step in manifest['deployment_steps'][:3]:
        print(f"  {step['step']}. {step['action']}")
        print(f"     Time: {step['estimated_time']}")
        print()
    
    # Get recommendations
    print("\n💡 Deployment Recommendations:")
    requirements = {
        'organization_size': 'medium',
        'compliance_requirements': ['GDPR', 'HIPAA'],
        'security_level': 'high',
        'budget_range': 'medium'
    }
    
    recommendations = manager.get_deployment_recommendations(requirements)
    
    for rec in recommendations[:3]:  # Show top 3
        print(f"  {rec['profile_id']}: Score {rec['score']:.1%}")
        print(f"    Setup Cost: ${rec['estimated_cost']['setup_cost']:,}")
        print(f"    Monthly Cost: ${rec['estimated_cost']['monthly_cost']:,}")
        print(f"    Timeline: {rec['deployment_time']['total']}")
        print()

if __name__ == "__main__":
    main()