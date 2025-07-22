# Linode deployment module for CDSI Cloud Bridge
# Author: bdstest
# Copyright: 2025 CDSI - Compliance Data Systems Insights

terraform {
  required_providers {
    linode = {
      source  = "linode/linode"
      version = "~> 2.0"
    }
  }
}

variable "customer_id" {
  description = "Customer identifier"
  type        = string
}

variable "deployment_size" {
  description = "Deployment size"
  type        = string
}

variable "bridge_architecture" {
  description = "Bridge architecture type"
  type        = string
}

variable "instance_type" {
  description = "Linode instance type"
  type        = string
}

variable "customer_cidr" {
  description = "Customer CIDR block"
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key"
  type        = string
}

variable "bridge_secret" {
  description = "Bridge connection secret"
  type        = string
  sensitive   = true
}

variable "enable_monitoring" {
  description = "Enable monitoring"
  type        = bool
}

variable "common_tags" {
  description = "Common resource tags"
  type        = map(string)
}

# Create SSH key
resource "linode_sshkey" "bridge_key" {
  label   = "cdsi-bridge-${var.customer_id}"
  ssh_key = var.ssh_public_key
}

# Create Linode instance
resource "linode_instance" "bridge_vm" {
  label           = "cdsi-bridge-${var.customer_id}"
  image          = "ubuntu22.04"
  region         = "us-east"  # Linode Newark datacenter
  type           = var.instance_type
  authorized_keys = [linode_sshkey.bridge_key.ssh_key]
  
  # Bootstrap script
  user_data = base64encode(templatefile("${path.module}/../../scripts/bootstrap.sh", {
    customer_id         = var.customer_id
    bridge_architecture = var.bridge_architecture
    bridge_secret      = var.bridge_secret
    customer_cidr      = var.customer_cidr
    enable_monitoring  = var.enable_monitoring
  }))
  
  tags = [for k, v in var.common_tags : "${k}:${v}"]
}

# Create firewall rules
resource "linode_firewall" "bridge_firewall" {
  label = "cdsi-bridge-fw-${var.customer_id}"
  
  # Inbound rules based on architecture
  dynamic "inbound" {
    for_each = var.bridge_architecture == "vpn_gateway" ? [
      { port = "500", protocol = "UDP" },
      { port = "4500", protocol = "UDP" }
    ] : []
    
    content {
      label    = "${inbound.value.protocol}-${inbound.value.port}"
      action   = "ACCEPT"
      protocol = inbound.value.protocol
      ports    = inbound.value.port
      ipv4     = ["0.0.0.0/0"]
    }
  }
  
  # Always allow SSH and HTTPS
  inbound {
    label    = "SSH"
    action   = "ACCEPT"
    protocol = "TCP"
    ports    = "22"
    ipv4     = ["0.0.0.0/0"]
  }
  
  inbound {
    label    = "HTTPS"
    action   = "ACCEPT"
    protocol = "TCP"
    ports    = "443"
    ipv4     = ["0.0.0.0/0"]
  }
  
  inbound {
    label    = "Bridge-Port"
    action   = "ACCEPT"
    protocol = "TCP"
    ports    = "8443"
    ipv4     = ["0.0.0.0/0"]
  }
  
  # Monitoring port
  inbound {
    label    = "Monitoring"
    action   = "ACCEPT"
    protocol = "TCP"
    ports    = "9090"
    ipv4     = ["0.0.0.0/0"]
  }
  
  # Outbound - allow all
  outbound_policy = "ACCEPT"
  
  # Apply to instance
  linodes = [linode_instance.bridge_vm.id]
}

# Create private IP if needed
resource "linode_instance_ip" "bridge_private" {
  count       = var.bridge_architecture == "vpn_gateway" ? 1 : 0
  linode_id   = linode_instance.bridge_vm.id
  type        = "ipv4"
  public      = false
}

# Create domain record for the bridge (optional)
resource "linode_domain_record" "bridge_dns" {
  count       = 0  # Enable if customer provides domain
  domain_id   = 0  # Customer domain ID
  name        = "bridge-${var.customer_id}"
  record_type = "A"
  target      = linode_instance.bridge_vm.ip_address
  ttl_sec     = 300
}

# Outputs
output "deployment_info" {
  description = "Linode deployment information"
  value = {
    instance_id       = linode_instance.bridge_vm.id
    instance_label    = linode_instance.bridge_vm.label
    instance_type     = linode_instance.bridge_vm.type
    region            = linode_instance.bridge_vm.region
    public_ip         = linode_instance.bridge_vm.ip_address
    private_ip        = var.bridge_architecture == "vpn_gateway" ? linode_instance_ip.bridge_private[0].address : null
    firewall_id       = linode_firewall.bridge_firewall.id
    status            = linode_instance.bridge_vm.status
    estimated_cost    = {
      hourly  = 0.030  # Linode 4GB pricing
      monthly = 22.0
    }
  }
}

output "connection_info" {
  description = "Connection information for customer"
  value = {
    bridge_endpoint   = "https://${linode_instance.bridge_vm.ip_address}:8443"
    monitoring_url    = "http://${linode_instance.bridge_vm.ip_address}:9090"
    ssh_connection    = "ssh root@${linode_instance.bridge_vm.ip_address}"
    tunnel_endpoint   = var.bridge_architecture == "reverse_tunnel" ? "wss://${linode_instance.bridge_vm.ip_address}:8443/tunnel" : null
    vpn_endpoint      = var.bridge_architecture == "vpn_gateway" ? linode_instance.bridge_vm.ip_address : null
    api_endpoint      = "https://${linode_instance.bridge_vm.ip_address}/api/v1"
  }
}