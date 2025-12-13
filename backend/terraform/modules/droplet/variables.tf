variable "droplet_name" {
  description = "Name of the droplet"
  type        = string
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
  default     = "nyc3"
}

variable "size" {
  description = "Droplet size slug"
  type        = string
  default     = "s-1vcpu-1gb"

  validation {
    condition     = can(regex("^s-\\d+vcpu-\\d+gb", var.size))
    error_message = "Size must be a valid DigitalOcean size slug (e.g., s-1vcpu-1gb)."
  }
}

variable "image" {
  description = "Droplet image (distribution)"
  type        = string
  default     = "ubuntu-22-04-x64"
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

variable "ssh_key_ids" {
  description = "List of SSH key IDs to add to the droplet"
  type        = list(number)
  default     = []
}

variable "user_data" {
  description = "User data script for droplet initialization"
  type        = string
  default     = ""
}

variable "firewall_rules" {
  description = "Firewall rules configuration"
  type = object({
    inbound = list(object({
      protocol         = string
      port_range       = string
      source_addresses = list(string)
    }))
  })
  default = {
    inbound = [
      {
        protocol         = "tcp"
        port_range       = "22"
        source_addresses = ["0.0.0.0/0", "::/0"]
      },
      {
        protocol         = "tcp"
        port_range       = "80"
        source_addresses = ["0.0.0.0/0", "::/0"]
      },
      {
        protocol         = "tcp"
        port_range       = "443"
        source_addresses = ["0.0.0.0/0", "::/0"]
      }
    ]
  }
}

variable "enable_ipv6" {
  description = "Enable IPv6 networking"
  type        = bool
  default     = true
}

variable "vpc_uuid" {
  description = "VPC UUID to attach droplet to"
  type        = string
  default     = null
}

variable "volume_size_gb" {
  description = "Size of additional data volume in GB (0 for no volume)"
  type        = number
  default     = 0

  validation {
    condition     = var.volume_size_gb >= 0
    error_message = "Volume size must be 0 or greater."
  }
}
