# Desktop Environment Customization on Security Onion (GNOME Shell / Oracle Linux 9)

**Project:** Security Onion lab on Oracle Linux 9 (minimal installation, no desktop environment)
**Objective:** Turn a *headless* Security Onion installation into a functional, usable graphical workstation for an analyst, solving every incompatibility found along the way.

---

## Context

Security Onion is installed by default **without a graphical interface** (server mode), since all of its services run as Docker containers managed from the command line, and the web console is accessed from an external browser. For this lab, it was decided to install a lightweight desktop environment (Xfce/GNOME) directly on the same VM, which exposed several incompatibilities specific to installing a desktop "by hand" on top of a minimal Oracle Linux 9 base. This document collects, step by step, every issue encountered and its solution.

---

## 1. Installing the base graphical environment

Security Onion uses very restricted repositories (EPEL + its own repos), without Oracle Linux's base repositories enabled. The first step was to temporarily enable what was needed and install a desktop environment.

```bash
# Enable the Oracle Linux 9 EPEL repository
sudo dnf install oracle-epel-release-el9 -y

# Install the Xfce desktop group (ended up coexisting with GNOME Shell,
# which was already partially present in the base system)
sudo dnf groupinstall Xfce -y

# Set graphical boot as default
sudo systemctl set-default graphical.target

# Reboot
sudo reboot
```

> **Lesson learned:** before installing the desktop group, it was necessary to confirm that no Salt process (`salt-minion`) was applying changes (`sudo so-status`), in order to avoid interrupting Security Onion's *highstate* midway through.

---

## 2. Minimize / maximize / close buttons on windows

**Symptom:** windows opened with no border or control buttons at all.

**Diagnosis:**
```bash
ps aux | grep xfwm4
```
Xfce's window manager (`xfwm4`) was never running. When trying to launch it manually:
```bash
xfwm4 --replace
```
the session would close completely. Reviewing the generated log:
```bash
xfwm4 --replace > /tmp/xfwm4_error.log 2>&1 &
cat /tmp/xfwm4_error.log
```
revealed the real cause:
```
Waiting for current window manager (GNOME Shell) on screen :0.0 to exit: Done
```

**Root cause:** the system was already using **GNOME Shell** as the actual window manager (not Xfce), and `xfwm4` conflicted with it when trying to "replace" it.

**Solution:** instead of forcing Xfce, the window buttons were configured directly in GNOME:
```bash
gsettings set org.gnome.desktop.wm.preferences button-layout ':minimize,maximize,close'
```
Since the session runs on **Wayland**, a simple shell *reload* does not apply the changes; the GNOME Shell process needs to be restarted:
```bash
killall -3 gnome-shell
```

**Result:** the three control buttons appeared on all windows immediately and permanently.

---

## 3. File explorer (equivalent to Windows Explorer)

**Thunar**, Xfce's native file explorer, was installed as a lightweight replacement for Windows Explorer:

```bash
sudo dnf install thunar mousepad -y
```

- **Thunar** → folder navigation, copying/moving/deleting files with clicks.
- **Mousepad** → simple text editor, equivalent to Notepad.

Both are available from the applications menu or by running `thunar` / `mousepad` in a terminal.

