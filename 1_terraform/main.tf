# 1. VM MASTER (Fedora)
resource "proxmox_virtual_environment_vm" "k8s_master" {
  name        = "k8s-master"
  node_name   = var.target_node
  vm_id       = 101
  description = "Kubernetes Master Node - Fedora"
  tags        = ["k8s", "master", "fedora_44"]

  clone {
    vm_id = 9000
  }

  cpu {
    cores = 2
  }
  memory {
    dedicated = 4096
  }

  disk {
    size = 20
    interface = "scsi0"
  }

  network_device {
    bridge = var.bridge_name
  }

  initialization {
    user_account {
      username = "admin"
      keys     = [var.ssh_public_key]
    }
    ip_config {
      ipv4 {
        address = "10.0.0.101/24"
        gateway = "10.0.0.1"
      }
    }
  }
}

# 2. VM WORKER 1 (Debian)
resource "proxmox_virtual_environment_vm" "k8s_worker1" {
  name        = "k8s-worker1"
  node_name   = var.target_node
  vm_id       = 102
  description = "Kubernetes Worker Node 1 - Debian"
  tags        = ["k8s", "worker", "debian_13"]

  clone {
    vm_id = 9001
  }

  cpu {
    cores = 1
  }
  memory {
    dedicated = 2560
  }

  disk {
    size = 15
    interface = "scsi0"
  }

  network_device {
    bridge = var.bridge_name
  }

  initialization {
    user_account {
      username = "debian"
      keys     = [var.ssh_public_key]
    }
    ip_config {
      ipv4 {
        address = "10.0.0.102/24"
        gateway = "10.0.0.1"
      }
    }
  }
}

# 3. VM WORKER 2 (Debian)
resource "proxmox_virtual_environment_vm" "k8s_worker2" {
  name        = "k8s-worker2"
  node_name   = var.target_node
  vm_id       = 103
  description = "Kubernetes Worker Node 2 - Debian"
  tags        = ["k8s", "worker", "debian_13"]

  clone {
    vm_id = 9001
  }

  cpu {
    cores = 1
  }
  memory {
    dedicated = 2560
  }

  disk {
    size = 15
    interface = "scsi0"
  }

  network_device {
    bridge = var.bridge_name
  }

  initialization {
    user_account {
      username = "debian"
      keys     = [var.ssh_public_key]
    }
    ip_config {
      ipv4 {
        address = "10.0.0.103/24"
        gateway = "10.0.0.1"
      }
    }
  }
}

output "master_ip" {
  value = "10.0.0.101"
  description = "IP del Master Node"
}

output "worker1_ip" {
  value = "10.0.0.102"
  description = "IP del Worker 1"
}

output "worker2_ip" {
  value = "10.0.0.103"
  description = "IP del Worker 2"
}
