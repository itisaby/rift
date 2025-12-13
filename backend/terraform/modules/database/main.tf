terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

resource "digitalocean_database_cluster" "db" {
  name       = var.db_name
  engine     = var.engine
  version    = var.engine_version
  size       = var.size
  region     = var.region
  node_count = var.node_count

  tags = concat(
    var.tags,
    ["managed-by-rift", "environment-${var.environment}"]
  )

  # Enable automated backups
  maintenance_window {
    day  = var.maintenance_day
    hour = var.maintenance_hour
  }

  # Private networking
  private_network_uuid = var.vpc_uuid
}

# Firewall rules for database
resource "digitalocean_database_firewall" "db_firewall" {
  cluster_id = digitalocean_database_cluster.db.id

  # Allow specific droplets if provided
  dynamic "rule" {
    for_each = var.allowed_droplet_ids
    content {
      type  = "droplet"
      value = rule.value
    }
  }

  # Allow specific IP addresses if provided
  dynamic "rule" {
    for_each = var.allowed_ip_addresses
    content {
      type  = "ip_addr"
      value = rule.value
    }
  }

  # Allow specific tags if provided
  dynamic "rule" {
    for_each = var.allowed_tags
    content {
      type  = "tag"
      value = rule.value
    }
  }
}

# Create a database user
resource "digitalocean_database_user" "app_user" {
  count      = var.create_app_user ? 1 : 0
  cluster_id = digitalocean_database_cluster.db.id
  name       = var.app_user_name
}

# Create application database (PostgreSQL/MySQL only)
resource "digitalocean_database_db" "app_db" {
  count      = var.create_app_database && contains(["pg", "mysql"], var.engine) ? 1 : 0
  cluster_id = digitalocean_database_cluster.db.id
  name       = var.app_database_name
}

# Read replica (optional)
resource "digitalocean_database_replica" "read_replica" {
  count      = var.create_read_replica ? 1 : 0
  cluster_id = digitalocean_database_cluster.db.id
  name       = "${var.db_name}-replica"
  region     = var.replica_region != "" ? var.replica_region : var.region
  size       = var.replica_size != "" ? var.replica_size : var.size

  tags = concat(
    var.tags,
    ["managed-by-rift", "environment-${var.environment}", "replica"]
  )
}
