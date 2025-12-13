# Rift Infrastructure Provisioning Knowledge Base

## Overview
This knowledge base provides comprehensive guidance for provisioning infrastructure on DigitalOcean using Terraform. It includes best practices, examples, and troubleshooting tips.

---

## Terraform Configuration Requirements

### Required Terraform Block
Every Terraform configuration MUST start with this exact block:

```hcl
terraform {
  required_version = ">= 1.0.0"
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}
```

### Required Variables
```hcl
variable "do_token" {
  description = "DigitalOcean API Token"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
  default     = "nyc3"
}

variable "environment" {
  description = "Environment (dev, staging, production)"
  type        = string
  default     = "production"
}

variable "tags" {
  description = "Resource tags"
  type        = list(string)
  default     = ["managed-by-rift"]
}
```

---

## DigitalOcean Resource Types

### 1. Droplets (Virtual Machines)
**Resource:** `digitalocean_droplet`
**Supports Tags:** ✅ Yes

```hcl
resource "digitalocean_droplet" "web" {
  name       = "web-server"
  size       = "s-2vcpu-4gb"
  image      = "ubuntu-22-04-x64"
  region     = var.region
  tags       = var.tags
  monitoring = true
  backups    = true
  
  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y nginx
  EOF
}
```

**Available Sizes:**
- `s-1vcpu-1gb` - $6/month (Basic)
- `s-1vcpu-2gb` - $12/month (Standard)
- `s-2vcpu-4gb` - $24/month (Medium)
- `s-4vcpu-8gb` - $48/month (Large)
- `s-8vcpu-16gb` - $96/month (XL)

**Available Images:**
- `ubuntu-22-04-x64` - Ubuntu 22.04 LTS
- `ubuntu-24-04-x64` - Ubuntu 24.04 LTS
- `debian-12-x64` - Debian 12
- `centos-stream-9-x64` - CentOS Stream 9

### 2. Database Clusters
**Resource:** `digitalocean_database_cluster`
**Supports Tags:** ✅ Yes

```hcl
resource "digitalocean_database_cluster" "postgres" {
  name       = "postgres-cluster"
  engine     = "pg"
  version    = "16"
  size       = "db-s-2vcpu-4gb"
  region     = var.region
  node_count = 2
  tags       = var.tags
}
```

**Supported Engines:**
- `pg` - PostgreSQL (versions: 13, 14, 15, 16)
- `mysql` - MySQL (versions: 8)
- `mongodb` - MongoDB (versions: 6, 7)
- `redis` - Redis (versions: 7)

**Database Sizes:**
- `db-s-1vcpu-1gb` - $15/month
- `db-s-2vcpu-4gb` - $60/month
- `db-s-4vcpu-8gb` - $120/month

### 3. Load Balancers
**Resource:** `digitalocean_loadbalancer`
**Supports Tags:** ❌ No

```hcl
resource "digitalocean_loadbalancer" "web" {
  name   = "web-loadbalancer"
  region = var.region
  
  forwarding_rule {
    entry_protocol  = "http"
    entry_port      = 80
    target_protocol = "http"
    target_port     = 80
  }
  
  healthcheck {
    protocol               = "http"
    port                   = 80
    path                   = "/"
    check_interval_seconds = 10
    response_timeout_seconds = 5
    healthy_threshold      = 3
    unhealthy_threshold    = 3
  }
  
  droplet_ids = [digitalocean_droplet.web.id]
}
```

### 4. Firewalls
**Resource:** `digitalocean_firewall`
**Supports Tags:** ❌ No

```hcl
resource "digitalocean_firewall" "web" {
  name = "web-firewall"
  droplet_ids = [digitalocean_droplet.web.id]
  
  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}
```

### 5. VPC (Virtual Private Cloud)
**Resource:** `digitalocean_vpc`
**Supports Tags:** ❌ No

```hcl
resource "digitalocean_vpc" "main" {
  name   = "app-vpc"
  region = var.region
  ip_range = "10.10.10.0/24"
}
```

### 6. Volumes (Block Storage)
**Resource:** `digitalocean_volume`
**Supports Tags:** ✅ Yes

