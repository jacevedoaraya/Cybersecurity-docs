# Personalización del Entorno Gráfico en Security Onion (GNOME Shell / Oracle Linux 9)

**Proyecto:** Laboratorio de Security Onion sobre Oracle Linux 9 (instalación mínima, sin escritorio)
**Objetivo:** Convertir una instalación *headless* de Security Onion en un entorno gráfico funcional y usable como estación de trabajo de analista, resolviendo cada incompatibilidad encontrada en el camino.

---

## Contexto

Security Onion se instala por defecto **sin interfaz gráfica** (modo servidor), ya que todos sus servicios corren como contenedores Docker administrados por línea de comandos y se accede a la consola web desde un navegador externo. Para este laboratorio se decidió instalar un entorno gráfico ligero (Xfce/GNOME) directamente sobre la misma VM, lo que expuso varias incompatibilidades propias de instalar un escritorio "a mano" sobre una base mínima de Oracle Linux 9. Este documento reúne, paso a paso, cada problema encontrado y su solución.

---

## 1. Instalación del entorno gráfico base

Security Onion usa repositorios muy restringidos (EPEL + repos propios), sin los repositorios base de Oracle Linux habilitados. El primer paso fue habilitar temporalmente lo necesario e instalar un entorno de escritorio.

```bash
# Habilitar el repositorio EPEL de Oracle Linux 9
sudo dnf install oracle-epel-release-el9 -y

# Instalar el grupo de escritorio Xfce (terminó conviviendo con GNOME Shell,
# que ya estaba parcialmente presente en el sistema base)
sudo dnf groupinstall Xfce -y

# Configurar arranque gráfico por defecto
sudo systemctl set-default graphical.target

# Reiniciar
sudo reboot
```

> **Lección aprendida:** antes de instalar el grupo de escritorio, hubo que confirmar que no hubiese ningún proceso de Salt (`salt-minion`) aplicando cambios (`sudo so-status`) para no interrumpir el *highstate* de Security Onion a mitad de proceso.

---

## 2. Botones de minimizar / maximizar / cerrar en las ventanas

**Síntoma:** las ventanas abrían sin ningún borde ni botones de control.

**Diagnóstico:**
```bash
ps aux | grep xfwm4
```
El gestor de ventanas de Xfce (`xfwm4`) nunca estaba corriendo. Al intentar lanzarlo manualmente:
```bash
xfwm4 --replace
```
la sesión se cerraba por completo. Revisando el log generado:
```bash
xfwm4 --replace > /tmp/xfwm4_error.log 2>&1 &
cat /tmp/xfwm4_error.log
```
se encontró la causa real:
```
Waiting for current window manager (GNOME Shell) on screen :0.0 to exit: Done
```

**Causa raíz:** el sistema ya estaba usando **GNOME Shell** como gestor de ventanas real (no Xfce), y `xfwm4` entraba en conflicto al intentar "reemplazarlo".

**Solución:** en vez de forzar Xfce, se configuraron los botones de ventana directamente en GNOME:
```bash
gsettings set org.gnome.desktop.wm.preferences button-layout ':minimize,maximize,close'
```
Como la sesión corre sobre **Wayland**, un simple *reload* de shell no aplica los cambios; hace falta reiniciar el proceso de GNOME Shell:
```bash
killall -3 gnome-shell
```

**Resultado:** los tres botones de control aparecieron en todas las ventanas de forma inmediata y permanente.

---

## 3. Explorador de archivos (equivalente al Explorador de Windows)

Se instaló **Thunar**, el explorador de archivos nativo de Xfce, como reemplazo ligero del Explorador de Windows:

```bash
sudo dnf install thunar mousepad -y
```

- **Thunar** → navegación de carpetas, copiar/mover/eliminar archivos con clics.
- **Mousepad** → editor de texto simple, equivalente al Bloc de notas.

Ambos quedan disponibles desde el menú de aplicaciones o ejecutando `thunar` / `mousepad` en terminal.

Más adelante, para dar soporte completo a la extensión de íconos de escritorio (ver sección 5), fue necesario instalar también **Nautilus** (el explorador oficial de GNOME), ya que varias extensiones de escritorio dependen de sus `GSettings` internos aunque Thunar sea el explorador principal de uso diario:

```bash
sudo dnf install nautilus -y
```

---

## 4. Barra de tareas / selector de ventanas

**Necesidad:** poder alternar entre varias aplicaciones abiertas (Terminal, Mousepad, navegador) sin depender de atajos de teclado, igual que la barra de tareas de Windows.

**Solución:** instalar la extensión nativa de GNOME Shell para listado de ventanas:

```bash
sudo dnf install gnome-shell-extension-window-list -y
```

Activarla:
```bash
gnome-extensions list
# → window-list@gnome-shell-extensions.gcampax.github.com

gnome-extensions enable window-list@gnome-shell-extensions.gcampax.github.com
```

Al estar en sesión Wayland, activar una extensión no basta con reiniciar el shell; se requiere cerrar sesión por completo:
```bash
gnome-session-quit --logout --no-prompt
```

**Resultado:** apareció una barra en la parte inferior de la pantalla listando todas las ventanas abiertas, con clic para alternar entre ellas — el equivalente funcional de la barra de tareas de Windows.

---

## 5. Íconos en el escritorio (Desktop Icons)

Este fue el problema más complejo de resolver, con dos intentos:

### 5.1 Primer intento — extensión clásica (falló)

```bash
sudo dnf install gnome-shell-extension-desktop-icons -y
gnome-extensions enable desktop-icons@gnome-shell-extensions.gcampax.github.com
gnome-session-quit --logout --no-prompt
```

