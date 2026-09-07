---
technologies: "Supercomputers"
category: "Explanations and use of technology"
difficulty: "Easy"
---

# Supercomputers

## Used material

1. <span id="used-material-1"></span> 

## Why use supercomputers?

## How to use supercomputers?

Notes
- Account use
- Luster
- Lmod
- Python
- SLURM basics
- SLURM sacct
- General monitoring


Notes on LUMI 

Notes on Roihu

1. create the SSH key pair

2. Upload the public key into MyCSC

3. Log in to download the certificate. Certificates last 24 hours

4. Move the certificate into .ssh with a suitable name

5. Check config

```
Host roihu-cpu
HostName roihu-cpu.csc.fi
User siilasjo
IdentityFile ~/.ssh/local-hpc.pem
CertificateFile ~/.ssh/local-hpc-cert.pub

Host roihu-gpu
HostName roihu-gpu.csc.fi
User siilasjo
IdentityFile ~/.ssh/local-hpc.pem
CertificateFile ~/.ssh/local-hpc-cert.pub
```

6. login in with either cpu or gpu

```
ssh roihu-cpu
ssh roihu-gpu
```