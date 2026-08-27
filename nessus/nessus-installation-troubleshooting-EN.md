# Nessus Installation & Troubleshooting Log

**Author:** Juan Pablo Acevedo Araya
**Context:** Cybersecurity coursework — installing Tenable Nessus (Essentials) on Windows
**Date:** August 2026

> This document records the real issues encountered while installing Nessus, root causes, and the fixes applied — useful as a personal reference and as a portfolio piece demonstrating troubleshooting skills.

---

## 1. Objective

Install Tenable Nessus on a Windows laptop for a cybersecurity class, ending up with a working **Nessus Essentials** license (free, no expiration, up to 16 hosts) tied to a personal user account.

## 2. Environment

- **OS:** Windows 10/11
- **Product attempted:** Nessus Professional (trial) → later switched to Nessus Essentials
- **Storage tried:** External HDD (drive G:) → External HDD (drive D:) → **Internal disk (C:)** (final, working setup)

## 3. Timeline of Issues & Fixes

### Issue 1 — Registered with a personal Gmail instead of a work email
**Problem:** The Nessus Professional trial signup form rejected a personal Gmail address, requiring a "work email."
**Fix:** Registered instead with a work/institutional email address. Confirmed this is legal — no law prohibits using a work email for a personal course signup — though it's worth checking internal company policy on acceptable use.

### Issue 2 — "Error: You are not authorized to perform this request" during account creation
**Problem:** While creating the local Nessus admin user through the web setup wizard, the process failed with this authorization error.
**Root cause:** Likely a session/timing desync in the setup wizard, sometimes tied to leftover state from a previous failed step.
**Fix attempted:** Refreshing the page, clearing cache, restarting the Nessus Windows service (`services.msc` → Tenable Nessus → Restart).

### Issue 3 — Login failed with "invalid credentials" after setup finished
**Problem:** After the plugin compilation finished and the login screen appeared, the created user account could not log in.
**Root cause:** The account was likely never fully created in the backend due to Issue 2 — the wizard *appeared* to move forward, but the user record was incomplete.
**Fix:** Used the command-line tool `nessuscli` to manage users directly, bypassing the web wizard:
```bash
# On Windows, cd alone won't switch drives — use /d
cd /d "G:\Programas"

# Create a new admin user
nessuscli adduser

# List existing users (to check what's actually saved)
nessuscli lsuser

# Remove a user if needed
nessuscli rmuser <username>

# Reset a password for an existing user
nessuscli chpasswd <username>
```
Must be run from an **elevated (Administrator) terminal**, from the folder where Nessus was installed (contains `nessuscli.exe`).

### Issue 4 — Username `jacevedoaraya` kept failing, even after reinstalling
**Problem:** That specific username consistently produced `An error occurred` when creating it via `nessuscli adduser`, even though `nessuscli lsuser` showed no users existed.
**Root cause:** Likely leftover/orphaned state tied to that exact username from the earlier failed web-based attempt (Issue 2), not visible through `lsuser` but still blocking re-creation.
**Fix:** Simply used a different username (e.g. `jpacevedo`) — worked immediately (`User added`).

### Issue 5 — "Only a Nessus Manager license allows you to create more than one user"
**Problem:** Tried to create a second user without deleting the first one.
**Root cause:** Essentials/Professional-trial licenses only allow **one local user at a time**.
**Fix:** Delete the existing user first (`nessuscli rmuser <username>`), confirm deletion with `nessuscli lsuser`, then create the new one.

### Issue 6 — Scanner showed "Unregistered Scanner" / Activation Code: N/A
**Problem:** Login succeeded, but the About page showed the scanner as unregistered — meaning the trial activation never completed, likely tied back to Issue 2's failed request.
**Fix:** Retrieved the real activation code from the Tenable account portal (`My Trials` / `My Products` section — **not** from the confirmation email, which did not show it), then entered it manually under **Settings → About → Overview → Activation Code (pencil icon)**.

