[Back to Main README](../README.md)

# K3s Encryption at Rest Setup

By default, K3s stores cluster state and Kubernetes Secrets in an unencrypted SQLite database (`/var/lib/rancher/k3s/server/db/state.db`). 
To mitigate the risk of data exposure if the Master Node disk is compromised, we can configure the K8s API Server to encrypt Secrets at rest using AES-CBC.

The following procedure was performed directly on the K3s Master Node.

### Step 1: Generate the Encryption Key
Generate a random 32-byte key and encode it in base64:
```bash
head -c 32 /dev/urandom | base64
```
*Copy the output string. This will be your encryption key.*

### Step 2: Create the Encryption Configuration File
Create the configuration file that the API Server will read to know how to encrypt/decrypt data:
```bash
sudo vi /etc/rancher/k3s/encryption.yaml
```
Paste the following configuration, replacing `<BASE64_KEY>` with the string generated in Step 1:
```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <BASE64_KEY>
      - identity: {} # Allows reading unencrypted secrets during migration
```

### Step 3: Configure K3s Systemd Service
K3s requires a specific flag to pass this configuration to the embedded Kubernetes API Server. Edit the K3s service file:
```bash
sudo vi /etc/systemd/system/k3s.service
```
Find the line starting with `ExecStart=/usr/local/bin/k3s server` and append the `--kube-apiserver-arg` flag:
```ini
ExecStart=/usr/local/bin/k3s server --kube-apiserver-arg="encryption-provider-config=/etc/rancher/k3s/encryption.yaml"
```

### Step 4: Restart K3s
Reload systemd and restart the K3s service to apply the changes:
```bash
sudo systemctl daemon-reload
sudo systemctl restart k3s
```
*Verify that the service is active and running without errors.*
```bash
sudo systemctl status k3s
```

### Step 5: Encrypt Existing Secrets
The new encryption configuration only applies to Secrets created *after* this step. To encrypt existing Secrets (like the MariaDB password), force the API Server to rewrite them:
```bash
kubectl get secrets --all-namespaces -o json | kubectl replace -f -
```

### Step 6: Verification
To verify that the Encryption at Rest is working, attempt to read the raw database file on the Master Node.
If you have a Secret with the password `password` (Base64: `cGFzc3dvcmQ=`), search for it in the database file:
```bash
sudo strings /var/lib/rancher/k3s/server/db/state.db | grep cGFzc3dvcmQ=
```
* If the output is empty, the secret is successfully encrypted at rest.
* If the output returns the base64 string, the secret is still in plaintext (configuration error).
