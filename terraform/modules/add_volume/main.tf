terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

resource "digitalocean_volume" "storage" {
  region                  = var.region
  name                    = var.volume_name
  size                    = var.size_gb
  description             = var.description
  initial_filesystem_type = var.filesystem_type

  tags = var.tags
}

resource "digitalocean_volume_attachment" "attach" {
  count      = var.attach_to_droplet_id != null ? 1 : 0
  droplet_id = var.attach_to_droplet_id
  volume_id  = digitalocean_volume.storage.id
}