### Issue 7 — Nessus Professional trial only had ~5 days left
**Problem:** The Professional trial license was short-lived and impractical for ongoing coursework.
**Decision:** Switched to **Nessus Essentials** instead — free, no expiration, sufficient host limit (16) for classroom/home-lab use.

### Issue 8 — Session dropped mid-way through changing the activation code
**Problem:** While replacing the Professional code with the Essentials code, the session logged out before saving, and the old Professional code remained active (even extended by a day).
**Fix attempt:** Retried the code swap without refreshing mid-process — inconsistent results, leading to Issue 9.

### Issue 9 — Persistent inconsistencies led to a clean reinstall
**Problem:** Switching licenses in-place kept producing edge cases (leftover config, wrong license persisting).
**Decision:** Fully uninstalled Nessus and **deleted leftover data folders** (`nessus`, `conf`) from the previous install locations, since the uninstaller doesn't always remove them — this residual data was also the cause of an unexpected **"Nessus is locked — enter encryption password"** screen on a supposedly clean reinstall (an old encrypted database was still present).

### Issue 10 — Installing on external drives (G:, then D:) caused repeated instability
**Problem:** Multiple authorization/state errors were more frequent when Nessus was installed on external USB drives.
**Root cause (suspected):** Slower I/O and/or filesystem permission handling differences on external/removable drives versus an internal disk.
**Fix:** Reinstalled on the **internal C: drive** — no further authorization errors occurred, and plugin compilation was noticeably faster.

### Issue 11 — "Activation failed" using the Essentials code from days earlier
**Problem:** The originally issued Essentials activation code failed validation during the clean C: install.
**Root cause:** The code had **expired** (Essentials activation codes are single-use / time-limited once issued and not immediately redeemed).
**Fix:** Requested a **new** Essentials activation code via the registration form (`Get an activation code` → skip if reusing → or fill the form again for a fresh one) and entered it immediately. This time it validated successfully and plugin download/compilation proceeded.

## 4. Final Working Setup

- Nessus installed on **internal disk (C:)**
- License: **Nessus Essentials** (free, no expiration, up to 16 hosts)
- Local admin user created successfully through the standard web wizard (no `nessuscli` workaround needed on the clean C: install)

## 5. Key Lessons Learned

1. **Install on the internal disk, not an external/USB drive.** External drives introduced repeated authorization and locking errors, likely due to I/O speed and/or permission handling.
2. **`cd` alone doesn't switch drives in Windows `cmd`.** Use `cd /d "X:\path"` to change drive and folder together.
3. **`nessuscli` is a reliable fallback** when the web setup wizard fails to create a user (`adduser`, `lsuser`, `rmuser`, `chpasswd`).
4. **A username that failed once may stay "stuck"** even if it doesn't appear in `lsuser` — just use a different username rather than debugging indefinitely.
5. **Essentials/Professional-trial licenses allow only one local user** — delete the old one before creating a new one.
6. **The activation code is not always in the welcome email** — check the Tenable account portal (`My Trials`) for the authoritative, live code.
7. **Activation codes can expire before being used** — if "Activation failed" appears with good internet, request a fresh code rather than retrying the same one repeatedly.
8. **When licensing state gets inconsistent, a clean reinstall (with manual deletion of leftover `nessus`/`conf` folders) is often faster than continuing to debug in place.**
9. **Nessus Essentials is the right fit for coursework/home labs:** free, no expiration, and the 16-host limit is rarely a real constraint for learning purposes — versus a Professional trial that expires in days.

---

## 📎 Quick Reference — `nessuscli` Commands

| Command | Purpose |
|---|---|
| `cd /d "X:\path"` | Change drive + folder in Windows cmd |
| `nessuscli adduser` | Create a new user |
| `nessuscli lsuser` | List existing users |
| `nessuscli rmuser <user>` | Delete a user |
| `nessuscli chpasswd <user>` | Reset a user's password |
