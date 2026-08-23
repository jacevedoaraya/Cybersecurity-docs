# Passive OSINT Reconnaissance Methodology

This repository documents, for educational and portfolio purposes, the methodology I applied in an academic project focused on information gathering and analysis using **passive OSINT** (Open Source Intelligence) techniques.

> **Note on this repository:** real data about individuals and organizations used during the original exercise was intentionally omitted or generalized. This document shows the **process, tools, and technical reasoning**, not an inventory of real targets exposed on the internet.

## Principles applied

All work was carried out under the following rules:

- **Passive** OSINT only (public information, no direct interaction with target systems).
- No aggressive scanning, brute force, phishing, or unauthorized access.
- Any sensitive finding: **documented without further probing or exposing third-party data**.

---

## 1. Image Geolocation via Visual OSINT

**Exercise goal:** determine the geographic location of a photograph based solely on its visual content and metadata, with no GPS coordinates available.

### Tools used

| Tool | Purpose |
|---|---|
| `exiftool` | EXIF metadata extraction (device, date, camera parameters) |
| [FotoForensics](https://fotoforensics.com) / [Forensically](https://29a.ch/photo-forensics) | Error Level Analysis (ELA), JPEG quantization table analysis, extraction of non-standard binary segments |
| `strings`, `binwalk` | Low-level binary analysis to detect residual metadata not removed by standard tools |
| Yandex Images / Google Lens | Reverse image search |
| Google Maps, Street View, Google Earth | Visual triangulation of the exact capture point |

### Methodology applied

1. **EXIF metadata extraction** with `exiftool`, including extended variants (`-a -u -g1`) to detect hidden or non-standard fields.
2. When EXIF was absent or incomplete, **forensic binary analysis** of non-standard file segments (e.g., proprietary vendor `APPn` segments), looking for residual readable strings.
3. **Integrity verification** via Error Level Analysis (ELA), to rule out digital manipulation of the content.
4. **Reverse image search** as the primary geolocation method when no GPS coordinates were embedded.
5. **Visual triangulation**: systematic comparison of the original image against geolocated reference photographs (user reviews, Google Earth spherical photos), looking for matches in architectural, geographic, and lighting elements.

### Key takeaways

- The absence of EXIF metadata doesn't mean the total absence of information: binary analysis of proprietary segments (vendor/chipset) can reveal hardware clues even when EXIF has been stripped.
- JPEG quantization tables allow inferring whether an image was recompressed by standard software after the original capture — a useful indicator that an image circulated through messaging apps.
- Visual triangulation-based geolocation has real limits: it isn't always possible to confirm an exact point, and it's more honest to report a confidence level than to force an unverified coordinate.

---

## 2. Passive Enumeration of an Organization

**Exercise goal:** obtain the inventory of public assets exposed on the internet by a target organization, without performing any type of active or intrusive scanning.

### Tools used

`whois` · [DNSdumpster](https://dnsdumpster.com) · [crt.sh](https://crt.sh) · [VirusTotal](https://virustotal.com) (Passive DNS / Historical SSL) · `dig` / `nslookup`

### Methodology applied

**Step 1 — Identifying network ranges and ASN**

```bash
whois <domain>
dig <domain> +short
whois <resulting_IP>       # query to LACNIC / ARIN / RIPE depending on region
```

From the domain's WHOIS record you obtain the nameservers; resolving each one and querying its IP WHOIS yields the **Autonomous System Number (ASN)** and the network range(s) (CIDR) assigned to the organization.

**Step 2 — Subdomain enumeration**

Passive subdomain reconnaissance sources are used:

- **DNSdumpster**: maps active subdomains, associated IPs, and detected web technologies (server, CMS, frameworks).
- **crt.sh**: queries the historical record of issued SSL certificates (Certificate Transparency Logs), which often reveals subdomains not listed by other sources.

**Step 3 — Infrastructure classification: owned vs. third-party providers**

Each identified subdomain/IP is classified according to who owns the corresponding ASN:

| Category | How it's identified |
|---|---|
| Owned infrastructure | The ASN belongs to the target organization |
| Cloud provider (AWS / Azure / GCP) | The ASN belongs to the cloud provider, even if the service is managed by the organization |
| Email / SaaS provider | MX, SPF, and TXT verification records (`google-site-verification`, `ms-domain-verification`, etc.) reveal which third-party providers the organization uses (email, CDN, MFA, analytics) |

**Step 4 — Virtual host (vhost) detection**

When a single IP hosts multiple subdomains, this is confirmed via:

- **Passive DNS Replication** (VirusTotal): historical record of which domains have resolved to that IP.
- **Historical SSL certificates**: the existence of individual certificates per domain, all pointing to the same IP, confirms *name-based virtual hosting* (the server decides which site to serve based on the SNI field of each request).

### Key takeaways

- A domain's TXT records (SPF, ownership verifications) are an underrated passive reconnaissance source: they reveal which SaaS providers an organization uses without touching any server.
- Combining several passive sources (DNSdumpster + crt.sh + VirusTotal) gives a much more complete picture than relying on a single tool, since each indexes data differently and with different freshness.
- Shared hosting (multiple vhosts on a single IP) is a common pattern in institutions with many low-traffic sites, and it's fully detectable passively.

---

## 3. Building Advanced Search Dorks

**Exercise goal:** build and document custom search dorks using advanced operators, to identify categories of devices and systems exposed on the internet (routers, switches, IP cameras, industrial control systems, and admin portals).

### Sources used

- **Shodan** (`http.title:`, `product:`, `country:`, `port:`)
- **Google Hacking Database (GHDB)** — a public repository of dorks cataloged and classified by exposure category

### General methodology

1. **Identify the "fingerprint"** of the product or device: the HTML title exposed by its web panel, or the product name recognized by the search tool.
2. **Build the dork** by combining the correct operator with that identified value (for example, `http.title:"<value>"`).
3. **Execute and document** the result at an aggregate level (number of results, countries, organizations, technologies), without accessing any specific panel, credential, or live feed.
4. When the source was the GHDB, the dork's record (author, publication date, category) was also documented, preserving the original cataloging.

### Example dorks documented (categories, without real target data)

```
# Admin portal (standard software, generic structure)
http.title:"phpMyAdmin"
http.title:"Log In" http.html:"wp-login"

# Router (by vendor/product)
http.title:"RouterOS"
http.title:"Cisco" http.title:"Router"

# Manageable switch
http.title:"Cisco" http.title:"Switch"
http.title:"ProCurve"

# IP camera (cataloged in GHDB)
intitle:"Toshiba Network Camera"

# SCADA / ICS system (cataloged in GHDB)
intitle:"CircarLife Scada" inurl:/html/index.html
```

### Key takeaways

- A dork's effectiveness isn't static: dorks cataloged years ago may stop returning results as systems get updated, reconfigured, or decommissioned — the absence of results is itself useful information.
- Not every result corresponds to a real device: platforms like Shodan explicitly tag certain hosts as *honeypots* (decoys), and it's necessary to identify and exclude them from the analysis.
- Some dorks cataloged in the GHDB are directly linked to documented vulnerabilities (CVEs), showing that a well-built dork isn't an arbitrary search: it targets an exposure pattern with real security relevance.

---

## Final Reflection

This project reinforced the importance of **responsible disclosure** in OSINT investigations: most of the techniques described here require zero direct interaction with the target infrastructure, and yet they still allow building a detailed picture of its public exposure surface. For that same reason, the specific findings obtained during the original exercise (organization, IPs, subdomains, and concrete devices) are kept out of this public repository.

---

*Tools: exiftool · FotoForensics · Forensically · Yandex Images · Google Earth · whois · DNSdumpster · crt.sh · VirusTotal · Shodan · Google Hacking Database*
