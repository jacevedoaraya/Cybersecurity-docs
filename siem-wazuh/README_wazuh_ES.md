# Instalación y Configuración de Wazuh 4.14.7

Guía paso a paso de la instalación del **agente Wazuh en Windows Server 2022** y la puesta en marcha del **servidor Wazuh (Manager, Indexer y Dashboard)** en una VM Ubuntu vía PuTTY, incluyendo los problemas encontrados y su solución.

## Entorno documentado

| Componente | Detalle |
|---|---|
| Servidor Wazuh (Manager/Indexer/Dashboard) | Ubuntu Server (VM) — IP `192.168.140.129` |
| Agente | Windows Server 2022 Datacenter — IP `192.168.140.130` |
| Nombre del agente | `SERVERHACK` |
| Versión de Wazuh | `4.14.7` |
| Acceso al servidor | PuTTY (SSH) |
| Acceso al agente | PowerShell (como Administrador) |

## Índice

1. [Instalación del agente Wazuh en Windows Server](#1-instalación-del-agente-wazuh-en-windows-server)
2. [Primer intento — Error 1625](#2-primer-intento--error-1625-política-del-sistema)
3. [Solución: PowerShell como Administrador](#3-solución-ejecutar-powershell-como-administrador)
4. [Verificación e inicio del servicio del agente](#4-verificación-e-inicio-del-servicio-del-agente)
5. [Encendido del servidor Wazuh vía PuTTY](#5-encendido-del-servidor-wazuh-vía-putty)
6. [Diagnóstico del error de arranque del Manager](#6-diagnóstico-del-error-de-arranque-del-manager)
7. [Causa raíz: disco lleno](#7-causa-raíz-disco-lleno)
8. [Ampliación del volumen lógico (LVM)](#8-ampliación-del-volumen-lógico-lvm)
9. [Arranque final de Manager, Indexer y Dashboard](#9-arranque-final-de-manager-indexer-y-dashboard)
10. [Verificación final: agente activo](#10-verificación-final-agente-activo-en-el-dashboard)
11. [Referencia rápida de comandos](#11-referencia-rápida-de-comandos)

---

## 1. Instalación del agente Wazuh en Windows Server

Ejecutado en **PowerShell**, en el Windows Server 2022 que se registraría como agente.

### 1.1 Descarga del instalador MSI

```powershell
Invoke-WebRequest -Uri https://packages.wazuh.com/4.x/windows/wazuh-agent-4.14.7-1.msi `
  -OutFile $env:tmp\wazuh-agent.msi
```

### 1.2 Instalación silenciosa, apuntando al manager

```powershell
msiexec.exe /i $env:tmp\wazuh-agent.msi /q WAZUH_MANAGER="192.168.140.129" `
  /l*v $env:tmp\wazuh-install.log
```

> **Nota:** con `/q` (modo silencioso) el comando no muestra salida en pantalla. Es normal — hay que revisar el log generado para confirmar éxito o error.

---

## 2. Primer intento — Error 1625 (política del sistema)

Al revisar el log:

```powershell
Get-Content $env:tmp\wazuh-install.log -Tail 30
```

Se encontró:

```
MSI (s): Rejecting product '{D9770AF7-8335-4FEB-927C-C575B11A1F7B}':
Non-assigned apps are disabled for non-admin users.
Note: 1: 1708
Product: Wazuh Agent -- Installation failed.
Info 1625. This installation is forbidden by system policy.
```

**Diagnóstico:** el error 1625 indica que Windows Installer bloqueó la instalación por política del sistema. La causa más común es ejecutar PowerShell **sin privilegios elevados** (sin "Ejecutar como administrador"), aunque el usuario de la sesión sea Administrador.

---

## 3. Solución: ejecutar PowerShell como Administrador

1. Cerrar la ventana de PowerShell abierta.
2. Abrir PowerShell con clic derecho → **"Ejecutar como administrador"**.
3. Confirmar la elevación (debe devolver `True`):

```powershell
([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
```

4. Repetir la instalación:

```powershell
cd $env:tmp
msiexec /i wazuh-agent.msi /q WAZUH_MANAGER="192.168.140.129" /l*v install.log
```

5. Verificar el log (ya sin el error 1625):

```powershell
Get-Content install.log -Tail 20
```

El log mostró que la instalación llegó hasta `ActionStart(Name=CloseGUI)`, confirmando que el proceso finalizó correctamente.

---

## 4. Verificación e inicio del servicio del agente

### 4.1 Confirmar que el servicio se instaló

```powershell
Get-Service WazuhSvc
```

Resultado: el servicio existía con estado `Stopped`.

### 4.2 Iniciar el servicio

```powershell
Start-Service WazuhSvc
```

### 4.3 Confirmar que quedó corriendo

```powershell
Get-Service WazuhSvc
```

Resultado esperado: `Running`.

### 4.4 Revisar el log del agente

```powershell
cd "C:\Program Files (x86)\ossec-agent"
Get-Content ossec.log -Tail 20
```

En este punto el agente arrancó todos sus módulos (FIM, syscollector, análisis de logs), pero mostró este error repetido porque el servidor Wazuh (VM) aún estaba apagado:

```
wazuh-agent: ERROR: (1208): Unable to connect to enrollment service at
'[192.168.140.129]:1515'
```

> Este error es esperado si el Manager aún no está encendido — el agente reintenta la conexión automáticamente.

---

## 5. Encendido del servidor Wazuh vía PuTTY

Con acceso SSH por PuTTY a la VM Ubuntu del servidor Wazuh, se revisó el estado de los tres componentes:

```bash
sudo systemctl status wazuh-manager
sudo systemctl status wazuh-indexer
sudo systemctl status wazuh-dashboard
```

Intento de arranque en orden recomendado (indexer → manager → dashboard):

```bash
sudo systemctl start wazuh-indexer
sudo systemctl start wazuh-manager
sudo systemctl start wazuh-dashboard
```

Para que arranquen automáticamente en cada reinicio de la VM:

```bash
sudo systemctl enable wazuh-indexer wazuh-manager wazuh-dashboard
```

---

## 6. Diagnóstico del error de arranque del Manager

El servicio `wazuh-manager` falló repetidamente con:

```
Active: failed (Result: timeout)
wazuh-manager.service: start operation timed out. Terminating.
Failed to start wazuh-manager.service – Wazuh manager.
```

Se intentó arrancarlo directo con el script de control (evita el timeout de systemd):

```bash
sudo /var/ossec/bin/wazuh-control start
sudo /var/ossec/bin/wazuh-control status
```

El resultado mostró que **wazuh-apid** (API) no arrancaba correctamente:

```
wazuh-apid did not start correctly.
wazuh-apid not running...
```

### 6.1 Ejecución manual del API para ver el error real

Localizar la ruta correcta del script:

```bash
sudo find /var/ossec -iname "*apid*"
```

Ruta encontrada: `/var/ossec/api/scripts/wazuh_apid.py`

Ejecutado con el intérprete de Python embebido de Wazuh (no el del sistema):

```bash
sudo /var/ossec/framework/python/bin/python3 /var/ossec/api/scripts/wazuh_apid.py -f
```

Esto reveló el error real:

```
2026/08/16 02:14:37 INFO: Starting API in foreground
OSError: [Errno 28] No space left on device
...
File ".../pyDaemonModule.py", line 83, in create_pid
    with open(filename, 'a') as fp:
OSError: [Errno 28] No space left on device
```

---

## 7. Causa raíz: disco lleno

Confirmado con:

```bash
df -h
```

La partición raíz `/dev/mapper/ubuntu--vg-ubuntu--lv` estaba al **100% de uso** (29 GB usados de 29 GB, 0 disponibles), a pesar de que el disco virtual de la VM tenía 100 GB asignados.

> **Explicación:** el disco físico de 100 GB solo tenía una partición (`sda3`) de 58 GB, y de esa partición solo 29 GB estaban asignados al volumen lógico usado por el sistema de archivos. El resto del espacio ya existía dentro de la VM pero no estaba en uso — no fue necesario ampliar el disco virtual ni afectar el disco del host.

Verificación de la estructura del disco:

```bash
lsblk
sudo vgdisplay
```

---

## 8. Ampliación del volumen lógico (LVM)

Ruta correcta del volumen lógico:

```bash
sudo lvdisplay
```

Ruta identificada: `/dev/ubuntu-vg/ubuntu-lv`

### 8.1 Extender el volumen lógico con el espacio libre disponible

```bash
sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
```

### 8.2 Redimensionar el sistema de archivos

```bash
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv
```

### 8.3 Confirmar el nuevo espacio disponible

```bash
df -h
```

Resultado: la partición `/` pasó de 29 GB a **57 GB**, quedando al 53% de uso con 26 GB disponibles.

---

## 9. Arranque final de Manager, Indexer y Dashboard

### 9.1 Manager

```bash
sudo systemctl start wazuh-manager
sudo systemctl status wazuh-manager
```

Resultado: `active (running)`, con todos los procesos activos (wazuh-authd, wazuh-db, wazuh-execd, wazuh-analysisd, wazuh-syscheckd, wazuh-remoted, wazuh-logcollector, wazuh-monitord, wazuh-modulesd, wazuh-apid).

### 9.2 Indexer

```bash
sudo systemctl stop wazuh-indexer
sudo systemctl start wazuh-indexer
sudo systemctl status wazuh-indexer
```

Resultado: `active (running)` una vez liberado el espacio en disco.

### 9.3 Dashboard

```bash
sudo systemctl start wazuh-dashboard
sudo systemctl status wazuh-dashboard
```

Resultado: `active (running)`.

> El indexer mostró errores de cluster en `/var/log/wazuh-indexer/wazuh-cluster.log`, pendientes de revisión posterior, sin bloquear el funcionamiento general del stack.

---

## 10. Verificación final: agente activo en el Dashboard

Acceso web: `https://192.168.140.129` → menú **Endpoints** (Agents).

| Campo | Valor |
|---|---|
| ID | 001 |
| Nombre | SERVERHACK |
| IP | 192.168.140.130 |
| Grupo | default |
| Sistema operativo | Microsoft Windows Server 2022 Datacenter |
| Cluster node | node01 |
| Versión | v4.14.7 |
| Estado | 🟢 Active |

Con esto se confirma que el agente instalado en el Windows Server está correctamente registrado y comunicándose de forma activa con el Manager de Wazuh.

---

## 11. Referencia rápida de comandos

### Windows Server (PowerShell, como Administrador)

```powershell
# Descargar el instalador
Invoke-WebRequest -Uri https://packages.wazuh.com/4.x/windows/wazuh-agent-4.14.7-1.msi `
  -OutFile $env:tmp\wazuh-agent.msi

# Instalar apuntando al manager
msiexec /i $env:tmp\wazuh-agent.msi /q WAZUH_MANAGER="192.168.140.129" `
  /l*v $env:tmp\wazuh-install.log

# Verificar e iniciar el servicio
Get-Service WazuhSvc
Start-Service WazuhSvc
Get-Service WazuhSvc

# Revisar el log del agente
Get-Content "C:\Program Files (x86)\ossec-agent\ossec.log" -Tail 20
```

### Servidor Wazuh (Ubuntu, vía PuTTY / SSH)

```bash
# Estado de los servicios
sudo systemctl status wazuh-manager
sudo systemctl status wazuh-indexer
sudo systemctl status wazuh-dashboard

# Arranque (orden recomendado)
sudo systemctl start wazuh-indexer
sudo systemctl start wazuh-manager
sudo systemctl start wazuh-dashboard

# Arranque automático al iniciar la VM
sudo systemctl enable wazuh-indexer wazuh-manager wazuh-dashboard

# Ver agentes conectados (alternativa por consola)
sudo /var/ossec/bin/agent_control -l
```

### Diagnóstico de espacio en disco (LVM)

```bash
df -h
lsblk
sudo vgdisplay
sudo lvdisplay

# Extender el volumen lógico con todo el espacio libre
sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv

# Redimensionar el sistema de archivos
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv
```

---

*Documentación técnica de instalación/configuración de Wazuh 4.14.7 (Manager + Indexer + Dashboard en Ubuntu, Agente en Windows Server 2022).*