Later, to fully support the desktop icons extension (see section 5), it was also necessary to install **Nautilus** (GNOME's official file manager), since several desktop extensions depend on its internal `GSettings` even though Thunar remains the main daily-use file explorer:

```bash
sudo dnf install nautilus -y
```

---

## 4. Taskbar / window switcher

**Need:** being able to switch between several open applications (Terminal, Mousepad, browser) without relying on keyboard shortcuts, similar to the Windows taskbar.

**Solution:** install GNOME Shell's native window-listing extension:

```bash
sudo dnf install gnome-shell-extension-window-list -y
```

Enable it:
```bash
gnome-extensions list
# → window-list@gnome-shell-extensions.gcampax.github.com

gnome-extensions enable window-list@gnome-shell-extensions.gcampax.github.com
```

Since the session runs on Wayland, enabling an extension is not enough with just a shell restart; a full logout is required:
```bash
gnome-session-quit --logout --no-prompt
```

**Result:** a bar appeared at the bottom of the screen listing all open windows, clickable to switch between them — the functional equivalent of the Windows taskbar.

---

## 5. Desktop icons

This was the most complex issue to solve, requiring two attempts:

### 5.1 First attempt — classic extension (failed)

```bash
sudo dnf install gnome-shell-extension-desktop-icons -y
gnome-extensions enable desktop-icons@gnome-shell-extensions.gcampax.github.com
gnome-session-quit --logout --no-prompt
```

The icons still did not appear. Checking the system log:
```bash
sudo journalctl -b 0 | grep -i "desktop-icons\|extension"
```
revealed the error:
```
JS ERROR: TypeError: Extension.desktopManager is null
```

**Root cause:** an actual incompatibility bug between that classic extension (designed for GNOME 40) and the specific GNOME Shell 40.10 build shipped with Oracle Linux 9. It was not a configuration issue, but a problem in the extension's own code.

### 5.2 Second attempt — Desktop Icons NG / DING (successful)

The decision was made to manually compile and install the modern **Desktop Icons NG (DING)** extension, cloning the official repository and using the version (`tag 44`) compatible with GNOME Shell 40–44:

```bash
# Build dependencies (require temporarily enabling base repositories)
sudo dnf config-manager --set-enabled ol9_codeready_builder
sudo dnf install meson ninja-build gettext -y

# Clone the repository and check out the correct version
cd ~
git clone https://gitlab.com/rastersoft/desktop-icons-ng.git
cd desktop-icons-ng
git checkout 44

# Build and install in the user's home directory
chmod +x local_install.sh
./local_install.sh
```

> **Note:** the `/tmp` directory on Security Onion is mounted with the `noexec` option for security reasons, so the project had to be cloned and compiled in `$HOME`, not in `/tmp`.

Enable the extension (and disable the classic one, to avoid conflicts):
```bash
gnome-extensions disable desktop-icons@gnome-shell-extensions.gcampax.github.com
gnome-extensions enable ding@rastersoft.com
gnome-session-quit --logout --no-prompt
```

The icons still did not appear. Diagnosis from the log:
```bash
sudo journalctl -b 0 | grep -B 3 "ding@rastersoft.*dbusUtils.js:396"
```
Error found:
```
Error getting introspection data over Dbus: GDBus.Error:org.freedesktop.DBus.Error.ServiceUnknown: The name is not activatable
```

**Root cause #1:** DING's auxiliary process (`ding.js`, an independent GJS script) never registered itself as an activatable D-Bus service when installed manually under `~/.local/`, so the GNOME Shell extension had no way to "wake it up" automatically.

**Temporary workaround:** launch it manually from its own directory (the script's `import` statements are relative):
```bash
cd ~/.local/share/gnome-shell/extensions/ding@rastersoft.com
gjs ding.js &
```

This revealed a second error:
```
JS ERROR: TypeError: Prefs.nautilusSettings is null
```

**Root cause #2:** DING depends on **Nautilus**'s `GSettings`, which was not installed (the system only had Thunar).

**Final solution:**
```bash
sudo dnf install nautilus -y
```

After installing Nautilus and relaunching `ding.js`, the icons appeared correctly on the desktop.

### 5.3 Making DING's startup permanent

Since the process was launched manually, an autostart entry was created so it launches automatically on every graphical session:

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

**Final result:** the icons in `~/Desktop` (the "Home" and "Trash" folders, plus the user's own files) are shown permanently over the wallpaper, surviving VM reboots.

---

## Summary of key learnings

| # | Problem | Root cause | Solution |
|---|---|---|---|
| 1 | Not enough repositories to install packages | Security Onion restricts repos for security reasons | Temporarily enable `EPEL`, `baseos`, `appstream`, and `codeready_builder`, then disable them when done |
| 2 | Windows without control buttons | `xfwm4` was never running; the system used GNOME Shell | Configure buttons via `gsettings` in GNOME instead of forcing Xfce |
| 3 | No graphical file manager | Not installed by default | Install Thunar (lightweight) and, later, Nautilus (DING dependency) |
| 4 | No way to switch between open windows | No window-listing extension | Install and enable `gnome-shell-extension-window-list` |
| 5 | Desktop icons not appearing (attempt 1) | Real compatibility bug in the classic extension with GNOME 40.10 | Migrate to Desktop Icons NG (DING), built from source |
| 6 | DING installed but no icons (attempt 2) | Auxiliary D-Bus process never registered/launched; also depended on Nautilus's GSettings | Manually launch `ding.js` + install Nautilus + create an autostart entry |

**General principle applied throughout the process:** whenever a silent failure occurs in the graphical environment, the source of truth is the system log (`journalctl -b 0`), filtered by the name of the extension or process in question — the graphical interface rarely shows the real error, but the log almost always has it.

---

*Document generated as part of the Security Onion lab logbook — useful as a GNOME Shell troubleshooting reference for minimal Oracle Linux 9 / RHEL 9 installations.*
