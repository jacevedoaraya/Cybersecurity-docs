# Wazuh 4.14.7 Installation and Configuration

Step-by-step guide covering the installation of the **Wazuh agent on Windows Server 2022** and the setup of the **Wazuh server (Manager, Indexer, and Dashboard)** on an Ubuntu VM via PuTTY, including the issues encountered and their solutions.

## Documented Environment

| Component | Detail |
|---|---|
| Wazuh Server (Manager/Indexer/Dashboard) | Ubuntu Server (VM) — IP `192.168.140.129` |
| Agent | Windows Server 2022 Datacenter — IP `192.168.140.130` |
| Agent name | `SERVERHACK` |
| Wazuh version | `4.14.7` |
| Server access | PuTTY (SSH) |
| Agent access | PowerShell (as Administrator) |

## Table of Contents

1. [Installing the Wazuh Agent on Windows Server](#1-installing-the-wazuh-agent-on-windows-server)
2. [First Attempt — Error 1625](#2-first-attempt--error-1625-system-policy)
3. [Fix: Run PowerShell as Administrator](#3-fix-run-powershell-as-administrator)
4. [Verifying and Starting the Agent Service](#4-verifying-and-starting-the-agent-service)
5. [Starting the Wazuh Server via PuTTY](#5-starting-the-wazuh-server-via-putty)
6. [Diagnosing the Manager Startup Error](#6-diagnosing-the-manager-startup-error)
7. [Root Cause: Disk Full](#7-root-cause-disk-full)
8. [Extending the Logical Volume (LVM)](#8-extending-the-logical-volume-lvm)
9. [Final Startup of Manager, Indexer, and Dashboard](#9-final-startup-of-manager-indexer-and-dashboard)
10. [Final Verification: Agent Active](#10-final-verification-agent-active-in-the-dashboard)
11. [Quick Command Reference](#11-quick-command-reference)

---

## 1. Installing the Wazuh Agent on Windows Server

Executed in **PowerShell**, on the Windows Server 2022 machine that would be registered as an agent.

### 1.1 Download the MSI installer

```powershell
Invoke-WebRequest -Uri https://packages.wazuh.com/4.x/windows/wazuh-agent-4.14.7-1.msi `
  -OutFile $env:tmp\wazuh-agent.msi
```

### 1.2 Silent installation, pointing to the manager

```powershell
msiexec.exe /i $env:tmp\wazuh-agent.msi /q WAZUH_MANAGER="192.168.140.129" `
  /l*v $env:tmp\wazuh-install.log
```

> **Note:** with `/q` (silent mode) the command produces no on-screen output. This is normal — the generated log file must be checked to confirm success or failure.

---

## 2. First Attempt — Error 1625 (System Policy)

Checking the log:

```powershell
Get-Content $env:tmp\wazuh-install.log -Tail 30
```

Found:

```
MSI (s): Rejecting product '{D9770AF7-8335-4FEB-927C-C575B11A1F7B}':
Non-assigned apps are disabled for non-admin users.
Note: 1: 1708
Product: Wazuh Agent -- Installation failed.
Info 1625. This installation is forbidden by system policy.
```

**Diagnosis:** error 1625 means Windows Installer blocked the installation due to system policy. The most common cause is running PowerShell **without elevated privileges** (not launched with "Run as Administrator"), even when the logged-in user is an Administrator.

---

## 3. Fix: Run PowerShell as Administrator

1. Close the open PowerShell window.
2. Open PowerShell by right-clicking → **"Run as Administrator"**.
3. Confirm elevation (should return `True`):

```powershell
([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
```

4. Repeat the installation:

```powershell
cd $env:tmp
msiexec /i wazuh-agent.msi /q WAZUH_MANAGER="192.168.140.129" /l*v install.log
```

5. Check the log (no more error 1625):

```powershell
Get-Content install.log -Tail 20
```

The log showed the installation reached `ActionStart(Name=CloseGUI)`, confirming the process finished successfully.

---

## 4. Verifying and Starting the Agent Service

### 4.1 Confirm the service was installed

```powershell
Get-Service WazuhSvc
```

Result: the service existed with status `Stopped`.

### 4.2 Start the service

```powershell
Start-Service WazuhSvc
```

### 4.3 Confirm it's running

```powershell
Get-Service WazuhSvc
```

Expected result: `Running`.

### 4.4 Check the agent log

```powershell
cd "C:\Program Files (x86)\ossec-agent"
Get-Content ossec.log -Tail 20
```

At this point the agent started all its modules (FIM, syscollector, log analysis), but showed this repeated error because the Wazuh server (VM) was still powered off:

```
wazuh-agent: ERROR: (1208): Unable to connect to enrollment service at
'[192.168.140.129]:1515'
```

> This error is expected if the Manager isn't powered on yet — the agent automatically retries the connection.

---

## 5. Starting the Wazuh Server via PuTTY

With SSH access via PuTTY to the Ubuntu VM hosting the Wazuh server, the status of the three main components was checked:

```bash
sudo systemctl status wazuh-manager
sudo systemctl status wazuh-indexer
sudo systemctl status wazuh-dashboard
```

Startup attempt in the recommended order (indexer → manager → dashboard):

```bash
sudo systemctl start wazuh-indexer
sudo systemctl start wazuh-manager
sudo systemctl start wazuh-dashboard
```

To have them start automatically on every VM reboot:

```bash
sudo systemctl enable wazuh-indexer wazuh-manager wazuh-dashboard
```

---

## 6. Diagnosing the Manager Startup Error

The `wazuh-manager` service repeatedly failed with:

```
Active: failed (Result: timeout)
wazuh-manager.service: start operation timed out. Terminating.
Failed to start wazuh-manager.service – Wazuh manager.
```

An attempt was made to start it directly with the control script (bypassing systemd's timeout):

```bash
sudo /var/ossec/bin/wazuh-control start
sudo /var/ossec/bin/wazuh-control status
```

The result showed that **wazuh-apid** (API) was not starting correctly:

```
wazuh-apid did not start correctly.
wazuh-apid not running...
```

### 6.1 Running the API manually to see the real error

Locate the correct path of the script:

```bash
sudo find /var/ossec -iname "*apid*"
```

Path found: `/var/ossec/api/scripts/wazuh_apid.py`

Run it using Wazuh's embedded Python interpreter (not the system one):

```bash
sudo /var/ossec/framework/python/bin/python3 /var/ossec/api/scripts/wazuh_apid.py -f
```

This revealed the real error:

```
2026/08/16 02:14:37 INFO: Starting API in foreground
OSError: [Errno 28] No space left on device
...
File ".../pyDaemonModule.py", line 83, in create_pid
    with open(filename, 'a') as fp:
OSError: [Errno 28] No space left on device
```

---

## 7. Root Cause: Disk Full

Confirmed with:

```bash
df -h
```

The root partition `/dev/mapper/ubuntu--vg-ubuntu--lv` was at **100% usage** (29 GB used out of 29 GB, 0 GB available), even though the VM's virtual disk had 100 GB allocated.

> **Explanation:** the 100 GB physical disk had a single partition (`sda3`) of 58 GB, and of that partition only 29 GB were assigned to the logical volume used by the filesystem. The rest of the space already existed inside the VM but was unused — there was no need to expand the virtual disk or touch the host's disk.

Verifying the disk structure:

```bash
lsblk
sudo vgdisplay
```

---

## 8. Extending the Logical Volume (LVM)

Correct logical volume path:

```bash
sudo lvdisplay
```

Path identified: `/dev/ubuntu-vg/ubuntu-lv`

### 8.1 Extend the logical volume with all available free space

```bash
sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
```

### 8.2 Resize the filesystem

```bash
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv
```

### 8.3 Confirm the new available space

```bash
df -h
```

Result: the `/` partition went from 29 GB to **57 GB**, now at 53% usage with 26 GB available.

---

## 9. Final Startup of Manager, Indexer, and Dashboard

### 9.1 Manager

```bash
sudo systemctl start wazuh-manager
sudo systemctl status wazuh-manager
```

Result: `active (running)`, with all processes up (wazuh-authd, wazuh-db, wazuh-execd, wazuh-analysisd, wazuh-syscheckd, wazuh-remoted, wazuh-logcollector, wazuh-monitord, wazuh-modulesd, wazuh-apid).

### 9.2 Indexer

```bash
sudo systemctl stop wazuh-indexer
sudo systemctl start wazuh-indexer
sudo systemctl status wazuh-indexer
```

Result: `active (running)` once disk space was freed.

### 9.3 Dashboard

```bash
sudo systemctl start wazuh-dashboard
sudo systemctl status wazuh-dashboard
```

Result: `active (running)`.

> The indexer showed cluster errors in `/var/log/wazuh-indexer/wazuh-cluster.log`, left pending for later review, without blocking the overall functioning of the stack.

---

## 10. Final Verification: Agent Active in the Dashboard

Web access: `https://192.168.140.129` → **Endpoints** (Agents) menu.

| Field | Value |
|---|---|
| ID | 001 |
| Name | SERVERHACK |
| IP | 192.168.140.130 |
| Group | default |
| Operating system | Microsoft Windows Server 2022 Datacenter |
| Cluster node | node01 |
| Version | v4.14.7 |
| Status | 🟢 Active |

This confirms the agent installed on the Windows Server is properly registered and actively communicating with the Wazuh Manager.

---

## 11. Quick Command Reference

### Windows Server (PowerShell, as Administrator)

```powershell
# Download the installer
Invoke-WebRequest -Uri https://packages.wazuh.com/4.x/windows/wazuh-agent-4.14.7-1.msi `
  -OutFile $env:tmp\wazuh-agent.msi

# Install pointing to the manager
msiexec /i $env:tmp\wazuh-agent.msi /q WAZUH_MANAGER="192.168.140.129" `
  /l*v $env:tmp\wazuh-install.log

# Verify and start the service
Get-Service WazuhSvc
Start-Service WazuhSvc
Get-Service WazuhSvc

# Check the agent log
Get-Content "C:\Program Files (x86)\ossec-agent\ossec.log" -Tail 20
```

### Wazuh Server (Ubuntu, via PuTTY / SSH)

```bash
# Service status
sudo systemctl status wazuh-manager
sudo systemctl status wazuh-indexer
sudo systemctl status wazuh-dashboard

# Startup (recommended order)
sudo systemctl start wazuh-indexer
sudo systemctl start wazuh-manager
sudo systemctl start wazuh-dashboard

# Automatic startup on VM boot
sudo systemctl enable wazuh-indexer wazuh-manager wazuh-dashboard

# View connected agents (console alternative)
sudo /var/ossec/bin/agent_control -l
```

### Disk Space Troubleshooting (LVM)

```bash
df -h
lsblk
sudo vgdisplay
sudo lvdisplay

# Extend the logical volume with all free space
sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv

# Resize the filesystem
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv
```

---

*Technical documentation for the installation/configuration of Wazuh 4.14.7 (Manager + Indexer + Dashboard on Ubuntu, Agent on Windows Server 2022).*
