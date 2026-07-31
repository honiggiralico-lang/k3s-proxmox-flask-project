terraform {
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "0.50.0" # Puoi anche mettere ">= 0.50.0" per avere l'ultima
    }
  }
}

provider "proxmox" {
  endpoint = var.pm_endpoint
  api_token = "${var.pm_api_token_id}=${var.pm_api_token_secret}"
  insecure = true 
}
