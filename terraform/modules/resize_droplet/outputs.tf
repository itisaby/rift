output "droplet_id" {
  description = "ID of the resized droplet"
  value       = var.droplet_id
}

output "new_size" {
  description = "New size of the droplet"
  value       = var.new_size
}

output "resize_disk" {
  description = "Whether disk was resized"
  value       = var.resize_disk
}
