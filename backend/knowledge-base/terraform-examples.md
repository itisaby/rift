# Terraform Examples for Common Scenarios

## Example 1: Node.js Web App with MongoDB

```hcl
# Node.js Droplet
resource "digitalocean_droplet" "webapp" {
  name   = "nodejs-webapp"
  size   = "s-2vcpu-4gb"
  image  = "ubuntu-22-04-x64"
  region = var.region
  tags   = var.tags
  
  monitoring = true
  backups    = true
  
  user_data = <<-EOF
    #!/bin/bash
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
    npm install -g pm2
  EOF
}

# MongoDB Database
resource "digitalocean_database_cluster" "mongodb" {
  name       = "mongodb-cluster"
  engine     = "mongodb"
  version    = "7"
  size       = "db-s-2vcpu-4gb"
  region     = var.region
  node_count = 1
  tags       = var.tags
}

# Firewall
resource "digitalocean_firewall" "webapp_fw" {
  name = "webapp-firewall"
  
  droplet_ids = [digitalocean_droplet.webapp.id]
  
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
  value = digitalocean_droplet.webapp.id
}

output "droplet_name" {
  value = digitalocean_droplet.webapp.name
}

output "ipv4_address" {
  value = digitalocean_droplet.webapp.ipv4_address
}

output "app_url" {
  value = "http://${digitalocean_droplet.webapp.ipv4_address}"
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

## Example 2: Load-Balanced Web Application

```hcl
# Multiple Web Servers
resource "digitalocean_droplet" "web" {
  count  = 3
  name   = "web-server-${count.index + 1}"
  size   = "s-1vcpu-2gb"
  image  = "ubuntu-22-04-x64"
  region = var.region
  tags   = var.tags
  
  monitoring = true
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

# Firewall
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

## Example 3: PostgreSQL Database with Backups

```hcl
# VPC for Private Network
resource "digitalocean_vpc" "main" {
  name   = "database-vpc"
  region = var.region
}

# PostgreSQL Cluster
resource "digitalocean_database_cluster" "postgres" {
  name       = "postgres-cluster"
  engine     = "pg"
  version    = "16"
  size       = "db-s-2vcpu-4gb"
  region     = var.region
  node_count = 2
  tags       = var.tags
  
  private_network_uuid = digitalocean_vpc.main.id
}

# Database
resource "digitalocean_database_db" "app_db" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "application_db"
}

# Database User
resource "digitalocean_database_user" "app_user" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "app_user"
}

# Outputs
output "database_id" {
  value = digitalocean_database_cluster.postgres.id
}

output "database_host" {
  value = digitalocean_database_cluster.postgres.host
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
  value     = digitalocean_database_cluster.postgres.uri
  sensitive = true
}

output "vpc_id" {
  value = digitalocean_vpc.main.id
}
```

## Best Practices

1. **Always use outputs** for resource IDs, IPs, and connection information
2. **Enable monitoring and backups** for production resources
3. **Use VPC** for database connections (private networking)
4. **Set proper firewall rules** - restrict access where possible
5. **Use count parameter** for multiple similar resources
6. **Include healthchecks** on load balancers
7. **Tag resources** appropriately for organization
8. **Use appropriate sizes** based on workload requirements
