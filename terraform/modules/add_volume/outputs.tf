output "volume_id" {
  description = "ID of the created volume"
  value       = digitalocean_volume.storage.id
}

output "volume_name" {
  description = "Name of the created volume"
  value       = digitalocean_volume.storage.name
}

output "size_gb" {
  description = "Size of the volume in GB"
  value       = digitalocean_volume.storage.size
}

output "filesystem_droplet_ids" {
  description = "IDs of droplets attached to this volume"
  value       = digitalocean_volume.storage.droplet_ids
}
