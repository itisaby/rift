terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

resource "digitalocean_droplet_resize" "resize" {
  droplet_id = var.droplet_id
  new_size   = var.new_size
  resize_disk = var.resize_disk
}

# Wait for droplet to be active after resize
resource "null_resource" "wait_for_active" {
  depends_on = [digitalocean_droplet_resize.resize]

  provisioner "local-exec" {
    command = "sleep 30"
  }
}