```hcl
resource "digitalocean_volume" "data" {
  name   = "data-volume"
  size   = 100
  region = var.region
  tags   = var.tags
}

resource "digitalocean_volume_attachment" "data" {
  droplet_id = digitalocean_droplet.web.id
  volume_id  = digitalocean_volume.data.id
}
```

---

## Common Infrastructure Patterns

### Pattern 1: Node.js Web Application with MongoDB

**Use Case:** Deploy a Node.js application with MongoDB database

```hcl
# Web Server Droplet
resource "digitalocean_droplet" "nodejs_app" {
  name       = "nodejs-webapp"
  size       = "s-2vcpu-4gb"
  image      = "ubuntu-22-04-x64"
  region     = var.region
  tags       = var.tags
  monitoring = true
  backups    = true
  
  user_data = <<-EOF
    #!/bin/bash
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs git
    npm install -g pm2
  EOF
}

# MongoDB Cluster
resource "digitalocean_database_cluster" "mongodb" {
  name       = "mongodb-cluster"
  engine     = "mongodb"
  version    = "7"
  size       = "db-s-2vcpu-4gb"
  region     = var.region
  node_count = 1
  tags       = var.tags
}

# Firewall Rules
resource "digitalocean_firewall" "webapp" {
  name = "webapp-firewall"
  droplet_ids = [digitalocean_droplet.nodejs_app.id]
  
  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

# Outputs
output "droplet_id" {
  value = digitalocean_droplet.nodejs_app.id
}

output "droplet_name" {
  value = digitalocean_droplet.nodejs_app.name
}

output "ipv4_address" {
  value = digitalocean_droplet.nodejs_app.ipv4_address
}

output "app_url" {
  value = "http://${digitalocean_droplet.nodejs_app.ipv4_address}"
}

output "database_id" {
  value = digitalocean_database_cluster.mongodb.id
}

output "database_host" {
  value = digitalocean_database_cluster.mongodb.host
}

output "database_port" {
  value = digitalocean_database_cluster.mongodb.port
}

output "connection_string" {
  value     = digitalocean_database_cluster.mongodb.uri
  sensitive = true
}
```

### Pattern 2: Load-Balanced Web Application with Auto-Scaling

**Use Case:** High-availability web application with multiple servers behind a load balancer

```hcl
# Multiple Web Servers
resource "digitalocean_droplet" "web" {
  count      = 3
  name       = "web-server-${count.index + 1}"
  size       = "s-1vcpu-2gb"
  image      = "ubuntu-22-04-x64"
  region     = var.region
  tags       = concat(var.tags, ["web-tier"])
  monitoring = true
  backups    = true
  
  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y nginx
    systemctl enable nginx
    systemctl start nginx
  EOF
}

# Load Balancer
resource "digitalocean_loadbalancer" "web_lb" {
  name   = "web-loadbalancer"
  region = var.region
  
  forwarding_rule {
    entry_protocol  = "http"
    entry_port      = 80
    target_protocol = "http"
    target_port     = 80
  }
  
  forwarding_rule {
    entry_protocol  = "https"
    entry_port      = 443
    target_protocol = "http"
    target_port     = 80
    tls_passthrough = false
  }
  
  healthcheck {
    protocol               = "http"
    port                   = 80
    path                   = "/"
    check_interval_seconds = 10
    response_timeout_seconds = 5
    healthy_threshold      = 3
    unhealthy_threshold    = 3
  }
  
  droplet_ids = digitalocean_droplet.web[*].id
}

# Firewall - Only Allow LB Traffic
resource "digitalocean_firewall" "web_fw" {
  name = "web-firewall"
  droplet_ids = digitalocean_droplet.web[*].id
  
  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_load_balancer_uids = [digitalocean_loadbalancer.web_lb.id]
  }
  
  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

# Outputs
output "lb_id" {
  value = digitalocean_loadbalancer.web_lb.id
}

output "lb_ip" {
  value = digitalocean_loadbalancer.web_lb.ip
}

output "lb_url" {
  value = "http://${digitalocean_loadbalancer.web_lb.ip}"
}

output "droplet_ids" {
  value = digitalocean_droplet.web[*].id
}

output "droplet_ips" {
  value = digitalocean_droplet.web[*].ipv4_address
}
```

