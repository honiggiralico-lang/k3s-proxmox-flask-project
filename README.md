# Automated Kubernetes Cluster on Proxmox with Terraform & Ansible

This project implements a fully automated, Infrastructure as Code (IaC) pipeline to provision a multi-node Kubernetes cluster on Proxmox VE. It includes the deployment of a multi-tier containerized application (Flask + Redis) managed entirely through GitOps principles.

## Architecture

- **Control Node (Workstation):** Fedora Linux 44. This machine acts as the DevOps control plane. It runs Terraform, Ansible, `kubectl`, and hosts a local Podman registry to serve container images directly to the cluster.
- **Hypervisor:** Proxmox VE (Bare-metal server on the same LAN, 12GB RAM).
- **Kubernetes Cluster (K3s):**
  - 1x Master Node (Fedora 44 Cloud Image)
  - 2x Worker Nodes (Debian 13 Cloud Images)

## Tech Stack
- **Infrastructure Provisioning:** Terraform (`bpg/proxmox` provider)
- **Configuration Management:** Ansible
- **Container Orchestration:** K3s (Lightweight Kubernetes, CNCF Certified)
- **Containerization:** Podman
- **Application:** Python (Flask) + Redis

## Project Structure
```text
.
├── 1_terraform/       # Proxmox VM provisioning using Cloud-Init
├── 2_ansible/         # K3s installation, cluster bootstrapping & registry config
├── 3_kubernetes/      # Kubernetes manifests (Deployments & Services)
├── app/               # Multi-tier Flask application source code & Dockerfile
└── README.md
```
# Quick Start / Reproduction

## Prerequisites
- A Proxmox VE instance with API tokens enabled.
- Cloud-Init templates created on Proxmox (Fedora and Debian).
- Terraform, Ansible, Podman, and `kubectl` installed on your control node.

---

## Step 1: Infrastructure Provisioning (Terraform)
1. Navigate to the `1_terraform/` directory.
2. Create a `terraform.tfvars` file based on `terraform.tfvars.example` and fill it with your Proxmox API token, SSH key, and network details.
3. Run the following commands:

```bash
terraform init
terraform apply -auto-approve
```

## Step 2: Cluster Configuration (Ansible)

1. Navigate to the 2_ansible/ directory
2. Create an inventory.ini file based on inventory.ini.example using the IPs outputted by Terraform.
3. Run the K3s setup playbook to bootstrap the master and join the workers:
```bash
ansible-playbook -i inventory.ini k3s-setup.yml
```

## Step 3: Local Container Registry Setup

To avoid pushing images to public registries, a local Podman registry is used on the Fedora Control Node:

1. Start the registry on the control node:
```bash
podman run -d -p 5000:5000 --name local-registry --restart=always registry:2
```
2. Allow insecure HTTP connections in /etc/containers/registries.conf on the control node.

3. Run the Ansible playbook to configure K3s nodes to pull from this local registry:
```bash
ansible-playbook -i inventory.ini registry-setup.yml
```

4. Build and push the Flask app image (replace <CONTROL_NODE_IP> with your workstation's LAN IP):
```bash
cd ../app/
podman build -t <CONTROL_NODE_IP>:5000/flask-k8s-app:2.0 .
podman push <CONTROL_NODE_IP>:5000/flask-k8s-app:2.0
```
## Step 4: Application Deployment (Kubernetes)

1. Copy the K3s kubeconfig from the master node to your control node to use kubectl.
2. Navigate to the 3_kubernetes/ directory.
3. Deploy the application:
```bash
kubectl apply -f app-deployment.yaml
```
4. Access the application at http://<MASTER_IP>:30001.

## Key Features & Engineering Challenges Solved

**- Strict Capacity Planning:** Successfully orchestrated 3 VMs and K8s workloads on a bare-metal host limited to 12GB of RAM, optimizing OS choices (using K3s instead of full K8s).
**- Automated Network Configuration:** Bypassed Cloud-Init network interface naming issues by enforcing specific interface configurations via Terraform.
**- Private Container Registry:** Implemented a secure, local HTTP registry using Podman on the control node. Automated the distribution of the registries.yaml configuration to all K3s nodes via Ansible, ensuring a fully self-contained offline-capable deployment.
**- Idempotent Infrastructure:** The entire environment can be destroyed and recreated from scratch in minutes using Terraform and Ansible.
## License
This project is licensed under the MIT License - see the LICENSE file for details.






