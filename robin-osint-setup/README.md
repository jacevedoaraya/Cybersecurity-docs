# Robin on an OSINT VM: installation guide with Gemini, Ollama and a desktop launcher

🌐 **English** | [Español](README.es.md)

This guide documents the installation and configuration of [Robin](https://github.com/apurvsinghgautam/robin), a dark web OSINT tool that uses large language models (LLMs) to refine queries, filter results from `.onion` search engines and generate investigation summaries.

It covers three stages, in the order they were carried out:

1. **Robin with Gemini** (Google's cloud API).
2. **Robin with Ollama** (local model, no data sent to AI providers).
3. **Desktop launcher** to start Robin with a double click.

Each stage includes its pros and cons, followed by an overall comparison at the end.

> ⚠️ **Legal notice.** Robin is intended for educational and lawful investigative purposes only. Accessing certain dark web content may be illegal depending on your jurisdiction. Use it at your own risk and comply with all laws and policies that apply to you.

---

## Table of contents

- [Environment](#environment)
- [Part 0: system preparation](#part-0-system-preparation)
- [Part 1: Robin with Gemini](#part-1-robin-with-gemini)
- [Part 2: Robin with Ollama (local model)](#part-2-robin-with-ollama-local-model)
- [Part 3: desktop launcher](#part-3-desktop-launcher)
- [Overall comparison](#overall-comparison)
- [Switching between Gemini and Ollama](#switching-between-gemini-and-ollama)
- [Troubleshooting](#troubleshooting)
- [Security recommendations](#security-recommendations)
- [Credits](#credits)

---

## Environment

| Component | Detail |
|---|---|
| Virtualization | VirtualBox, network in **NAT** mode |
| Operating system | Debian GNU/Linux 13 (trixie), XFCE desktop |
| Resources (with Gemini) | 4 GB RAM, 2 cores |
| Resources (with Ollama) | 12 GB RAM, 3 cores (host machine: 20 GB, 4 cores) |
| Disk | 60 GB |
| Robin | Official image `apurvsg/robin:latest` |
| Interface port | `8501` (Streamlit) |

---

## Part 0: system preparation

### 0.1 VM snapshot

Before you start, take a snapshot in VirtualBox via **Machine → Take Snapshot...**. If something goes wrong, you can roll back to a clean state.

### 0.2 Update the system

```bash
cat /etc/os-release              # confirm the distribution
sudo apt update && sudo apt upgrade -y
```

### 0.3 Install Docker and Tor

```bash
sudo apt install -y docker.io tor
sudo systemctl enable --now docker tor
```

Check Tor. On Debian, `tor.service` is a "master" unit that shows as `active (exited)`; the one doing the actual work is `tor@default`:

```bash
systemctl status tor@default     # should say: active (running)
sudo ss -tlnp | grep 9050        # should show 127.0.0.1:9050
```

> **Note:** testing showed that the Robin container **ships with its own Tor** (on startup it prints `Starting Tor... Tor is ready.`). The system Tor service is not strictly required for Robin, but it causes no conflicts.
>
> **Tor Browser does not replace the Tor service.** The browser bundles its own Tor, but it only runs while the browser is open and only for that browser (port 9150).

### 0.4 Pull the official image

```bash
sudo docker pull apurvsg/robin:latest
```

> Only use the image and repository from the original author (`apurvsinghgautam/robin`). There are many forks; a modified copy could contain malicious code.

### 0.5 Working directory

```bash
mkdir -p ~/robin/investigations && cd ~/robin
id -u                            # should return 1000
```

The container runs as UID 1000. Creating the `investigations` folder before the first run prevents Docker from creating it as `root`, which would stop Robin from saving investigations.

---

## Part 1: Robin with Gemini

### 1.1 Get the API key

1. Go to <https://aistudio.google.com/app/apikey> with your Google account. It's best to do this from the browser **inside the VM**, so you can copy and paste the key directly.
2. Use the existing key or click **Create API key**.
3. Copy the key (it starts with `AIza...`).

### 1.2 Create the `.env` file

```bash
cd ~/robin
nano .env
```

Content, on a single line with no spaces:

```
GOOGLE_API_KEY=AIzaYourKeyHere
```

In the terminal, paste with **Ctrl+Shift+V**. To save: **Ctrl+O**, **Enter**, **Ctrl+X**.

Protect the file and check it without revealing the key:

```bash
chmod 600 .env
cut -d= -f1 .env                 # should show only: GOOGLE_API_KEY
```

> Robin also accepts `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY` and `OPENROUTER_API_KEY`. One is enough.

### 1.3 Run Robin

```bash
cd ~/robin
sudo docker run --rm \
   -v "$(pwd)/.env:/app/.env" \
   -v "$(pwd)/investigations:/app/investigations" \
   -e STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
   --add-host=host.docker.internal:host-gateway \
   -p 127.0.0.1:8501:8501 \
   apurvsg/robin:latest
```

What each option does:

| Option | Purpose |
|---|---|
| `-v .../.env:/app/.env` | Passes the API key to the container |
| `-v .../investigations:...` | Keeps investigations across restarts |
| `-e STREAMLIT_BROWSER_GATHER_USAGE_STATS=false` | Disables Streamlit telemetry |
| `--add-host=host.docker.internal:host-gateway` | Lets the container reach services on the VM (needed for Ollama) |
| `-p 127.0.0.1:8501:8501` | Exposes the interface **only** inside the VM, not on the network |

Expected output:

```
Tor is ready.
Refreshing model list from providers...
  google       24 models
Starting Robin: AI-Powered Dark Web OSINT Tool...
```

> The `External URL` line printed by Streamlit is informational only. Since the port is bound to `127.0.0.1`, the interface is not reachable from outside the VM.

### 1.4 Using the interface

Open **Firefox** (not Tor Browser) at `http://localhost:8501`. The interface runs on the VM itself, and Robin already performs its searches over Tor internally. Tor Browser usually cannot open `localhost`.

To manually open an `.onion` link from the results, copy it and open it in **Tor Browser**, never in Firefox.

### 1.5 Gemini pros and cons

| ✅ Pros | ❌ Cons |
|---|---|
| Fast: investigations finish quickly | Queries and scraped content are sent to Google for analysis |
| Very good summarization and filtering quality | API calls **do not go through Tor**: Google sees your real public IP |
| Low resource usage: works with 4 GB RAM and 2 cores | On the free tier, Google may use the content to improve its products (check the current terms) |
| Simple setup: a single line in `.env` | Depends on a Google account and an internet connection |
| Free tier available | Rate limits on the free plan |
| Access to many models (24 detected) | The API key is a secret that must be protected; if leaked, someone could use it on your behalf |

---

## Part 2: Robin with Ollama (local model)

With Ollama, the AI model runs inside the VM. The only traffic leaving to the internet is searching and scraping, which go through Tor.

### 2.1 Increase VM resources

An 8B-parameter model needs a fair amount of RAM. Check current resources:

```bash
free -h
nproc
df -h ~
```

If needed, shut down the VM (`sudo poweroff`) and in VirtualBox go to **Settings → System**:

- **Motherboard → Base Memory:** 12288 MB.
- **Processor:** 3.

Always leave enough memory for the host machine (in this case, 8 GB and 1 core).

Rough model guide based on VM RAM:

| VM RAM | Suggested model | Comment |
|---|---|---|
| < 8 GB | `llama3.2:1b` / `llama3.2:3b` | Works, but with limited results |
| 8–16 GB | `llama3.1:8b` | Good balance (used in this guide) |
| > 16 GB | Larger models | Better quality, slower without a GPU |

### 2.2 Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

On a VM you'll see `No NVIDIA/AMD GPU detected. Ollama will run in CPU-only mode.` This is expected.

### 2.3 Let the container reach Ollama

By default Ollama only listens on `127.0.0.1:11434`, which the container cannot reach.

```bash
sudo systemctl edit ollama.service
```

In the space between `### Anything between here...` and `### Edits below this comment will be discarded`, write:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
```

Save, restart and verify:

```bash
sudo systemctl daemon-reload && sudo systemctl restart ollama
sudo ss -tlnp | grep 11434       # should show *:11434
```

> With VirtualBox networking in NAT mode, the local network cannot reach the VM, so Ollama is not exposed. If you use **Bridged Adapter** mode, protect port 11434 with a firewall.

### 2.4 Pull and test the model

```bash
ollama pull llama3.1:8b          # ~4.9 GB
ollama run llama3.1:8b "Hello, answer in one sentence"
```

### 2.5 Disable the Gemini key

To make sure nothing is sent to Google, comment out the line in `.env`:

```bash
nano ~/robin/.env
```

```
#GOOGLE_API_KEY=AIza...
```

Ollama **does not need** any variable in `.env`: Robin defaults to `http://host.docker.internal:11434`.

### 2.6 Run Robin

Use the same command as in section 1.3. The `google 24 models` line will no longer appear on startup.

In the interface, the model shows up in the sidebar as **`[ollama] llama3.1:8b`** ("Locally detected Ollama models are automatically added to this list").

### 2.7 Ollama pros and cons

| ✅ Pros | ❌ Cons |
|---|---|
| **Fully private analysis:** neither queries nor scraped content go to an AI provider | Needs a lot of RAM: 8 GB practical minimum, 12 GB or more recommended |
| No API keys, accounts or secrets to protect | **Slow** without a GPU: each investigation can take several minutes |
| No per-use cost or request limits | Lower filtering and summarization quality than large cloud models |
| Analysis works without relying on external services | Takes ~5 GB of disk per model |
| Full control over the model and its version | More complex setup (systemd, `OLLAMA_HOST`) |
| | Listening on `0.0.0.0` requires care with the VM's network settings |
| | The VM becomes sluggish while the model is working |

---

## Part 3: desktop launcher

To avoid typing the long command every time, create a script and a desktop icon.

### 3.1 Startup script

The script starts Robin and automatically opens Firefox once the interface is ready.

```bash
cat > ~/robin/iniciar.sh << 'EOF'
#!/bin/bash
cd ~/robin
( until curl -s http://localhost:8501 >/dev/null; do sleep 2; done
  firefox http://localhost:8501 ) &
sudo docker run --rm \
   -v "$(pwd)/.env:/app/.env" \
   -v "$(pwd)/investigations:/app/investigations" \
   -e STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
   --add-host=host.docker.internal:host-gateway \
   -p 127.0.0.1:8501:8501 \
   apurvsg/robin:latest
EOF
chmod +x ~/robin/iniciar.sh
```

From the terminal, just run `~/robin/iniciar.sh`.

### 3.2 Desktop icon (XFCE)

```bash
cat > "$(xdg-user-dir DESKTOP)/Robin.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=Robin
Comment=AI-Powered Dark Web OSINT Tool
Exec=xfce4-terminal --title=Robin -e "bash -c '~/robin/iniciar.sh; read -p \"Robin stopped. Press Enter to close...\"'"
Icon=utilities-terminal
Terminal=false
EOF
chmod +x "$(xdg-user-dir DESKTOP)/Robin.desktop"
```

### 3.3 Usage

1. Double-click the **Robin** icon.
2. The first time, an "Untrusted application launcher" dialog appears. Choose **Mark As Secure And Launch**.
3. Enter your `sudo` password in the terminal window.
4. Firefox opens the interface automatically.

To stop Robin: in the "Robin" window, press **Ctrl+C** and then **Enter**.

### 3.4 Launcher pros and cons

| ✅ Pros | ❌ Cons |
|---|---|
| Start with a double click | Still asks for the `sudo` password on every start |
| Opens the browser automatically | Depends on XFCE (`xfce4-terminal`); other desktops need a different command |
| Avoids typos in the long command | Paths (`~/robin`) and browser (`firefox`) are hard-coded in the script |
| Always uses the same security options | The terminal window must stay open while Robin runs |
| Easy to edit in a single file | The launcher must be marked as trusted the first time |

> **About avoiding `sudo`:** adding your user to the `docker` group would remove the password prompt, but that group is effectively equivalent to `root` access. This guide keeps `sudo` on purpose.

---

## Overall comparison

| Criterion | Gemini | Ollama (`llama3.1:8b`) |
|---|---|---|
| Analysis privacy | Low: content goes to Google | High: everything stays in the VM |
| IP exposure to the AI provider | Yes (the API does not use Tor) | Not applicable |
| Speed | High | Low (CPU only) |
| Result quality | High | Medium |
| RAM needed in the VM | ~4 GB | ~12 GB recommended |
| Extra disk | Minimal | ~5 GB per model |
| Cost | Free with limits / pay per use | Free |
| Setup difficulty | Low | Medium |
| Requires external account | Yes | No |

**Which one to choose?**

- **Gemini:** for testing, learning or low-resource machines, when queries are not sensitive.
- **Ollama:** for investigations where confidentiality matters more than speed.
- **Desktop launcher:** recommended in both cases, for convenience.

---

## Switching between Gemini and Ollama

Just edit `~/robin/.env` and restart Robin:

| To use | Line in `.env` |
|---|---|
| Gemini | `GOOGLE_API_KEY=AIza...` (no `#`) |
| Ollama only | `#GOOGLE_API_KEY=AIza...` (commented out) |

If the key is active and Ollama is also running, both will appear in the model selector in the interface.

---

## Troubleshooting

| Problem | Likely cause | Solution |
|---|---|---|
| `tor.service` shows `active (exited)` | Normal behavior on Debian | Check `systemctl status tor@default` |
| `No such file or directory` when running `iniciar.sh` | The script was not created | Repeat section 3.1 |
| nano asks "Save modified buffer?" on exit | File was not saved with Ctrl+O | Press `Y`, then `Enter` |
| Ollama models don't appear | Ollama only listens on `127.0.0.1` | Review section 2.3 and `ss -tlnp \| grep 11434` |
| Investigations are not saved | Folder is owned by `root` or UID is not 1000 | Create the folder before the first run; check `id -u` |
| Launcher does nothing | Desktop does not use `xfce4-terminal` | Change the terminal command in `Robin.desktop` |

Connection test between the container and Ollama (with Robin running, from another terminal):

```bash
sudo docker exec $(sudo docker ps -q --filter ancestor=apurvsg/robin:latest) \
  python -c "import urllib.request;print(urllib.request.urlopen('http://host.docker.internal:11434/api/tags').read()[:300])"
```

---

## Security recommendations

- Take a VM **snapshot** before major changes.
- Keep VirtualBox networking in **NAT** mode.
- Bind the interface only to `127.0.0.1` (`-p 127.0.0.1:8501:8501`).
- Protect `.env` with `chmod 600` and **never** push it to GitHub. Add `.env` to your `.gitignore`.
- Open `.onion` links only in Tor Browser and do not download files from those sites.
- Update the image regularly with `sudo docker pull apurvsg/robin:latest`.
- To delete local investigations: `rm -f ~/robin/investigations/*`.

Example `.gitignore` for this repository:

```
.env
investigations/
```

---

## Credits

- **Robin** was created by [Apurv Singh Gautam](https://github.com/apurvsinghgautam) and is distributed under the MIT license: <https://github.com/apurvsinghgautam/robin>
- **Ollama:** <https://ollama.com>
- **Tor Project:** <https://www.torproject.org>

This guide documents a personal installation in a lab environment and is not affiliated with Robin's author.