### Pattern 3: PostgreSQL Database with Automated Backups

**Use Case:** Production database with high availability and automated backups

```hcl
# VPC for Private Network
resource "digitalocean_vpc" "database_vpc" {
  name     = "database-vpc"
  region   = var.region
  ip_range = "10.10.10.0/24"
}

# PostgreSQL Cluster (Multi-node for HA)
resource "digitalocean_database_cluster" "postgres" {
  name       = "postgres-cluster"
  engine     = "pg"
  version    = "16"
  size       = "db-s-4vcpu-8gb"
  region     = var.region
  node_count = 3
  tags       = var.tags
  
  private_network_uuid = digitalocean_vpc.database_vpc.id
}

# Application Database
resource "digitalocean_database_db" "app_db" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "application_db"
}

# Database User
resource "digitalocean_database_user" "app_user" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "app_user"
}

# Application Server (in same VPC)
resource "digitalocean_droplet" "app_server" {
  name       = "app-server"
  size       = "s-2vcpu-4gb"
  image      = "ubuntu-22-04-x64"
  region     = var.region
  tags       = var.tags
  monitoring = true
  backups    = true
  vpc_uuid   = digitalocean_vpc.database_vpc.id
}

# Outputs
output "database_id" {
  value = digitalocean_database_cluster.postgres.id
}

output "database_host" {
  value = digitalocean_database_cluster.postgres.private_host
}

output "database_port" {
  value = digitalocean_database_cluster.postgres.port
}

output "database_name" {
  value = digitalocean_database_db.app_db.name
}

output "database_user" {
  value = digitalocean_database_user.app_user.name
}

output "connection_string" {
  value     = "postgresql://${digitalocean_database_user.app_user.name}@${digitalocean_database_cluster.postgres.private_host}:${digitalocean_database_cluster.postgres.port}/${digitalocean_database_db.app_db.name}"
  sensitive = true
}

output "vpc_id" {
  value = digitalocean_vpc.database_vpc.id
}

output "app_server_ip" {
  value = digitalocean_droplet.app_server.ipv4_address
}
```

---

## Best Practices

### 1. Security
- **Always use firewalls** to restrict access
- **Use VPC** for database connections (private networking)
- **Enable SSH key authentication** (disable password auth)
- **Restrict database access** to application servers only
- **Use SSL/TLS** for web traffic (HTTPS)

### 2. High Availability
- **Use load balancers** for distributing traffic
- **Deploy multiple nodes** (at least 2-3 for production)
- **Use database clusters** with multiple nodes
- **Enable monitoring** on all resources
- **Set up healthchecks** on load balancers

### 3. Backups & Disaster Recovery
- **Enable automated backups** for droplets (production)
- **Database clusters** have automatic daily backups
- **Use volumes** for persistent data
- **Tag resources** for easy identification
- **Document recovery procedures**

### 4. Cost Optimization
- **Right-size resources** based on actual usage
- **Use monitoring** to identify underutilized resources
- **Start small** and scale up as needed
- **Development environments** can use smaller sizes
- **Clean up unused resources** regularly

### 5. Naming Conventions
- Use descriptive names: `webapp-server`, `postgres-db`, `api-loadbalancer`
- Include environment: `prod-webapp`, `dev-database`
- Use consistent naming patterns
- Avoid special characters (use hyphens, not underscores)

### 6. Tagging Strategy
- Always include: `managed-by-rift`, `environment-{env}`
- Add project tags: `project-name`
- Add tier tags: `web-tier`, `data-tier`
- Add cost center tags for billing

---

## Common Firewall Port Rules

### Web Applications
```hcl
# SSH Access
port_range = "22"
protocol   = "tcp"

# HTTP
port_range = "80"
protocol   = "tcp"

# HTTPS
port_range = "443"
protocol   = "tcp"
```

### Databases
```hcl
# PostgreSQL
port_range = "5432"
protocol   = "tcp"

# MySQL
port_range = "3306"
protocol   = "tcp"

# MongoDB
port_range = "27017"
protocol   = "tcp"

# Redis
port_range = "6379"
protocol   = "tcp"
```

