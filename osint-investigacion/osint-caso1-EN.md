# Case 1 — OSINT Investigation of a Person Through a Social Media Username

> **Note:** the username and identifying details in this case were **anonymized** prior to publication, for ethical and privacy reasons. The documented methodology, tools, and steps are faithful to the original exercise.

## 🎯 Summary

This report documents an **OSINT (Open Source Intelligence)** exercise aimed at investigating a person starting from a single available data point: a **username** found in a log record after a possible attack was detected. No additional context was available (no IP, no email, no real name), so the entire investigation had to start from that username.

**Username investigated:** `TargetUser_Case01`

**Objective:** determine the identity, activity, and possible motivation of the user associated with that alias, using only public sources and passive reconnaissance tools.

---

## 🛠 Tools used

| Tool | Function | Link |
|---|---|---|
| OSINT Framework | Map of OSINT resources organized by category | https://osintframework.com/ |
| Sherlock | Searches a username across hundreds of platforms and social networks | https://github.com/sherlock-project/sherlock |
| cirw.in | Tool for decoding/inspecting PGP public keys | https://cirw.in/ |
| Nitter | Alternative interface for viewing Twitter/X profiles without an account | https://nitter.net |

---

## 🔧 Phase 1 — Environment setup

### 1. Exploring OSINT Framework

We visited osintframework.com to review the different categories of available resources (usernames, social media, email, domains, etc.), building a mental map of which tools to use depending on the type of data available.

### 2. Installing Sherlock

Sherlock is a command-line tool that queries hundreds of websites to check whether a given username is registered on each one.

Cloning the repository on Kali Linux:

```bash
git clone https://github.com/sherlock-project/sherlock.git
```

### 3. Installation method

Following the project's official guide, we chose to install via `apt`, compatible with Kali and ParrotOS distributions:

```bash
sudo apt install sherlock
```

### 4. Verifying the installation

```bash
sherlock --version
# Sherlock v0.16.0
```

With this, the environment was ready to begin the search.

---

## 🔎 Phase 2 — Investigating the user

### Case context

A possible security incident was identified. The only available lead was a username left in a log record:

**User:** `TargetUser_Case01`

No other additional data was available (IP, email, device, etc.), so the investigation had to start exclusively from this alias.

### Step 1 — Searching the username with Sherlock

```bash
sherlock TargetUser_Case01
```

### Step 2 — Analyzing the results

Sherlock returned 40 matches across different platforms (social networks, forums, developer services, streaming communities, marketplaces, etc.):

```
[*] Search completed with 40 results
```

Among the most relevant results: 7Cups, Archive.org, ArtStation, Envato Forum, GitHub, HackerEarth, Hashnode, LinkedIn, Reddit, Roblox, Spotify, Telegram, Threads, among others.

Of all of them, the analysis focused on identifying which platform could provide technical or real contact information, beyond simple empty profiles.

### Step 3 — Selecting the most relevant source: GitHub

The following profile was identified as having the highest investigative value:

```
https://github.com/TargetUser_Case01
```

GitHub tends to be a rich OSINT source because it exposes:
- Projects and code the person works on.
- Possible technical activity patterns.
- Public keys (PGP/SSH) linked to their digital identity.
- Commits with metadata (name, email, time zone).

### Step 4 — Analyzing the repository content

Reviewing the user's repositories revealed activity related to connecting to servers for cryptocurrency mining (Bitcoin), suggesting a possible financial motivation behind the detected incident.

### Step 5 — The "PGP" repository

Among the repositories, one named `PGP` was found — typically used to host public keys used for signing and digital encryption. The user had published their PGP public key there.

> **What is PGP?** Pretty Good Privacy is an encryption standard that allows signing and encrypting messages or files. Each public key usually carries an associated user ID (name + email address) that can reveal real contact information.

### Step 6 — Extracting the email from the public key

Using cirw.in to inspect the published PGP key, we were able to extract the email identifier associated with that key.

### Step 7 — Analyzing the email domain

The email found belonged to **ProtonMail**, an email provider focused on end-to-end encryption and privacy.

**Implication for the investigation:** the use of ProtonMail indicates the user has a privacy/OPSEC-conscious profile. This significantly reduces the viability of continuing the investigation through that channel, since:
- It does not expose metadata the way a conventional provider (Gmail, Outlook) would.
- It makes it harder to correlate the email with other accounts or data breaches.
- Any attempt at unauthorized access to that email would be both technically costly and illegal, placing it outside the scope of a passive, ethical OSINT analysis.

### Step 8 — Cross-verification on Nitter

Nitter was used to search for the original username and confirm activity on Twitter/X-type social networks:

**Username tested:** `TargetUser_Case01`

### Step 9 — Testing a username variant

A variant of the alias detected during the investigation was also tried:

**Username tested:** `TargetUser_Case01_alt`

No results or verifiable matches were obtained for this variant.

---

## ✅ Conclusions

1. The investigated user (`TargetUser_Case01`) shows activity related to searching for vulnerable machines aimed at cryptocurrency mining (Bitcoin), suggesting a financial motivation behind the detected incident.
2. An associated email address was identified through metadata from a PGP key publicly published on GitHub.
3. The use of a high-security email provider (ProtonMail) significantly limits the possibilities of further investigation through conventional OSINT channels, since this provider is specifically designed to minimize metadata exposure.
4. The investigation is considered closed in its passive phase, since any additional step (such as attempting to access the email) would exceed the ethical and legal scope of an OSINT analysis and would constitute unauthorized access.

---

## ⚠️ Ethical and legal note

This exercise was carried out using only publicly available information sources (social networks, open-source repositories, voluntarily published PGP keys) and for incident response / defensive investigation purposes. No unauthorized access to systems, accounts, or emails was performed. Any application of this methodology must comply with applicable privacy and data protection laws, and must have proper authorization when carried out in a corporate context or as part of incident response.

---


> Remember to anonymize or blur any sensitive data in screenshots before publishing them (real emails, IPs, names, etc.), even if the investigated user is fictitious or part of a lab exercise.
