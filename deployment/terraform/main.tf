# CDSI Cloud Bridge Terraform Configuration
# Automated deployment for hybrid/on-prem connectivity
# Author: bdstest
# Copyright: 2025 CDSI - Compliance Data Systems Insights

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
    linode = {
      source  = "linode/linode"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# Variables for customer configuration
variable "customer_id" {
  description = "Unique customer identifier"
  type        = string
}

variable "deployment_size" {
  description = "Deployment size: small, medium, or large"
  type        = string
  default     = "small"
  validation {
    condition     = contains(["small", "medium", "large"], var.deployment_size)
    error_message = "Deployment size must be small, medium, or large."
  }
}

variable "cloud_provider" {
  description = "Cloud provider: aws, digitalocean, or linode"
  type        = string
  default     = "linode"  # Most cost-effective
  validation {
    condition     = contains(["aws", "digitalocean", "linode"], var.cloud_provider)
    error_message = "Cloud provider must be aws, digitalocean, or linode."
  }
}

variable "bridge_architecture" {
  description = "Bridge architecture type"
  type        = string
  default     = "reverse_tunnel"
  validation {
    condition     = contains(["reverse_tunnel", "vpn_gateway", "container_bridge", "api_proxy"], var.bridge_architecture)
    error_message = "Bridge architecture must be reverse_tunnel, vpn_gateway, container_bridge, or api_proxy."
  }
}

variable "region" {
  description = "Cloud region for deployment"
  type        = string
  default     = "us-east"
}

variable "customer_cidr" {
  description = "Customer on-premise CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "enable_monitoring" {
  description = "Enable monitoring and alerting"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

# Local values for instance sizing
locals {
  # Instance specifications based on deployment size
  instance_specs = {
    small = {
      aws = {
        instance_type = "t3.medium"
        vcpus        = 2
        memory_gb    = 4
      }
      digitalocean = {
        instance_type = "s-2vcpu-4gb"
        vcpus        = 2
        memory_gb    = 4
      }
      linode = {
        instance_type = "g6-standard-2"
        vcpus        = 2
        memory_gb    = 4
      }
    }
    medium = {
      aws = {
        instance_type = "c5.large"
        vcpus        = 2
        memory_gb    = 4
      }
      digitalocean = {
        instance_type = "c-4"
        vcpus        = 4
        memory_gb    = 8
      }
      linode = {
        instance_type = "g6-standard-4"
        vcpus        = 4
        memory_gb    = 8
      }
    }
    large = {
      aws = {
        instance_type = "c5.xlarge"
        vcpus        = 4
        memory_gb    = 8
      }
      digitalocean = {
        instance_type = "c-8"
        vcpus        = 8
        memory_gb    = 16
      }
      linode = {
        instance_type = "g6-standard-6"
        vcpus        = 6
        memory_gb    = 16
      }
    }
  }
  
  # Selected instance specification
  selected_spec = local.instance_specs[var.deployment_size][var.cloud_provider]
  
  # Common tags
  common_tags = {
    Project     = "CDSI-Bridge"
    Customer    = var.customer_id
    Size        = var.deployment_size
    Architecture = var.bridge_architecture
    ManagedBy   = "Terraform"
    Environment = "production"
    CreatedBy   = "bdstest"
  }
}

# Random password for secure connections
resource "random_password" "bridge_secret" {
  length  = 32
  special = true
}

# Generate SSH key pair for instances
resource "tls_private_key" "bridge_ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "local_file" "private_key" {
  content  = tls_private_key.bridge_ssh.private_key_pem
  filename = "${path.module}/keys/${var.customer_id}_private_key.pem"
  file_permission = "0600"
}

resource "local_file" "public_key" {
  content  = tls_private_key.bridge_ssh.public_key_openssh
  filename = "${path.module}/keys/${var.customer_id}_public_key.pub"
  file_permission = "0644"
}

# AWS Provider Configuration
provider "aws" {
  count  = var.cloud_provider == "aws" ? 1 : 0
  region = "us-east-1"
}

# DigitalOcean Provider Configuration  
provider "digitalocean" {
  count = var.cloud_provider == "digitalocean" ? 1 : 0
}

# Linode Provider Configuration
provider "linode" {
  count = var.cloud_provider == "linode" ? 1 : 0
}

# Include provider-specific modules
module "aws_deployment" {
  count  = var.cloud_provider == "aws" ? 1 : 0
  source = "./modules/aws"
  
  customer_id         = var.customer_id
  deployment_size     = var.deployment_size
  bridge_architecture = var.bridge_architecture
  instance_type       = local.selected_spec.instance_type
  customer_cidr      = var.customer_cidr
  ssh_public_key     = tls_private_key.bridge_ssh.public_key_openssh
  bridge_secret      = random_password.bridge_secret.result
  enable_monitoring  = var.enable_monitoring
  common_tags        = local.common_tags
}

module "digitalocean_deployment" {
  count  = var.cloud_provider == "digitalocean" ? 1 : 0
  source = "./modules/digitalocean"
  
  customer_id         = var.customer_id
  deployment_size     = var.deployment_size
  bridge_architecture = var.bridge_architecture
  instance_size      = local.selected_spec.instance_type
  customer_cidr      = var.customer_cidr
  ssh_public_key     = tls_private_key.bridge_ssh.public_key_openssh
  bridge_secret      = random_password.bridge_secret.result
  enable_monitoring  = var.enable_monitoring
  common_tags        = local.common_tags
}

module "linode_deployment" {
  count  = var.cloud_provider == "linode" ? 1 : 0
  source = "./modules/linode"
  
  customer_id         = var.customer_id
  deployment_size     = var.deployment_size
  bridge_architecture = var.bridge_architecture
  instance_type       = local.selected_spec.instance_type
  customer_cidr      = var.customer_cidr
  ssh_public_key     = tls_private_key.bridge_ssh.public_key_openssh
  bridge_secret      = random_password.bridge_secret.result
  enable_monitoring  = var.enable_monitoring
  common_tags        = local.common_tags
}

# Outputs
output "deployment_info" {
  description = "Bridge deployment information"
  value = {
    customer_id     = var.customer_id
    cloud_provider  = var.cloud_provider
    deployment_size = var.deployment_size
    architecture    = var.bridge_architecture
    instance_spec   = local.selected_spec
    
    # Provider-specific outputs
    aws_info = var.cloud_provider == "aws" ? module.aws_deployment[0].deployment_info : null
    digitalocean_info = var.cloud_provider == "digitalocean" ? module.digitalocean_deployment[0].deployment_info : null
    linode_info = var.cloud_provider == "linode" ? module.linode_deployment[0].deployment_info : null
  }
}

output "connection_info" {
  description = "Connection information for customer setup"
  sensitive   = true
  value = {
    ssh_private_key_path = local_file.private_key.filename
    ssh_public_key_path  = local_file.public_key.filename
    bridge_secret       = random_password.bridge_secret.result
    
    # Provider-specific connection info
    connection_details = var.cloud_provider == "aws" ? module.aws_deployment[0].connection_info : (
      var.cloud_provider == "digitalocean" ? module.digitalocean_deployment[0].connection_info : (
        var.cloud_provider == "linode" ? module.linode_deployment[0].connection_info : null
      )
    )
  }
}

output "customer_setup_guide" {
  description = "Customer setup instructions"
  value = {
    architecture_type = var.bridge_architecture
    setup_steps = [
      "1. Download the on-premise connector package",
      "2. Install Docker (if using container_bridge architecture)",
      "3. Configure firewall rules for outbound connections",
      "4. Run the automated setup script with provided credentials",
      "5. Verify connectivity using the test command",
      "6. Complete the CDSI platform configuration"
    ]
    
    required_ports = var.bridge_architecture == "reverse_tunnel" ? [443, 8443] : (
      var.bridge_architecture == "vpn_gateway" ? [500, 4500] : (
        var.bridge_architecture == "container_bridge" ? [443, 8080] : [443]
      )
    )
    
    estimated_setup_time = var.deployment_size == "small" ? "2-4 hours" : (
      var.deployment_size == "medium" ? "4-6 hours" : "6-12 hours"
    )
  }
}