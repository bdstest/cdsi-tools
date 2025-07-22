#!/usr/bin/env python3
"""
CDSI Cloud Bridge Manager

Enables seamless connectivity between cloud infrastructure and on-premise/hybrid
customer deployments using lightweight bridge VMs and containerized connectors.

Competitive Architecture:
- Cloud-hosted management plane (always available)
- On-premise data plane (customer controlled)
- Secure bridge connectivity via VPN/containers
- Cost-optimized cloud instances sized per customer needs
- Automated Terraform deployment for rapid setup

Author: bdstest
License: Apache 2.0
Copyright: 2025 CDSI - Compliance Data Systems Insights
"""

import json
import logging
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class BridgeArchitecture(Enum):
    """Cloud bridge deployment architectures"""
    REVERSE_TUNNEL = "reverse_tunnel"  # On-prem initiates connection
    VPN_GATEWAY = "vpn_gateway"        # Site-to-site VPN
    CONTAINER_BRIDGE = "container_bridge"  # Containerized connector
    API_PROXY = "api_proxy"            # API gateway proxy

class CloudProvider(Enum):
    """Supported cloud providers for bridge VMs"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    DIGITALOCEAN = "digitalocean"
    LINODE = "linode"

@dataclass
class CloudInstanceSpec:
    """Cloud instance specifications for bridge VM"""
    provider: CloudProvider
    instance_type: str
    vcpus: int
    memory_gb: int
    storage_gb: int
    network_performance: str
    hourly_cost: float
    monthly_cost: float
    max_concurrent_connections: int
    max_throughput_mbps: int

@dataclass
class BridgeConfiguration:
    """Bridge configuration for customer deployment"""
    customer_id: str
    architecture_type: BridgeArchitecture
    cloud_instance: CloudInstanceSpec
    on_prem_requirements: Dict[str, Any]
    network_config: Dict[str, Any]
    security_config: Dict[str, Any]
    monitoring_config: Dict[str, Any]
    backup_strategy: Dict[str, Any]
    estimated_monthly_cost: float
    deployment_time_hours: int

class CloudBridgeManager:
    """
    Manages cloud bridge infrastructure for hybrid and on-premise deployments
    
    Provides cost-competitive connectivity solutions that match or beat
    existing market players while maintaining security and performance.
    """
    
    def __init__(self, config_path: str = "config/cloud_bridge.yaml"):
        self.config_path = Path(config_path)
        self.instance_catalog = self._build_instance_catalog()
        self.architecture_templates = self._build_architecture_templates()
        
        logger.info("Cloud Bridge Manager initialized")
    
    def _build_instance_catalog(self) -> Dict[str, List[CloudInstanceSpec]]:
        """Build catalog of optimized cloud instances for different customer sizes"""
        return {
            # Small customers (< 100 users, < 500 devices)
            'small': [
                # AWS options
                CloudInstanceSpec(
                    provider=CloudProvider.AWS,
                    instance_type="t3.medium",
                    vcpus=2,
                    memory_gb=4,
                    storage_gb=20,
                    network_performance="Up to 5 Gbps",
                    hourly_cost=0.0416,
                    monthly_cost=30.0,
                    max_concurrent_connections=100,
                    max_throughput_mbps=500
                ),
                # DigitalOcean (cost competitive)
                CloudInstanceSpec(
                    provider=CloudProvider.DIGITALOCEAN,
                    instance_type="s-2vcpu-4gb",
                    vcpus=2,
                    memory_gb=4,
                    storage_gb=80,
                    network_performance="4 Gbps",
                    hourly_cost=0.036,
                    monthly_cost=26.0,
                    max_concurrent_connections=100,
                    max_throughput_mbps=400
                ),
                # Linode (best value)
                CloudInstanceSpec(
                    provider=CloudProvider.LINODE,
                    instance_type="Linode 4GB",
                    vcpus=2,
                    memory_gb=4,
                    storage_gb=80,
                    network_performance="4 Gbps",
                    hourly_cost=0.030,
                    monthly_cost=22.0,
                    max_concurrent_connections=120,
                    max_throughput_mbps=400
                )
            ],
            
            # Medium customers (100-500 users, 500-2000 devices)
            'medium': [
                # AWS
                CloudInstanceSpec(
                    provider=CloudProvider.AWS,
                    instance_type="c5.large",
                    vcpus=2,
                    memory_gb=4,
                    storage_gb=50,
                    network_performance="Up to 10 Gbps",
                    hourly_cost=0.085,
                    monthly_cost=62.0,
                    max_concurrent_connections=500,
                    max_throughput_mbps=1000
                ),
                # DigitalOcean
                CloudInstanceSpec(
                    provider=CloudProvider.DIGITALOCEAN,
                    instance_type="c-4",
                    vcpus=4,
                    memory_gb=8,
                    storage_gb=100,
                    network_performance="5 Gbps",
                    hourly_cost=0.071,
                    monthly_cost=52.0,
                    max_concurrent_connections=400,
                    max_throughput_mbps=800
                ),
                # Linode
                CloudInstanceSpec(
                    provider=CloudProvider.LINODE,
                    instance_type="Linode 8GB",
                    vcpus=4,
                    memory_gb=8,
                    storage_gb=160,
                    network_performance="5 Gbps",
                    hourly_cost=0.060,
                    monthly_cost=44.0,
                    max_concurrent_connections=450,
                    max_throughput_mbps=800
                )
            ],
            
            # Large customers (500+ users, 2000+ devices)
            'large': [
                # AWS
                CloudInstanceSpec(
                    provider=CloudProvider.AWS,
                    instance_type="c5.xlarge",
                    vcpus=4,
                    memory_gb=8,
                    storage_gb=100,
                    network_performance="Up to 10 Gbps",
                    hourly_cost=0.170,
                    monthly_cost=124.0,
                    max_concurrent_connections=1000,
                    max_throughput_mbps=2000
                ),
                # DigitalOcean
                CloudInstanceSpec(
                    provider=CloudProvider.DIGITALOCEAN,
                    instance_type="c-8",
                    vcpus=8,
                    memory_gb=16,
                    storage_gb=200,
                    network_performance="6 Gbps",
                    hourly_cost=0.143,
                    monthly_cost=105.0,
                    max_concurrent_connections=800,
                    max_throughput_mbps=1500
                ),
                # Linode (best performance/cost)
                CloudInstanceSpec(
                    provider=CloudProvider.LINODE,
                    instance_type="Linode 16GB",
                    vcpus=6,
                    memory_gb=16,
                    storage_gb=320,
                    network_performance="6 Gbps",
                    hourly_cost=0.120,
                    monthly_cost=88.0,
                    max_concurrent_connections=900,
                    max_throughput_mbps=1500
                )
            ]
        }
    
    def _build_architecture_templates(self) -> Dict[str, Dict[str, Any]]:
        """Build architecture templates for different bridge types"""
        return {
            # Reverse tunnel - most secure, customer initiates connection
            'reverse_tunnel': {
                'description': 'On-premise agent initiates secure tunnel to cloud',
                'security_level': 'highest',
                'complexity': 'low',
                'customer_firewall_changes': 'outbound only',
                'components': {
                    'cloud_side': ['bridge_vm', 'load_balancer', 'monitoring'],
                    'on_prem_side': ['cdsi_agent', 'tunnel_client', 'local_db']
                },
                'network_requirements': {
                    'outbound_ports': [443, 8443],
                    'inbound_ports': [],
                    'protocols': ['HTTPS', 'WSS']
                },
                'data_flow': 'On-prem -> Cloud (initiated from on-prem)',
                'suitable_for': ['high_security', 'restrictive_firewalls', 'government']
            },
            
            # VPN Gateway - traditional site-to-site
            'vpn_gateway': {
                'description': 'Site-to-site VPN between cloud and on-premise',
                'security_level': 'high', 
                'complexity': 'medium',
                'customer_firewall_changes': 'inbound/outbound',
                'components': {
                    'cloud_side': ['vpn_gateway', 'bridge_vm', 'private_subnet'],
                    'on_prem_side': ['vpn_endpoint', 'cdsi_platform', 'database']
                },
                'network_requirements': {
                    'outbound_ports': [500, 4500],
                    'inbound_ports': [500, 4500],
                    'protocols': ['IPSec', 'IKEv2']
                },
                'data_flow': 'Bidirectional over encrypted tunnel',
                'suitable_for': ['enterprise', 'medium_security', 'existing_vpn']
            },
            
            # Container Bridge - lightweight, Docker-based
            'container_bridge': {
                'description': 'Lightweight containerized connector',
                'security_level': 'medium',
                'complexity': 'low',
                'customer_firewall_changes': 'outbound only',
                'components': {
                    'cloud_side': ['bridge_vm', 'container_registry', 'api_gateway'],
                    'on_prem_side': ['docker_container', 'cdsi_connector', 'config_volume']
                },
                'network_requirements': {
                    'outbound_ports': [443, 8080],
                    'inbound_ports': [],
                    'protocols': ['HTTPS', 'WebSocket']
                },
                'data_flow': 'Container -> Cloud API (polling/webhook)',
                'suitable_for': ['small_business', 'quick_setup', 'docker_environments']
            },
            
            # API Proxy - simplest integration
            'api_proxy': {
                'description': 'Cloud-hosted API proxy for on-premise systems',
                'security_level': 'medium',
                'complexity': 'lowest',
                'customer_firewall_changes': 'outbound only',
                'components': {
                    'cloud_side': ['api_gateway', 'proxy_service', 'cache_layer'],
                    'on_prem_side': ['cdsi_client', 'api_credentials', 'local_config']
                },
                'network_requirements': {
                    'outbound_ports': [443],
                    'inbound_ports': [],
                    'protocols': ['HTTPS']
                },
                'data_flow': 'On-prem API calls -> Cloud proxy -> Processing',
                'suitable_for': ['saas_integration', 'minimal_setup', 'api_first']
            }
        }
    
    def recommend_bridge_configuration(self, requirements: Dict[str, Any]) -> BridgeConfiguration:
        """Recommend optimal bridge configuration based on customer requirements"""
        
        # Determine customer size category
        user_count = requirements.get('users', 50)
        device_count = requirements.get('devices', 200)
        security_level = requirements.get('security_level', 'medium')
        budget_preference = requirements.get('budget_preference', 'balanced')  # cost_optimized, balanced, performance
        existing_infrastructure = requirements.get('existing_infrastructure', [])
        
        # Size category
        if user_count < 100 and device_count < 500:
            size_category = 'small'
        elif user_count < 500 and device_count < 2000:
            size_category = 'medium'
        else:
            size_category = 'large'
        
        # Select architecture based on security needs
        if security_level in ['high', 'government'] or 'air_gap' in requirements.get('compliance', []):
            architecture = BridgeArchitecture.REVERSE_TUNNEL
        elif 'vpn' in existing_infrastructure:
            architecture = BridgeArchitecture.VPN_GATEWAY
        elif 'docker' in existing_infrastructure or user_count < 100:
            architecture = BridgeArchitecture.CONTAINER_BRIDGE
        else:
            architecture = BridgeArchitecture.API_PROXY
        
        # Select optimal cloud instance
        instances = self.instance_catalog[size_category]
        
        if budget_preference == 'cost_optimized':
            # Choose cheapest option
            selected_instance = min(instances, key=lambda x: x.monthly_cost)
        elif budget_preference == 'performance':
            # Choose highest performance
            selected_instance = max(instances, key=lambda x: x.max_throughput_mbps)
        else:
            # Balanced - best performance per dollar
            selected_instance = max(instances, key=lambda x: x.max_throughput_mbps / x.monthly_cost)
        
        # Calculate total monthly cost including network and storage
        base_cost = selected_instance.monthly_cost
        network_cost = self._calculate_network_cost(architecture, requirements)
        storage_cost = self._calculate_storage_cost(requirements)
        monitoring_cost = 15.0  # Basic monitoring
        
        total_monthly_cost = base_cost + network_cost + storage_cost + monitoring_cost
        
        # Estimate deployment time
        deployment_time = self._estimate_deployment_time(architecture, size_category)
        
        return BridgeConfiguration(
            customer_id=requirements.get('customer_id', 'unknown'),
            architecture_type=architecture,
            cloud_instance=selected_instance,
            on_prem_requirements=self._generate_on_prem_requirements(architecture, size_category),
            network_config=self._generate_network_config(architecture, selected_instance),
            security_config=self._generate_security_config(architecture, security_level),
            monitoring_config=self._generate_monitoring_config(selected_instance),
            backup_strategy=self._generate_backup_strategy(requirements),
            estimated_monthly_cost=total_monthly_cost,
            deployment_time_hours=deployment_time
        )
    
    def _calculate_network_cost(self, architecture: BridgeArchitecture, requirements: Dict[str, Any]) -> float:
        """Calculate monthly network costs"""
        data_transfer_gb = requirements.get('monthly_data_transfer_gb', 100)
        
        costs = {
            BridgeArchitecture.REVERSE_TUNNEL: 0.02 * data_transfer_gb,  # $0.02/GB
            BridgeArchitecture.VPN_GATEWAY: 45.0,  # VPN gateway cost
            BridgeArchitecture.CONTAINER_BRIDGE: 0.01 * data_transfer_gb,  # Lower transfer cost
            BridgeArchitecture.API_PROXY: 0.01 * data_transfer_gb  # API gateway included
        }
        
        return min(costs.get(architecture, 10.0), 200.0)  # Cap at $200/month
    
    def _calculate_storage_cost(self, requirements: Dict[str, Any]) -> float:
        """Calculate monthly storage costs"""
        storage_gb = requirements.get('cloud_storage_gb', 50)
        backup_gb = storage_gb * 2  # Backup is 2x primary storage
        
        # Standard SSD storage cost: $0.10/GB/month
        # Backup storage cost: $0.05/GB/month
        return (storage_gb * 0.10) + (backup_gb * 0.05)
    
    def _estimate_deployment_time(self, architecture: BridgeArchitecture, size_category: str) -> int:
        """Estimate deployment time in hours"""
        base_times = {
            BridgeArchitecture.API_PROXY: 2,
            BridgeArchitecture.CONTAINER_BRIDGE: 4,
            BridgeArchitecture.REVERSE_TUNNEL: 6,
            BridgeArchitecture.VPN_GATEWAY: 8
        }
        
        size_multipliers = {
            'small': 1.0,
            'medium': 1.5,
            'large': 2.0
        }
        
        return int(base_times[architecture] * size_multipliers[size_category])
    
    def _generate_on_prem_requirements(self, architecture: BridgeArchitecture, size_category: str) -> Dict[str, Any]:
        """Generate on-premise requirements"""
        base_requirements = {
            'minimum_cpu_cores': 2,
            'minimum_ram_gb': 4,
            'minimum_storage_gb': 50,
            'network_bandwidth_mbps': 100,
            'operating_systems': ['Ubuntu 20.04+', 'CentOS 8+', 'RHEL 8+', 'Windows Server 2019+'],
            'container_runtime': ['Docker 20.10+', 'Podman 3.0+'] if architecture == BridgeArchitecture.CONTAINER_BRIDGE else None
        }
        
        # Scale requirements based on size
        if size_category == 'medium':
            base_requirements['minimum_cpu_cores'] = 4
            base_requirements['minimum_ram_gb'] = 8
            base_requirements['minimum_storage_gb'] = 100
            base_requirements['network_bandwidth_mbps'] = 500
        elif size_category == 'large':
            base_requirements['minimum_cpu_cores'] = 8
            base_requirements['minimum_ram_gb'] = 16
            base_requirements['minimum_storage_gb'] = 200
            base_requirements['network_bandwidth_mbps'] = 1000
        
        return base_requirements
    
    def _generate_network_config(self, architecture: BridgeArchitecture, instance: CloudInstanceSpec) -> Dict[str, Any]:
        """Generate network configuration"""
        template = self.architecture_templates[architecture.value]
        
        return {
            'architecture': architecture.value,
            'cloud_provider': instance.provider.value,
            'cloud_region': 'us-east-1',  # Default, customer can choose
            'required_ports': template['network_requirements'],
            'protocols': template['network_requirements']['protocols'],
            'bandwidth_guarantee': f"{instance.max_throughput_mbps}Mbps",
            'latency_target': '<100ms',
            'encryption': 'AES-256' if architecture in [BridgeArchitecture.REVERSE_TUNNEL, BridgeArchitecture.VPN_GATEWAY] else 'TLS 1.3',
            'connection_pooling': True,
            'load_balancing': True if architecture != BridgeArchitecture.API_PROXY else False
        }
    
    def _generate_security_config(self, architecture: BridgeArchitecture, security_level: str) -> Dict[str, Any]:
        """Generate security configuration"""
        base_config = {
            'authentication': 'mutual_tls' if security_level == 'high' else 'api_key',
            'encryption_at_rest': True,
            'encryption_in_transit': True,
            'audit_logging': True,
            'intrusion_detection': security_level in ['high', 'government'],
            'vulnerability_scanning': True,
            'compliance_monitoring': True
        }
        
        if security_level == 'government':
            base_config.update({
                'fips_compliance': True,
                'air_gap_support': True,
                'security_clearance_required': True,
                'audit_trail_immutable': True
            })
        
        return base_config
    
    def _generate_monitoring_config(self, instance: CloudInstanceSpec) -> Dict[str, Any]:
        """Generate monitoring configuration"""
        return {
            'metrics_collection': {
                'infrastructure': ['cpu', 'memory', 'network', 'disk'],
                'application': ['response_time', 'throughput', 'error_rate'],
                'business': ['compliance_scans', 'user_activity', 'data_processed']
            },
            'alerting': {
                'channels': ['email', 'webhook', 'sms'],
                'thresholds': {
                    'cpu_usage': 80,
                    'memory_usage': 85,
                    'disk_usage': 90,
                    'network_utilization': 75
                }
            },
            'dashboards': ['infrastructure', 'application', 'business'],
            'log_retention_days': 90,
            'monitoring_cost_monthly': 15.0
        }
    
    def _generate_backup_strategy(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate backup strategy"""
        return {
            'backup_frequency': 'daily',
            'retention_policy': {
                'daily': '30_days',
                'weekly': '12_weeks',
                'monthly': '12_months',
                'yearly': '7_years'
            },
            'backup_locations': ['cloud_primary', 'cloud_secondary'],
            'encryption': 'AES-256',
            'compression': True,
            'incremental_backups': True,
            'recovery_time_objective': '4_hours',
            'recovery_point_objective': '1_hour'
        }
    
    def get_competitive_analysis(self) -> Dict[str, Any]:
        """Compare our pricing with major competitors"""
        return {
            'cdsi_pricing': {
                'small_deployment': {
                    'monthly_cost': 48.0,  # $22 instance + $26 extras
                    'setup_cost': 0,
                    'deployment_time': '2-4 hours',
                    'features': ['automated_setup', 'terraform_deployment', 'monitoring_included']
                },
                'medium_deployment': {
                    'monthly_cost': 74.0,  # $44 instance + $30 extras
                    'setup_cost': 0,
                    'deployment_time': '4-6 hours',
                    'features': ['high_availability', 'auto_scaling', 'advanced_monitoring']
                },
                'large_deployment': {
                    'monthly_cost': 128.0,  # $88 instance + $40 extras
                    'setup_cost': 0,
                    'deployment_time': '6-12 hours',
                    'features': ['enterprise_support', 'custom_integrations', 'dedicated_resources']
                }
            },
            'competitor_pricing': {
                'onetrust': {
                    'monthly_cost_range': '200-800',
                    'setup_cost': '5000-25000',
                    'deployment_time': '2-6 months',
                    'our_advantage': '60-85% cost savings, 95% faster deployment'
                },
                'trustarc': {
                    'monthly_cost_range': '150-600',
                    'setup_cost': '3000-15000',
                    'deployment_time': '1-4 months',
                    'our_advantage': '50-80% cost savings, 90% faster deployment'
                },
                'privacera': {
                    'monthly_cost_range': '300-1200',
                    'setup_cost': '10000-50000',
                    'deployment_time': '3-8 months',
                    'our_advantage': '70-90% cost savings, 95% faster deployment'
                }
            },
            'value_proposition': {
                'cost_advantage': '50-90% lower than competitors',
                'speed_advantage': '90-95% faster deployment',
                'technical_advantage': 'Cloud-native with on-prem security',
                'compliance_advantage': 'Built-in regulatory intelligence'
            }
        }
    
    def generate_customer_quote(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate customer quote with competitive pricing"""
        config = self.recommend_bridge_configuration(requirements)
        competitive_analysis = self.get_competitive_analysis()
        
        # Determine size category for pricing
        user_count = requirements.get('users', 50)
        if user_count < 100:
            size_category = 'small_deployment'
        elif user_count < 500:
            size_category = 'medium_deployment'
        else:
            size_category = 'large_deployment'
        
        our_pricing = competitive_analysis['cdsi_pricing'][size_category]
        
        return {
            'quote_id': f"CDSI-{datetime.now().strftime('%Y%m%d')}-{requirements.get('customer_id', 'QUOTE')}",
            'customer_requirements': requirements,
            'recommended_configuration': asdict(config),
            'pricing': {
                'monthly_cost': our_pricing['monthly_cost'],
                'setup_cost': our_pricing['setup_cost'],
                'annual_cost': our_pricing['monthly_cost'] * 12,
                'deployment_time': our_pricing['deployment_time'],
                'cost_breakdown': {
                    'cloud_instance': config.cloud_instance.monthly_cost,
                    'network_data_transfer': f"{config.estimated_monthly_cost - config.cloud_instance.monthly_cost - 15.0:.2f}",
                    'monitoring_alerting': 15.0,
                    'support_included': 0.0
                }
            },
            'competitive_advantage': {
                'cost_savings_vs_competitors': '50-90%',
                'deployment_speed_advantage': '90-95%',
                'included_features': our_pricing['features']
            },
            'next_steps': {
                'terraform_deployment': 'Automated via provided scripts',
                'support_during_setup': 'Included in first 30 days',
                'go_live_timeline': our_pricing['deployment_time']
            },
            'generated_at': datetime.now().isoformat(),
            'valid_until': (datetime.now().replace(day=datetime.now().day + 30)).isoformat()
        }

def main():
    """Test the cloud bridge manager"""
    print("🌉 CDSI Cloud Bridge Manager Test")
    print("=" * 50)
    
    # Initialize manager
    bridge_manager = CloudBridgeManager()
    
    # Test different customer scenarios
    scenarios = [
        {
            'name': 'Small Business',
            'requirements': {
                'customer_id': 'small_biz_001',
                'users': 25,
                'devices': 100,
                'security_level': 'medium',
                'budget_preference': 'cost_optimized',
                'monthly_data_transfer_gb': 50,
                'compliance': ['GDPR', 'CCPA']
            }
        },
        {
            'name': 'Enterprise',
            'requirements': {
                'customer_id': 'enterprise_001', 
                'users': 250,
                'devices': 1000,
                'security_level': 'high',
                'budget_preference': 'balanced',
                'monthly_data_transfer_gb': 500,
                'existing_infrastructure': ['vpn'],
                'compliance': ['GDPR', 'SOX', 'HIPAA']
            }
        },
        {
            'name': 'Government',
            'requirements': {
                'customer_id': 'gov_agency_001',
                'users': 500,
                'devices': 2500,
                'security_level': 'government',
                'budget_preference': 'performance',
                'monthly_data_transfer_gb': 1000,
                'compliance': ['FISMA', 'FedRAMP']
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🏛️ {scenario['name']} Scenario:")
        
        # Generate recommendation
        config = bridge_manager.recommend_bridge_configuration(scenario['requirements'])
        
        print(f"Recommended Architecture: {config.architecture_type.value}")
        print(f"Cloud Provider: {config.cloud_instance.provider.value}")
        print(f"Instance Type: {config.cloud_instance.instance_type}")
        print(f"Monthly Cost: ${config.estimated_monthly_cost:.2f}")
        print(f"Deployment Time: {config.deployment_time_hours} hours")
        print(f"Max Throughput: {config.cloud_instance.max_throughput_mbps}Mbps")
        
        # Generate quote
        quote = bridge_manager.generate_customer_quote(scenario['requirements'])
        print(f"\n📊 Cost Comparison:")
        print(f"Our Price: ${quote['pricing']['monthly_cost']}/month")
        print(f"Competitor Range: $150-1200/month")
        print(f"Savings: {quote['competitive_advantage']['cost_savings_vs_competitors']}")
        print(f"Setup Time: {quote['pricing']['deployment_time']} vs 1-8 months")
    
    # Show competitive analysis
    print("\n💼 Competitive Analysis:")
    analysis = bridge_manager.get_competitive_analysis()
    
    print("Value Propositions:")
    for key, value in analysis['value_proposition'].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")

if __name__ == "__main__":
    main()