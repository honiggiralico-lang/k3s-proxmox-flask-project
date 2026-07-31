variable "pm_endpoint" {
  type        = string
  description = "URL di Proxmox (es. https://10.0.0.51:8006/)"
}

variable "pm_api_token_id" {
  type        = string
  description = "Token ID per l'API di Proxmox (es. root@pam!terraform)"
}

variable "pm_api_token_secret" {
  type        = string
  description = "Secret del Token API"
  sensitive   = true
}

variable "target_node" {
  type        = string
  default     = "pve" 
  description = "Nome del nodo Proxmox dove creare le VM"
}

variable "bridge_name" {
  type        = string
  default     = "vmbr0"
  description = "Bridge di rete di Proxmox per le VM"
}

variable "ssh_public_key" {
  type        = string
  default     = ""
  description = "Chiave pubblica SSH per accedere alle VM"
}
