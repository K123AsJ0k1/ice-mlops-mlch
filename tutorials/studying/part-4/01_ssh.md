---
technologies: "SSH"
category: "Explanation and use of technology"
difficulty: "Easy"
---

# SSH

## Used material

1. <span id="used-material-1"></span> [What is SSH (Secure Shell)?](https://www.ssh.com/academy/ssh)

2. <span id="used-material-2"></span> [Get started with OpenSSH for Windows](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse?tabs=gui&pivots=windows-11)

3. <span id="used-material-3"></span> [OpenSSH Server](https://ubuntu.com/server/docs/how-to/security/openssh-server/)

4. <span id="used-material-4"></span> [SSH on MacOs for noobs](https://medium.com/@harrison_46485/ssh-on-macos-for-noobs-3ed636313e1d)

5. <span id="used-material-5"></span> [SSH Essentials](https://www.digitalocean.com/community/tutorials/ssh-essentials-working-with-ssh-servers-clients-and-keys)

6. <span id="used-material-6"></span> [SSH simplified using SSH Config](https://blog.tarkalabs.com/ssh-simplified-using-ssh-config-161406ba75d7)

7. <span id="used-material-7"></span> [SSH Tunneling](https://www.ssh.com/academy/ssh/tunneling-example)

## Why use SSH?

SSH is widely used for the following reasons:

- Most common tool for secure communications between remote machines (mature)

- Easy to use either via terminal or software (abstracted)

- Widely supported by most operating systems (interoperable)

These make SSH the default networking tool that enables us to manage remote systems and forward connections between separated software.

## How to use SSH?

You need to confirm that your device has a working SSH client [(1)](#used-material-1). Please check the details using available documentation for your operating system, such as Windows 11 [(2)](#used-material-2), Ubuntu 24.04 [(3)](#used-material-3) and MacOS [(4)](#used-material-4). By default, we will be operating Linux-based remote computers, which is why we recommend familiarizing yourself with the details [(5)](#used-material-5). For us, the most used commands are:

- Connecting to a remote server

```
ssh [SERVER_USERNAME]@[SERVER_IP_ADDRESS]
```

- Connecting to a remote server with a local forward to get a connection

```
ssh -L [CLIENT_HOST_ADDRESS]:[CLIENT_HOST_PORT] [SERVER_HOST_ADDRESS]:[SERVER_HOST_PORT] [SERVER_USERNAME]@[SERVER_IP_ADDRESS]
```

- Connecting to a remote server with a remote forward to give a connection

```
ssh -R [SERVER_HOST_ADDRESS]:[SERVER_HOST_PORT] [CLIENT_HOST_ADDRESS]:[CLIENT_HOST_PORT] [SERVER_USERNAME]@[SERVER_IP_ADDRESS]
```

## SSH config

The main problem with manual SSH use via the terminal is the need to enter long exact commands. SSH can help with this via a config file, usually located in a .ssh folder within the personal folder [(6)](#used-material-6). We can create it in the following way:

```
cd .ssh
nano config
```

Now, we recommend having the following blocks:

```
Host CPU-cpouta
Hostname [VM_FLOATING_IP]
User [VM_USER]
IdentityFile ~/.ssh/local-cpouta.pem

Host GPU-cpouta
Hostname [VM_FLOATING_IP]
User [VM_USER]
IdentityFile ~/.ssh/local-cpouta.pem
```

This format allows us to simply write the hostname to create a connection. For example, this command connects your computer to the remote virtual machine:

```
ssh GPU-cpouta
```

We will also use in the future multiple remote and local forward tunnels [(7)](#used-material-7) to connect our containers, which we can simplify into a single command in the following way:

```
Host lf-GPU-cpouta
Hostname [VM_FLOATING_IP]
User [VM_USER]
IdentityFile ~/.ssh/local-cpouta.pem
LocalForward [CLIENT_HOST_ADDRESS]:[CLIENT_HOST_PORT] [SERVER_HOST_ADDRESS]:[SERVER_HOST_PORT]
LocalForward [CLIENT_HOST_ADDRESS]:[CLIENT_HOST_PORT] [SERVER_HOST_ADDRESS]:[SERVER_HOST_PORT]

Host rf-GPU-cpouta
Hostname [VM_FLOATING_IP]
User [VM_USER]
IdentityFile ~/.ssh/local-cpouta.pem
RemoteForward [SERVER_HOST_ADDRESS]:[SERVER_HOST_PORT] [CLIENT_HOST_ADDRESS]:[CLIENT_HOST_PORT]
RemoteForward [SERVER_HOST_ADDRESS]:[SERVER_HOST_PORT] [CLIENT_HOST_ADDRESS]:[CLIENT_HOST_PORT]
```

Be aware that SSH provides many commands, whose use depends on the targeted SSH server. If the server isn't configured correctly, the commands will fail. For example, the remote forward commands in rf-GPU-cpouta require the server configuration to have GatewayPorts clientspecified. We will mention these details when they become relevant.

---