Los íconos seguían sin aparecer. Revisando el log del sistema:
```bash
sudo journalctl -b 0 | grep -i "desktop-icons\|extension"
```
apareció el error:
```
JS ERROR: TypeError: Extension.desktopManager is null
```

**Causa raíz:** bug de incompatibilidad real entre esa extensión clásica (diseñada para GNOME 40) y la build específica de GNOME Shell 40.10 que trae Oracle Linux 9. No era un problema de configuración, sino del propio código de la extensión.

### 5.2 Segundo intento — Desktop Icons NG / DING (exitoso)

Se optó por compilar e instalar manualmente la extensión moderna **Desktop Icons NG (DING)**, clonando el repositorio oficial y usando la versión (`tag 44`) compatible con GNOME Shell 40–44:

```bash
# Dependencias de compilación (requieren repos base habilitados temporalmente)
sudo dnf config-manager --set-enabled ol9_codeready_builder
sudo dnf install meson ninja-build gettext -y

# Clonar el repositorio y usar la versión correcta
cd ~
git clone https://gitlab.com/rastersoft/desktop-icons-ng.git
cd desktop-icons-ng
git checkout 44

# Compilar e instalar en el home del usuario
chmod +x local_install.sh
./local_install.sh
```

> **Nota:** el directorio `/tmp` en Security Onion está montado con la opción `noexec` por seguridad, por lo que el proyecto tuvo que clonarse y compilarse en `$HOME`, no en `/tmp`.

Activar la extensión (y desactivar la clásica, para evitar conflictos):
```bash
gnome-extensions disable desktop-icons@gnome-shell-extensions.gcampax.github.com
gnome-extensions enable ding@rastersoft.com
gnome-session-quit --logout --no-prompt
```

Los íconos seguían sin aparecer. Diagnóstico en el log:
```bash
sudo journalctl -b 0 | grep -B 3 "ding@rastersoft.*dbusUtils.js:396"
```
Error encontrado:
```
Error getting introspection data over Dbus: GDBus.Error:org.freedesktop.DBus.Error.ServiceUnknown: The name is not activatable
```

**Causa raíz #1:** el proceso auxiliar de DING (`ding.js`, un script GJS independiente) nunca se registró como servicio D-Bus activable al instalarse manualmente en `~/.local/`, así que la extensión de GNOME Shell no podía "despertarlo" automáticamente.

**Solución temporal:** lanzarlo manualmente desde su propio directorio (los `import` del script son relativos):
```bash
cd ~/.local/share/gnome-shell/extensions/ding@rastersoft.com
gjs ding.js &
```

Esto reveló un segundo error:
```
JS ERROR: TypeError: Prefs.nautilusSettings is null
```

**Causa raíz #2:** DING depende de las `GSettings` de **Nautilus**, que no estaba instalado (el sistema solo tenía Thunar).

**Solución definitiva:**
```bash
sudo dnf install nautilus -y
```

Tras instalar Nautilus y relanzar `ding.js`, los íconos aparecieron correctamente en el escritorio.

### 5.3 Hacer el arranque de DING permanente

Como el proceso se lanzó manualmente, se creó una entrada de autoarranque para que se inicie solo en cada sesión gráfica:

```bash
mkdir -p ~/.config/autostart

cat > ~/.config/autostart/ding.desktop << 'EOF'
[Desktop Entry]
Type=Application
Exec=gjs /home/jpaasec/.local/share/gnome-shell/extensions/ding@rastersoft.com/ding.js
Path=/home/jpaasec/.local/share/gnome-shell/extensions/ding@rastersoft.com
Hidden=false
X-GNOME-Autostart-enabled=true
Name=DING Desktop Icons
EOF
```

**Resultado final:** los íconos de `~/Desktop` (carpetas "Home", "Trash" y archivos propios) se muestran de forma permanente sobre el fondo de pantalla, sobreviviendo a reinicios de la VM.

---

## Resumen de aprendizajes clave

| # | Problema | Causa raíz | Solución |
|---|---|---|---|
| 1 | Sin repos suficientes para instalar paquetes | Security Onion limita los repos por seguridad | Habilitar temporalmente `EPEL`, `baseos`, `appstream` y `codeready_builder`, y deshabilitarlos al terminar |
| 2 | Ventanas sin botones de control | `xfwm4` nunca corría; el sistema usaba GNOME Shell | Configurar botones vía `gsettings` en GNOME en vez de forzar Xfce |
| 3 | Sin gestor de archivos gráfico | No venía instalado por defecto | Instalar Thunar (ligero) y, más adelante, Nautilus (dependencia de DING) |
| 4 | Sin forma de alternar ventanas abiertas | Sin extensión de listado de ventanas | Instalar y activar `gnome-shell-extension-window-list` |
| 5 | Íconos de escritorio no aparecían (intento 1) | Bug real de compatibilidad en la extensión clásica con GNOME 40.10 | Migrar a Desktop Icons NG (DING), compilado desde código fuente |
| 6 | DING instalado pero sin íconos (intento 2) | Proceso D-Bus auxiliar nunca se registró/lanzó; además dependía de GSettings de Nautilus | Lanzar `ding.js` manualmente + instalar Nautilus + crear entrada de autoarranque |

**Principio general aplicado en todo el proceso:** ante cualquier fallo silencioso en el entorno gráfico, la fuente de verdad es el log del sistema (`journalctl -b 0`), filtrando por el nombre de la extensión o proceso en cuestión — la interfaz gráfica rara vez muestra el error real, pero el log casi siempre lo tiene.

---

*Documento generado como parte de la bitácora de laboratorio de Security Onion — útil como referencia de troubleshooting de GNOME Shell sobre instalaciones mínimas de Oracle Linux 9 / RHEL 9.*
