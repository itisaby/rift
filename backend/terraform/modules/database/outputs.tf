output "id" {
  description = "Database cluster ID"
  value       = digitalocean_database_cluster.db.id
}

output "name" {
  description = "Database cluster name"
  value       = digitalocean_database_cluster.db.name
}

output "engine" {
  description = "Database engine"
  value       = digitalocean_database_cluster.db.engine
}

output "version" {
  description = "Database engine version"
  value       = digitalocean_database_cluster.db.version
}

output "host" {
  description = "Database host"
  value       = digitalocean_database_cluster.db.host
}

output "port" {
  description = "Database port"
  value       = digitalocean_database_cluster.db.port
}

output "database" {
  description = "Default database name"
  value       = digitalocean_database_cluster.db.database
}

output "user" {
  description = "Default database user"
  value       = digitalocean_database_cluster.db.user
}

output "password" {
  description = "Default database password"
  value       = digitalocean_database_cluster.db.password
  sensitive   = true
}

output "uri" {
  description = "Database connection URI"
  value       = digitalocean_database_cluster.db.uri
  sensitive   = true
}

output "private_uri" {
  description = "Private database connection URI"
  value       = digitalocean_database_cluster.db.private_uri
  sensitive   = true
}

output "urn" {
  description = "Database cluster URN"
  value       = digitalocean_database_cluster.db.urn
}

output "private_host" {
  description = "Private database host"
  value       = digitalocean_database_cluster.db.private_host
}

output "app_user_name" {
  description = "Application user name (if created)"
  value       = var.create_app_user ? digitalocean_database_user.app_user[0].name : null
}

output "app_user_password" {
  description = "Application user password (if created)"
  value       = var.create_app_user ? digitalocean_database_user.app_user[0].password : null
  sensitive   = true
}

output "app_database_name" {
  description = "Application database name (if created)"
  value       = var.create_app_database && contains(["pg", "mysql"], var.engine) ? digitalocean_database_db.app_db[0].name : null
}

output "replica_id" {
  description = "Read replica ID (if created)"
  value       = var.create_read_replica ? digitalocean_database_replica.read_replica[0].id : null
}

output "replica_uri" {
  description = "Read replica connection URI (if created)"
  value       = var.create_read_replica ? digitalocean_database_replica.read_replica[0].uri : null
  sensitive   = true
}
