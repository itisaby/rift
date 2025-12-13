output "id" {
  description = "Droplet ID"
  value       = digitalocean_droplet.instance.id
}

output "name" {
  description = "Droplet name"
  value       = digitalocean_droplet.instance.name
}

output "ipv4_address" {
  description = "Public IPv4 address"
  value       = digitalocean_droplet.instance.ipv4_address
}

output "ipv4_address_private" {
  description = "Private IPv4 address"
  value       = digitalocean_droplet.instance.ipv4_address_private
}

output "ipv6_address" {
  description = "IPv6 address"
  value       = digitalocean_droplet.instance.ipv6_address
}

output "urn" {
  description = "Droplet URN"
  value       = digitalocean_droplet.instance.urn
}

output "region" {
  description = "Droplet region"
  value       = digitalocean_droplet.instance.region
}

output "size" {
  description = "Droplet size"
  value       = digitalocean_droplet.instance.size
}

output "status" {
  description = "Droplet status"
  value       = digitalocean_droplet.instance.status
}

output "volume_id" {
  description = "Attached volume ID (if created)"
  value       = var.volume_size_gb > 0 ? digitalocean_volume.data_volume[0].id : null
}

output "firewall_id" {
  description = "Firewall ID (if created)"
  value       = var.firewall_rules != null ? digitalocean_firewall.droplet_firewall[0].id : null
}
