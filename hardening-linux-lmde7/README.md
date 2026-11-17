# 🛡️ Hardening de Linux — LMDE 7 (Debian 13)

Proyecto práctico de **endurecimiento (hardening) de un servidor Linux** realizado como parte de un curso de ciberseguridad. Se partió de una instalación limpia de **Linux Mint Debian Edition 7** en una máquina virtual y se aplicaron controles de seguridad en el kernel, la autenticación, el acceso remoto, el servidor web, la prevención de intrusiones y la auditoría del sistema.

Cada control se **verificó con pruebas reales** (ataques simulados, intentos de acceso no autorizado, eventos de auditoría) y se documentaron los **problemas encontrados al aplicar la guía en Debian 13**, junto con su solución.

---

## 📋 Tabla de contenido

1. [Entorno del laboratorio](#-entorno-del-laboratorio)
2. [Resumen de controles aplicados](#-resumen-de-controles-aplicados)
3. [Inventario inicial](#1-inventario-inicial)
4. [Hardening del kernel (sysctl)](#2-hardening-del-kernel-sysctl)
5. [Política de contraseñas (pwquality)](#3-política-de-contraseñas-libpam-pwquality)
6. [SSH con doble factor (2FA)](#4-ssh-con-doble-factor-2fa)
7. [Hardening de Apache2](#5-hardening-de-apache2)
8. [Fail2ban](#6-fail2ban)
9. [Auditoría con auditd](#7-auditoría-con-auditd)
10. [Hallazgos técnicos en Debian 13](#-hallazgos-técnicos-en-debian-13)
11. [Lecciones aprendidas](#-lecciones-aprendidas)
12. [Estructura del repositorio](#-estructura-del-repositorio)

---

## 🖥️ Entorno del laboratorio

| Elemento | Valor |
|---|---|
| Sistema operativo | LMDE 7 "Gigi" (base Debian 13 "Trixie") |
| Kernel | 6.12.116+deb13-amd64 |
| Virtualización | VMware Workstation (red NAT) |
| Hostname | `jpaasec` |
| Servicios expuestos | SSH (22/TCP), HTTP (80/TCP) |
| Cliente de pruebas | Windows (PowerShell, OpenSSH, curl) |
| Fecha | Noviembre de 2026 |

Versiones de los componentes principales:

| Componente | Versión |
|---|---|
| OpenSSH | 10.0p2 Debian 7+deb13u4 |
| Apache | 2.4.71 (Debian) |
| Fail2ban | 1.1.0 |
| auditd | 4.0.2 |

---

## ✅ Resumen de controles aplicados

| # | Área | Controles principales | Estado |
|---|---|---|---|
| 1 | Inventario | Puertos abiertos, usuarios, datos del sistema | ✅ |
| 2 | Kernel / Red | `rp_filter`, `accept_redirects`, `send_redirects`, `log_martians` | ✅ |
| 3 | Kernel / FS | `protected_hardlinks`, `protected_symlinks`, `dmesg_restrict` | ✅ |
| 4 | Contraseñas | `libpam-pwquality`: longitud, complejidad, diccionario, `enforce_for_root` | ✅ |
| 5 | SSH + 2FA | Usuario dedicado, `PermitRootLogin no`, `AllowGroups`, Google Authenticator | ✅ |
| 6 | Apache | `ServerTokens Prod`, 7 cabeceras de seguridad, módulos innecesarios desactivados | ✅ |
| 7 | Fail2ban | 5 jaulas (SSH y Apache), integración con iptables | ✅ |
| 8 | Auditoría | 23 reglas de vigilancia, modo inmutable (`-e 2`) | ✅ |

---

## 1. Inventario inicial

Antes de aplicar cualquier cambio se documentó el estado del sistema.

**Puertos abiertos (antes del hardening):**

| Puerto | Protocolo | Servicio | Exposición |
|---|---|---|---|
| 22 | TCP | OpenSSH 10.0p2 | Toda la red (IPv4 e IPv6) |
| 631 | TCP | CUPS 2.4 (impresión) | Solo localhost |
| 5353 | UDP | Avahi 0.8 (mDNS) | Toda la red |
| Aleatorios | UDP | Avahi | Toda la red |

**Usuarios:** solo `root` y el usuario administrador tenían shell interactiva. Todas las cuentas de servicio usaban `/usr/sbin/nologin`, y no existía ningún otro usuario con UID 0.

```bash
sudo ss -tulnp
sudo nmap -sV localhost
awk -F: '$3==0 || $3>=1000 || $7 ~ /sh$/ {print $1, $3, $4, $7}' /etc/passwd
```

---

## 2. Hardening del kernel (sysctl)

Archivo: `/etc/sysctl.d/hardening.conf`

| Parámetro | Valor | Protección |
|---|---|---|
| `net.ipv4.conf.all.rp_filter` | 1 | IP spoofing |
| `net.ipv4.conf.all.accept_redirects` | 0 | Redirecciones ICMP entrantes |
| `net.ipv4.conf.all.send_redirects` | 0 | Redirecciones ICMP salientes |
| `net.ipv4.conf.all.log_martians` | 1 | Registro de paquetes con direcciones imposibles |
| `fs.protected_hardlinks` | 1 | Abuso de enlaces duros |
| `fs.protected_symlinks` | 1 | Abuso de enlaces simbólicos |
| `kernel.dmesg_restrict` | 1 | Lectura de logs del kernel por usuarios sin privilegios |

<details>
<summary>📄 Ver hardening.conf</summary>

```ini
# Hardening de RED
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.log_martians = 1

# Hardening de File System
fs.protected_hardlinks = 1
fs.protected_symlinks = 1

# Hardening de Kernel
kernel.dmesg_restrict = 1
```
</details>

```bash
sudo sysctl -p /etc/sysctl.d/hardening.conf
dmesg | head -3    # Usuario normal: "Operation not permitted"
```

Los valores se verificaron después de reiniciar la máquina.

---

## 3. Política de contraseñas (libpam-pwquality)

Línea configurada en `/etc/pam.d/common-password`, **antes** de `pam_unix.so`:

```
password  requisite  pam_pwquality.so retry=3 minlen=12 minclass=3 ucredit=-1 lcredit=-1 dcredit=-1 ocredit=-1 maxrepeat=3 maxsequence=3 difok=5 reject_username gecoscheck dictcheck enforce_for_root
```

### Pruebas realizadas

| Contraseña | Resultado | Motivo reportado |
|---|---|---|
| `123456` | ❌ Rechazada | Menos de 1 mayúscula |
| `password` | ❌ Rechazada | Menos de 1 dígito |
| `P@ssword1` | ❌ Rechazada | Menos de 12 caracteres |
| `Usuarioprueba1!` | ❌ Rechazada | Contiene el nombre de usuario |
| `Abc123!Xyz#99` | ❌ Rechazada | No supera la verificación de diccionario (patrones predecibles) |
| Contraseña aleatoria de 14 caracteres | ✅ Aceptada | Cumple todas las reglas |

> 💡 `pam_pwquality` solo informa la **primera regla que falla**, por eso el motivo reportado no siempre coincide con el "más obvio".

> 💡 `Abc123!Xyz#99` cumple longitud y clases de caracteres, pero `dictcheck` detectó secuencias predecibles (`Abc`, `123`, `Xyz`). La política resultó más estricta de lo esperado.

---

## 4. SSH con doble factor (2FA)

### Diseño

- Grupo y usuario dedicados: **`sshadmin`** (con permisos `sudo`).
- Solo el grupo `sshadmin` puede entrar por SSH (`AllowGroups`).
- `root` bloqueado (`PermitRootLogin no`).
- Doble factor: **código TOTP (Google Authenticator) + contraseña**, gestionado por PAM.
- Banner legal antes de autenticar.

### Configuración PAM (`/etc/pam.d/sshd`)

```
# Autenticacion de doble factor - Google Authenticator
auth required pam_google_authenticator.so

@include common-auth
```

Al ir antes de `common-auth`, el servidor pide **primero el código** y **después la contraseña**. No se usó `nullok`: cualquier usuario sin 2FA configurado queda fuera.

<details>
<summary>📄 Ver sshd_config (líneas activas)</summary>

```
Include /etc/ssh/sshd_config.d/*.conf
Port 22
PermitRootLogin no
AllowGroups sshadmin
UsePAM yes
PasswordAuthentication yes
ChallengeResponseAuthentication yes
KbdInteractiveAuthentication yes
AuthenticationMethods keyboard-interactive
MaxAuthTries 3
LoginGraceTime 30
MaxSessions 5
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding no
PermitEmptyPasswords no
IgnoreRhosts yes
Banner /etc/ssh/banner.txt
LogLevel VERBOSE
SyslogFacility AUTH
PrintMotd no
AcceptEnv LANG LC_* COLORTERM NO_COLOR
Subsystem sftp /usr/lib/openssh/sftp-server
```
</details>

### Pruebas realizadas

| Prueba | Resultado |
|---|---|
| `sshd -t` | ✅ Sintaxis válida |
| `sshadmin` con código + contraseña | ✅ Acceso concedido |
| Primer intento lento (aceptando la huella del servidor) | ⏱️ Cortado por `LoginGraceTime 30` |
| `root` con cualquier credencial | ❌ Rechazado; conexión cerrada |

Evidencia en `/var/log/auth.log`:

```
Accepted google_authenticator for sshadmin
Accepted keyboard-interactive/pam for sshadmin from 192.168.140.1 port 55295 ssh2
User root from 192.168.140.1 not allowed because none of user's groups are listed in AllowGroups
Dummy password supplied by PAM. Did OpenSSH 'PermitRootLogin <anything but yes>' ...
Timeout before authentication for connection from 192.168.140.1
srclimit_penalise: ipv4: new 192.168.140.1/32 deferred penalty of 10 seconds ...
```

> 💡 Root está bloqueado por **tres capas** a la vez: `PermitRootLogin no`, `AllowGroups sshadmin` y la ausencia de 2FA (sin `nullok`). OpenSSH 10 además penalizó la IP que agotó el tiempo de autenticación (`PerSourcePenalties`).

---

## 5. Hardening de Apache2

### Antes y después (`curl -I http://localhost`)

| Cabecera | Antes | Después |
|---|---|---|
| `Server` | `Apache/2.4.71 (Debian)` | `Apache` |
| `X-Frame-Options` | — | `SAMEORIGIN` |
| `X-Content-Type-Options` | — | `nosniff` |
| `X-XSS-Protection` | — | `1; mode=block` |
| `Referrer-Policy` | — | `no-referrer-when-downgrade` |
| `Content-Security-Policy` | — | `default-src 'self'; ...` |
| `Permissions-Policy` | — | `geolocation=(), microphone=(), ...` |
| `X-Permitted-Cross-Domain-Policies` | — | `none` |
| `Strict-Transport-Security` | — | No aplicada (el servidor no usa HTTPS) |

El tamaño de la respuesta en `access.log` pasó de **255 a 663 bytes** por las cabeceras añadidas.

### Otros controles

| Control | Resultado |
|---|---|
| `ServerSignature Off` | Las páginas de error ya no muestran la versión |
| `TraceEnable Off` | `TRACE` → **405 Method Not Allowed** |
| Listado de directorios | `/icons/` → **404 Not Found** |
| Módulos desactivados | `autoindex`, `status` (29 → 27 módulos) |
| Usuario de los procesos | Principal: `root`; trabajadores: `www-data` |
| `ServerName` definido | Eliminada la advertencia AH00558 |

<details>
<summary>📄 Ver security.conf</summary>

```apache
ServerTokens Prod
ServerSignature Off

<Directory />
    Options -Indexes -FollowSymLinks -Includes
    AllowOverride None
    Require all denied
</Directory>

# Ajuste Debian: apache2.conf habilita "Indexes" en /var/www/
<Directory /var/www/>
    Options -Indexes
</Directory>

TraceEnable Off

LimitRequestBody 1048576
Timeout 60
KeepAlive On
KeepAliveTimeout 5
MaxKeepAliveRequests 100

<IfModule mod_headers.c>
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Referrer-Policy "no-referrer-when-downgrade"
    Header always set Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; frame-ancestors 'none'"
    Header always set Permissions-Policy "geolocation=(), microphone=(), camera=(), payment=(), usb=()"
    Header always set X-Permitted-Cross-Domain-Policies "none"
    # Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    Header unset X-Powered-By
    Header unset Server
</IfModule>

<FilesMatch "^(\.ht|.*\.bak$|.*\.log$|.*\.conf$)">
    Require all denied
</FilesMatch>

<DirectoryMatch "/(\.(git|svn|hg)|CVS)">
    Require all denied
</DirectoryMatch>
```
</details>

---

## 6. Fail2ban

### Jaulas configuradas

| Jaula | Backend | maxretry | findtime | bantime | Log vigilado |
|---|---|---|---|---|---|
| `sshd` | systemd | 3 | 5 min | 2 h | Journal de `ssh.service` |
| `apache-auth` | auto (pyinotify) | 5 | 10 min | 1 h | `error.log` |
| `apache-badbots` | auto (pyinotify) | 2 | 10 min | 24 h | `access.log` |
| `apache-noscript` | auto (pyinotify) | 6 | 10 min | 1 h | `error.log` |
| `apache-overflows` | auto (pyinotify) | 2 | 10 min | 2 h | `error.log` |

<details>
<summary>📄 Ver jail.local</summary>

```ini
[DEFAULT]
ignoreip = 127.0.0.1/8 ::1
bantime  = 1h
findtime = 10m
maxretry = 5
backend = systemd
banaction = iptables-multiport
banaction_allports = iptables-allports

[sshd]
enabled  = true
port     = ssh
filter   = sshd
backend  = systemd
logpath  = %(sshd_log)s
maxretry = 3
findtime = 5m
bantime  = 2h

[apache-auth]
enabled  = true
port     = http,https
filter   = apache-auth
backend  = auto
logpath  = %(apache_error_log)s
maxretry = 5
bantime  = 1h

[apache-badbots]
enabled  = true
port     = http,https
filter   = apache-badbots
backend  = auto
logpath  = %(apache_access_log)s
maxretry = 2
bantime  = 24h

[apache-noscript]
enabled  = true
port     = http,https
filter   = apache-noscript
backend  = auto
logpath  = %(apache_error_log)s
maxretry = 6

[apache-overflows]
enabled  = true
port     = http,https
filter   = apache-overflows
backend  = auto
logpath  = %(apache_error_log)s
maxretry = 2
bantime  = 2h
```
</details>

### Validación del filtro con datos reales

`fail2ban-regex` sobre `auth.log` detectó los **6 intentos fallidos de root** de las pruebas de SSH (incluida la regla de `AllowGroups`) y **ningún falso positivo** con el acceso legítimo de `sshadmin`.

### Ataque simulado de fuerza bruta

Desde Windows se intentó entrar por SSH con un usuario inexistente:

```
21:48:19  [sshd] Found 192.168.140.1
21:48:43  [sshd] Found 192.168.140.1
21:48:43  [sshd] Found 192.168.140.1
21:48:43  [sshd] Ban 192.168.140.1        ← bloqueo en 24 segundos
21:55:59  [sshd] Unban 192.168.140.1      ← desbloqueo manual
```

| Evidencia | Resultado |
|---|---|
| Conexión en curso | Cortada al aplicarse el ban |
| Siguiente intento | `Connection timed out` |
| Regla creada | `REJECT all -- 192.168.140.1 ... reject-with icmp-port-unreachable` |
| Desbloqueo manual | `fail2ban-client set sshd unbanip` |
| Baneo manual | `fail2ban-client set sshd banip 203.0.113.50` (IP de documentación TEST-NET-3) |
| Persistencia | Los bloqueos se guardan en `fail2ban.sqlite3` y sobreviven a reinicios |

---

## 7. Auditoría con auditd

### Configuración del servicio (`auditd.conf`)

| Parámetro | Antes | Después |
|---|---|---|
| `max_log_file` | 8 MB | **50 MB** |
| `num_logs` | 5 | **10** |
| `space_left` | 75 MB | **100 MB** |
| `log_format` | ENRICHED | ENRICHED |

El historial disponible pasó de ~40 MB a ~500 MB.

### Reglas de vigilancia (23)

| Grupo | Clave | Archivos o carpetas |
|---|---|---|
| Identidad | `usuarios`, `passwords`, `grupos` | `/etc/passwd`, `/etc/shadow`, `/etc/group`, `/etc/gshadow` |
| Privilegios | `sudoers` | `/etc/sudoers`, `/etc/sudoers.d/` |
| Acceso remoto | `ssh-config`, `pam-config` | `/etc/ssh/sshd_config`, `/etc/pam.d/` |
| Kernel | `sysctl` | `/etc/sysctl.conf`, `/etc/sysctl.d/` |
| Logs | `logs-*` | `auth.log`, `syslog`, `fail2ban.log`, `apache2/` |
| Binarios | `binarios` | `/usr/bin/`, `/usr/sbin/` |
| Tareas programadas | `cron` | `crontab`, `cron.d`, `cron.daily`, `cron.hourly`, `/var/spool/cron` |
| Web | `apache-config` | `/etc/apache2/` |
| Módulos del kernel | `modulos-kernel` | `/usr/bin/kmod` |

<details>
<summary>📄 Ver hardening.rules</summary>

```
-D
-b 8192
-f 1

-w /etc/passwd -p wa -k usuarios
-w /etc/shadow -p wa -k passwords
-w /etc/group -p wa -k grupos
-w /etc/gshadow -p wa -k grupos

-w /etc/sudoers -p wa -k sudoers
-w /etc/sudoers.d/ -p wa -k sudoers

-w /etc/ssh/sshd_config -p wa -k ssh-config
-w /etc/pam.d/ -p wa -k pam-config

-w /etc/sysctl.conf -p wa -k sysctl
-w /etc/sysctl.d/ -p wa -k sysctl

-w /var/log/auth.log -p rwa -k logs-auth
-w /var/log/syslog -p rwa -k logs-sistema
-w /var/log/fail2ban.log -p rwa -k logs-fail2ban
-w /var/log/apache2/ -p rwa -k logs-apache

# Debian 13 (usrmerge): /bin y /sbin son enlaces a /usr/bin y /usr/sbin
-w /usr/bin/ -p xa -k binarios
-w /usr/sbin/ -p xa -k binarios

-w /etc/crontab -p wa -k cron
-w /etc/cron.d/ -p wa -k cron
-w /etc/cron.daily/ -p wa -k cron
-w /etc/cron.hourly/ -p wa -k cron
-w /var/spool/cron/ -p wa -k cron

-w /etc/apache2/ -p wa -k apache-config

# insmod, rmmod y modprobe son enlaces a kmod
-w /usr/bin/kmod -p x -k modulos-kernel

# Reglas inmutables hasta el próximo reinicio
-e 2
```
</details>

### Pruebas realizadas

| Prueba | Resultado |
|---|---|
| `touch /etc/passwd` | ✅ Registrado (`key=usuarios`, `auid=jacevedoaraya`, `uid=root`) |
| `touch -r` para restaurar la fecha | ✅ También registrado: intentar borrar huellas deja rastro |
| `cat /etc/passwd` | No registrado (la regla `-p wa` no audita lecturas) |
| Carga de reglas | ✅ Registrada como `CONFIG_CHANGE op=add_rule` (auditd se audita a sí mismo) |
| `sudo true` tras `sudo -k` | ✅ Aparece en `aureport -au` |
| `auditctl -D` con `-e 2` activo | ❌ `Operation not permitted`: ni root puede borrar las reglas |
| Reinicio del sistema | ✅ 23 reglas y `enabled 2` cargados automáticamente |

> 💡 El campo `auid` (audit UID) identifica al **usuario real** detrás de cada acción, aunque haya usado `sudo`. Es la base de la trazabilidad en una auditoría forense.

---

## 🔍 Hallazgos técnicos en Debian 13

Durante el proyecto se detectaron diferencias entre la guía original y el comportamiento real de Debian 13:

| Área | Hallazgo | Solución aplicada |
|---|---|---|
| sysctl | Debian 13 ya no incluye `/etc/sysctl.conf` | Uso de `/etc/sysctl.d/hardening.conf` |
| PAM | `pwquality` no aplica la política cuando root cambia contraseñas | Se agregó `enforce_for_root` |
| SSH | Debian trae `KbdInteractiveAuthentication no` y `X11Forwarding yes`; en `sshd_config` **gana la primera aparición** de cada directiva | Reescritura completa de `sshd_config` |
| SSH | `Protocol 2` es obsoleta desde OpenSSH 7.6 | Directiva comentada |
| SSH | `sshd -T` ya no muestra `challengeresponse` (es un alias) | Verificación con `kbdinteractive` |
| Apache | Advertencia AH00558 en cada arranque | `ServerName` en un archivo de configuración propio |
| Apache | `apache2.conf` habilita `Indexes` en `/var/www/` y anula el `-Indexes` de `<Directory />` | Bloque `<Directory /var/www/> Options -Indexes` |
| Apache | `Header unset Server` no elimina la cabecera | La reduce `ServerTokens Prod` |
| Apache | `apache-htcacheclean` activo sin caché en disco habilitada | Servicio identificado como innecesario |
| Fail2ban | Con `backend = systemd` heredado, las jaulas de Apache nunca leerían sus archivos | `backend = auto` en las jaulas de Apache |
| Fail2ban | La copia de `jail.conf` ya contenía las secciones; agregarlas las duplicaría | Reescritura completa de `jail.local` |
| Fail2ban | El cliente mostró `timed out` aunque la regla era `REJECT` | El aviso ICMP fue filtrado en la red NAT o por el firewall de Windows |
| auditd | `/bin` y `/sbin` son enlaces (usrmerge) | Se vigilan `/usr/bin` y `/usr/sbin` |
| auditd | `insmod`, `rmmod` y `modprobe` son enlaces a `kmod` | Se vigila `/usr/bin/kmod` |
| auditd | `-e 2` impide corregir reglas sin reiniciar | Se activó solo después de probar las reglas |
| auditd | En Debian, auditd **sí permite** `systemctl restart` (`RefuseManualStop=no`) | Documentado como diferencia con RHEL |
| auditd | auditd 4.x advierte "Old style watch rules are slower" | Se mantuvo `-w`; en producción se recomienda `-a always,exit -F path=...` |

---

## 📚 Lecciones aprendidas

1. **Respaldar antes de tocar.** Cada archivo crítico (PAM, `sshd_config`, `security.conf`, `jail.local`, reglas de auditoría) se respaldó antes de modificarlo, y se tomaron instantáneas de la VM antes de cada sección.
2. **Validar antes de reiniciar un servicio:** `sshd -t`, `apache2ctl configtest`, `fail2ban-client -t`.
3. **Las guías no siempre coinciden con la distribución.** Hay que comprobar cómo trata cada programa las directivas duplicadas, el orden de lectura de los archivos y las rutas reales del sistema.
4. **Un control no está aplicado hasta que se prueba.** Cada medida se verificó con un intento real de saltársela.
5. **Los logs cuentan la historia.** Los registros de SSH, Fail2ban, Apache y auditd permitieron reconstruir cada prueba con fecha, hora, IP y usuario.
6. **Defensa en profundidad.** Un atacante que intente entrar como root por SSH se encuentra con `AllowGroups`, `PermitRootLogin no`, el 2FA, `LoginGraceTime`, `MaxAuthTries`, Fail2ban y, finalmente, el registro de auditd.

---

## 📁 Estructura del repositorio

```
hardening-linux-lmde7/
├── README.md
└── evidencias/
    ├── 01-ssh-2fa-login.png
    ├── 02-root-bloqueado.png
    ├── 03-apache-antes-despues.png
    ├── 04-fail2ban-ban.png
    └── 05-auditd-inmutable.png
```

### Evidencias

<!-- Sube tus pantallazos a la carpeta evidencias/ con estos nombres para que se muestren aquí -->

| Prueba | Captura |
|---|---|
| Acceso SSH con 2FA | ![SSH 2FA](evidencias/01-ssh-2fa-login.png) |
| Root bloqueado | ![Root bloqueado](evidencias/02-root-bloqueado.png) |
| Apache antes y después | ![Apache](evidencias/03-apache-antes-despues.png) |
| Fail2ban bloqueando un ataque | ![Fail2ban](evidencias/04-fail2ban-ban.png) |
| auditd inmutable | ![auditd](evidencias/05-auditd-inmutable.png) |

---

## ⚠️ Aviso

Este proyecto se realizó en un **entorno de laboratorio aislado** con fines educativos. Las configuraciones deben revisarse y adaptarse antes de aplicarse en sistemas de producción. No se incluyen contraseñas, claves secretas de 2FA ni códigos de emergencia.

---

**Autor:** jacevedoaraya · Proyecto de curso de ciberseguridad · Noviembre de 2026
