terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

resource "digitalocean_droplet" "instance" {
  name   = var.droplet_name
  region = var.region
  size   = var.size
  image  = var.image

  tags = concat(
    var.tags,
    ["managed-by-rift", "environment-${var.environment}"]
  )

  # User data for initialization
  user_data = var.user_data

  # SSH keys
  ssh_keys = var.ssh_key_ids

  # Enable monitoring
  monitoring = true

  # Enable backups if production
  backups = var.environment == "production" ? true : false

  # IPv6
  ipv6 = var.enable_ipv6

  # VPC
  vpc_uuid = var.vpc_uuid
}

# Attach firewall if provided
resource "digitalocean_firewall" "droplet_firewall" {
  count = var.firewall_rules != null ? 1 : 0

  name = "${var.droplet_name}-firewall"

  droplet_ids = [digitalocean_droplet.instance.id]

  # Inbound rules from variable
  dynamic "inbound_rule" {
    for_each = var.firewall_rules != null ? var.firewall_rules.inbound : []
    content {
      protocol         = inbound_rule.value.protocol
      port_range       = inbound_rule.value.port_range
      source_addresses = inbound_rule.value.source_addresses
    }
  }

  # Allow all outbound traffic
  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

# Optional: Create a volume if size is specified
resource "digitalocean_volume" "data_volume" {
  count = var.volume_size_gb > 0 ? 1 : 0

  region      = var.region
  name        = "${var.droplet_name}-data"
  size        = var.volume_size_gb
  description = "Data volume for ${var.droplet_name}"

  tags = concat(
    var.tags,
    ["managed-by-rift", "environment-${var.environment}"]
  )
}

# Attach volume to droplet
resource "digitalocean_volume_attachment" "data_volume_attachment" {
  count = var.volume_size_gb > 0 ? 1 : 0

  droplet_id = digitalocean_droplet.instance.id
  volume_id  = digitalocean_volume.data_volume[0].id
}
