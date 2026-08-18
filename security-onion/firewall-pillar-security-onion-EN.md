# Security Onion: Fixing Agent Enrollment Failures via Firewall and Pillar Configuration

**Diagnostic and remediation log — SecOps lab environment**

| Field | Value |
|---|---|
| Environment | Security Onion (Eval mode), based on CentOS/Rocky |
| Minion ID | `juanpablo_eval` |
| Objective | Resolve the firewall misconfiguration blocking agent enrollment |
| Tools used | Salt (`salt-call`), nftables/iptables-nft, vi, bash |

---

## 1. Problem summary

New agents could not be enrolled into the Security Onion manager. The investigation traced the problem to the internal Docker-facing firewall (nftables, managed through the `DOCKER-USER` chain), which was not allowing traffic from the analyst network to the ports required for enrollment and monitoring (Elasticsearch's REST API and the management web interface served by Nginx).

The fix required defining a new Salt pillar for the affected host, which in turn revealed two pre-existing gaps in the node's base pillar configuration (missing sensor interface and main host interface definitions) that were silently blocking the firewall state from being applied at all.

---

## 2. Root cause analysis

### 2.1 Missing / incorrectly named firewall pillar

Security Onion's firewall rules are generated per-minion from Salt pillar files located at `/opt/so/saltstack/local/pillar/minions/`. The pillar file must be named exactly after the Salt minion ID (confirmed with `salt-call grains.get id`), not an arbitrary name.

The file was initially created as `nohacker_eval.sls`, but the actual minion ID was `juanpablo_eval` — so Salt never loaded the intended configuration.

### 2.2 Undefined pillar dependencies (sensor.interface, host.mainint)

After fixing the filename, applying the firewall state failed with a Jinja rendering error in `globals.map.jinja`, a shared template used by most Security Onion states. Two required values were completely missing from the node's pillar tree:

- **`sensor.interface`** — the network interface used for traffic capture (`bond0`, MTU 9000, no IP — the sniffing interface).
- **`host.mainint`** — the management interface (`ens160`, the one holding the host's administration IP).

These values were absent from every pillar file on the system (confirmed via a recursive grep), including an empty (0-byte) `adv_juanpablo_eval.sls` file that appeared to be a leftover from an incomplete initial installation.

Since these values are consumed by a global template shared by nearly all Security Onion states, their absence was blocking not just the firewall state, but potentially the application of other states on this node as well.

---

## 3. Remediation steps

### Step 1 — Confirm the actual minion ID

```bash
sudo salt-call grains.get id
```

**Result:** returned `juanpablo_eval`, confirming the mismatch with the pillar filename.

### Step 2 — Create the pillar file with the correct name and the firewall rule

```bash
sudo tee /opt/so/saltstack/local/pillar/minions/juanpablo_eval.sls > /dev/null << 'EOF'
firewall:
  hostgroups:
    analyst:
      - 192.168.116.0/24
  role:
    eval:
      chain:
        DOCKER-USER:
          hostgroups:
            analyst:
              portgroups:
                - elasticsearch_rest
                - nginx
EOF
```

**Result:** written directly via a heredoc (`bash tee`) instead of an interactive editor, to avoid corruption from a stuck `vi` session and stray swap files.

### Step 3 — Refresh and validate the pillar

```bash
sudo salt-call saltutil.refresh_pillar
sudo salt-call pillar.get firewall
```

**Result:** confirmed that Salt was now correctly merging the new `analyst` hostgroup with the existing pillar data.

### Step 4 — First state.apply attempt (partial failure)

```bash
sudo salt-call state.apply firewall
```

**Result:** failed with: `Jinja variable ... has no attribute 'sensor'` — identified as a missing `sensor.interface` pillar key.

### Step 5 — Add the missing sensor interface

```bash
sudo tee -a /opt/so/saltstack/local/pillar/minions/juanpablo_eval.sls > /dev/null << 'EOF'
sensor:
  interface: bond0
EOF
```

**Result:** interface identified via `ip a` as the dedicated capture interface (no IP, MTU 9000).

### Step 6 — Second state.apply attempt (partial failure)

```bash
sudo salt-call state.apply firewall
```

**Result:** failed with a new error: `has no attribute 'host'` — traced to `globals.map.jinja`, which requires `host.mainint`.

### Step 7 — Add the missing management interface

```bash
sudo tee -a /opt/so/saltstack/local/pillar/minions/juanpablo_eval.sls > /dev/null << 'EOF'
host:
  mainint: ens160
EOF
```

**Result:** interface identified via `ip a` as the one holding the management IP (192.168.140.150).

### Step 8 — Final state.apply (success)

```bash
sudo salt-call state.apply firewall
```

**Result:** `Succeeded: 8 (changed=4), Failed: 0`. The iptables/nftables ruleset was updated and reloaded via `iptables-restore`.

### Step 9 — Verify the live firewall ruleset

```bash
sudo nft list ruleset | grep "192.168.116"
```

**Result:** confirmed three new ACCEPT rules for `192.168.116.0/24` on ports 9200 (Elasticsearch), 80, and 443 (Nginx).

---

## 4. Verification

The final nftables ruleset was inspected directly (not just the Salt state output) to confirm the change actually took effect at the packet-filtering layer:

```
ip saddr 192.168.116.0/24 tcp dport 9200 counter packets 0 bytes 0 accept
ip saddr 192.168.116.0/24 tcp dport 80 counter packets 0 bytes 0 accept
ip saddr 192.168.116.0/24 tcp dport 443 counter packets 0 bytes 0 accept
```

With these rules active, hosts on the analyst subnet (`192.168.116.0/24`) can now reach Elasticsearch's REST API and the management interface served by Nginx, both required for agent enrollment.

---

## 5. Key takeaways

- Salt pillar filenames for per-minion configuration must exactly match the minion ID (`salt-call grains.get id`), not an informally assigned name.
- A single missing pillar key in a shared Jinja template (`globals.map.jinja`) can silently block unrelated states across the entire node — always trace Jinja rendering errors back to the specific pillar key referenced in the traceback.
- When an interactive editor session becomes unreliable (stuck macros, orphaned swap files), writing configuration via a non-interactive heredoc (`cat`/`tee << EOF`) is a safer, more reproducible alternative to hand-editing in `vi`.
- Always validate a fix at two layers: the orchestration layer (`salt-call pillar.get` / `state.apply` summary) and the actually applied state (`nft list ruleset`) — a successful Salt run does not by itself prove that real-time behavior has changed.

---

*Prepared as part of a hands-on cybersecurity course lab on deploying and troubleshooting a SOC with Security Onion.*
