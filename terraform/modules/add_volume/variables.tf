variable "region" {
  description = "Region to create the volume in"
  type        = string
  default     = "nyc3"
}

variable "volume_name" {
  description = "Name of the volume"
  type        = string
}

variable "size_gb" {
  description = "Size of the volume in GB"
  type        = number

  validation {
    condition     = var.size_gb >= 1 && var.size_gb <= 16384
    error_message = "Volume size must be between 1 and 16384 GB."
  }
}

variable "description" {
  description = "Description of the volume"
  type        = string
  default     = "Managed by Rift"
}

variable "filesystem_type" {
  description = "Initial filesystem type (ext4 or xfs)"
  type        = string
  default     = "ext4"

  validation {
    condition     = contains(["ext4", "xfs"], var.filesystem_type)
    error_message = "Filesystem type must be either ext4 or xfs."
  }
}

variable "attach_to_droplet_id" {
  description = "Optional droplet ID to attach volume to"
  type        = number
  default     = null
}

variable "tags" {
  description = "Tags to apply to the volume"
  type        = list(string)
  default     = ["rift", "managed"]
}
