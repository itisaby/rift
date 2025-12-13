variable "db_name" {
  description = "Name of the database cluster"
  type        = string
}

variable "engine" {
  description = "Database engine (pg, mysql, redis, mongodb, kafka, opensearch)"
  type        = string
  default     = "pg"

  validation {
    condition     = contains(["pg", "mysql", "redis", "mongodb", "kafka", "opensearch"], var.engine)
    error_message = "Engine must be one of: pg, mysql, redis, mongodb, kafka, opensearch."
  }
}

variable "engine_version" {
  description = "Database engine version"
  type        = string
  default     = "15"
}

variable "size" {
  description = "Database cluster size slug"
  type        = string
  default     = "db-s-1vcpu-1gb"

  validation {
    condition     = can(regex("^db-", var.size))
    error_message = "Size must be a valid DigitalOcean database size slug (e.g., db-s-1vcpu-1gb)."
  }
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
  default     = "nyc3"
}

variable "node_count" {
  description = "Number of database nodes (1-3)"
  type        = number
  default     = 1

  validation {
    condition     = var.node_count >= 1 && var.node_count <= 3
    error_message = "Node count must be between 1 and 3."
  }
}

variable "environment" {
  description = "Environment (development, staging, production)"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = list(string)
  default     = []
}

variable "maintenance_day" {
  description = "Day of week for maintenance window"
  type        = string
  default     = "sunday"
}

variable "maintenance_hour" {
  description = "Hour for maintenance window (HH:00:00 format)"
  type        = string
  default     = "02:00:00"
}

variable "vpc_uuid" {
  description = "VPC UUID for private networking"
  type        = string
  default     = null
}

variable "allowed_droplet_ids" {
  description = "List of droplet IDs allowed to connect"
  type        = list(string)
  default     = []
}

variable "allowed_ip_addresses" {
  description = "List of IP addresses allowed to connect"
  type        = list(string)
  default     = []
}

variable "allowed_tags" {
  description = "List of tags for droplets allowed to connect"
  type        = list(string)
  default     = []
}

variable "create_app_user" {
  description = "Create an application database user"
  type        = bool
  default     = false
}

variable "app_user_name" {
  description = "Name for application database user"
  type        = string
  default     = "app_user"
}

variable "create_app_database" {
  description = "Create an application database (PostgreSQL/MySQL only)"
  type        = bool
  default     = false
}

variable "app_database_name" {
  description = "Name for application database"
  type        = string
  default     = "app_db"
}

variable "create_read_replica" {
  description = "Create a read replica"
  type        = bool
  default     = false
}

variable "replica_region" {
  description = "Region for read replica (defaults to primary region)"
  type        = string
  default     = ""
}

variable "replica_size" {
  description = "Size for read replica (defaults to primary size)"
  type        = string
  default     = ""
}