### Application Ports
```hcl
# Node.js (common)
port_range = "3000"
protocol   = "tcp"

# Python Flask/Django
port_range = "5000"
protocol   = "tcp"

# Custom Application
port_range = "8000-9000"
protocol   = "tcp"
```

---

## Troubleshooting Common Issues

### Issue 1: Droplet Creation Fails
**Symptoms:** Terraform apply fails with "droplet limit exceeded"
**Solution:** Contact DigitalOcean support to increase droplet limit or delete unused droplets

### Issue 2: Database Connection Timeout
**Symptoms:** Cannot connect to database from application
**Solution:**
- Check VPC configuration
- Verify firewall rules allow database port
- Use private host for database connections
- Ensure database cluster is in same region as app

### Issue 3: Load Balancer Healthcheck Failing
**Symptoms:** Load balancer marks all droplets as unhealthy
**Solution:**
- Verify application is running on target port
- Check healthcheck path returns 200 OK
- Adjust healthcheck timeout and interval
- Ensure firewall allows load balancer traffic

### Issue 4: High Costs
**Symptoms:** Monthly bill higher than expected
**Solution:**
- Review resource sizes (downsize if possible)
- Delete unused resources (snapshots, volumes, droplets)
- Use monitoring to identify idle resources
- Consider reserved instances for long-term use

---

## Output Guidelines

### Always Include These Outputs:
1. **Resource IDs** - For tracking and management
2. **IP Addresses** - For accessing resources
3. **Connection Strings** - For database access (mark sensitive)
4. **URLs** - For web applications and load balancers
5. **Names** - For identification

### Example Complete Outputs:
```hcl
# Droplet Outputs
output "droplet_id" {
  description = "ID of the droplet"
  value       = digitalocean_droplet.web.id
}

output "droplet_name" {
  description = "Name of the droplet"
  value       = digitalocean_droplet.web.name
}

output "ipv4_address" {
  description = "Public IP address"
  value       = digitalocean_droplet.web.ipv4_address
}

# Database Outputs
output "database_id" {
  description = "Database cluster ID"
  value       = digitalocean_database_cluster.db.id
}

output "database_host" {
  description = "Database host"
  value       = digitalocean_database_cluster.db.host
}

output "database_port" {
  description = "Database port"
  value       = digitalocean_database_cluster.db.port
}

output "connection_string" {
  description = "Database connection string"
  value       = digitalocean_database_cluster.db.uri
  sensitive   = true
}

# Load Balancer Outputs
output "lb_id" {
  description = "Load balancer ID"
  value       = digitalocean_loadbalancer.lb.id
}

output "lb_ip" {
  description = "Load balancer IP"
  value       = digitalocean_loadbalancer.lb.ip
}

output "lb_url" {
  description = "Load balancer URL"
  value       = "http://${digitalocean_loadbalancer.lb.ip}"
}
```

---

## Version Compatibility

### Terraform Version
- Minimum: `>= 1.0.0`
- Recommended: Latest stable (1.9.x)

### DigitalOcean Provider
- Version: `~> 2.0`
- Source: `digitalocean/digitalocean`

### Database Versions
- PostgreSQL: 13, 14, 15, 16 (Recommended: 16)
- MySQL: 8 (Recommended: 8)
- MongoDB: 6, 7 (Recommended: 7)
- Redis: 7 (Recommended: 7)

---

## Quick Reference: Resource Sizing

### Development Environment
- Droplets: `s-1vcpu-1gb` or `s-1vcpu-2gb`
- Database: `db-s-1vcpu-1gb`
- Node Count: 1

### Staging Environment
- Droplets: `s-1vcpu-2gb` or `s-2vcpu-4gb`
- Database: `db-s-2vcpu-4gb`
- Node Count: 2

### Production Environment
- Droplets: `s-2vcpu-4gb` or larger
- Database: `db-s-4vcpu-8gb` or larger
- Node Count: 3+ (for high availability)

---

This knowledge base is maintained by the Rift Infrastructure Management Platform.
For questions or updates, refer to the Rift documentation.
