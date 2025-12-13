variable "droplet_id" {
  description = "ID of the droplet to resize"
  type        = number
}

variable "new_size" {
  description = "New size slug (e.g., s-2vcpu-4gb)"
  type        = string

  validation {
    condition     = can(regex("^s-\\d+vcpu-\\d+gb(-intel|-amd)?$", var.new_size))
    error_message = "Size must be a valid DigitalOcean size slug (e.g., s-2vcpu-4gb)."
  }
}

variable "resize_disk" {
  description = "Whether to resize the disk (irreversible if true)"
  type        = bool
  default     = false
}
