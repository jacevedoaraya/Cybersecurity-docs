<p align="right"><a href="README.md">Español</a> | <b>English</b></p>

<div align="justify">

# Lab: Creating a Certificate Signing Request and a Self-Signed Certificate

Hands-on lab from the **CompTIA Security+ (SY0-701)** book, digital certificates (PKI) topic. Done on Kali Linux using the OpenSSL tool.

## What is this lab about?

When you visit a page with `https://`, your browser checks that the site is who it claims to be. To do that, it uses a **digital certificate**.

A simple way to understand it is to compare it to an ID card:

- An **ID card** says who you are. A **certificate** says which website it is.
- The government issues ID cards, which is why everyone trusts them. Certificates are issued by a **Certificate Authority (CA)**, a company that browsers already trust.
- If you make your own ID card at home, it might look fine, but nobody will accept it. That is a **self-signed certificate**.

In this lab I do both things: I prepare a request like the one you would send to a CA, and then I create a certificate signed by myself to see why the system rejects it.

## Tools

| Component | Version |
|---|---|
| Operating system | <!-- output of: grep PRETTY_NAME /etc/os-release --> |
| OpenSSL | <!-- output of: openssl version --> |

## Key terms

- **Private key:** a secret only the site owner has. It is like your house key: you never hand it to anyone.
- **Public key:** can be shared with everyone. It is used to check things signed with the private key, but it does not reveal the private key.
- **CSR (Certificate Signing Request):** the "form" sent to a CA to request a certificate. It contains the site name and the public key, never the private key.
- **Self-signed certificate:** a certificate that signs itself, with no CA backing it.
- **Trusted roots:** the list of CAs that your system and browser trust from the start.

---

## Step 1: Create the keys and the request (CSR)

With a single command I create the private key and the request for the site `www.laboratorio.local`:

```bash
openssl req -new -newkey rsa:2048 -nodes -keyout servidor.key \
  -out servidor.csr \
  -subj "/C=DO/O=Laboratorio/CN=www.laboratorio.local"
```

What each part does:

| Part of the command | Meaning |
|---|---|
| `-new` | Create a new request |
| `-newkey rsa:2048` | Also create a new 2048-bit key pair |
| `-nodes` | Do not protect the private key with a password (only acceptable in a lab) |
| `-keyout servidor.key` | Save the private key to this file |
| `-out servidor.csr` | Save the request to this file |
| `-subj` | The site details: country (C), organization (O) and site name (CN) |

While it works, OpenSSL fills the screen with `.` and `+`. This is normal: it is searching for the numbers that make up the key. When `-----` appears, it finished successfully.

**Result:** two new files, `servidor.key` (the secret) and `servidor.csr` (the request).

## Step 2: Check what is inside the request

First I check who the request is for:

```bash
openssl req -in servidor.csr -noout -subject
```

```
subject=C=DO, O=Laboratorio, CN=www.laboratorio.local
```

Then I look at the full contents:

```bash
openssl req -in servidor.csr -noout -text
```

```
Certificate Request:
    Data:
        Version: 1 (0x0)
        Subject: C=DO, O=Laboratorio, CN=www.laboratorio.local
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                Public-Key: (2048 bit)
                Modulus:
                    00:eb:03:35:3d:d7:e2:db:f8:72:0b:03:08:00:b5:
                    ...
                Exponent: 65537 (0x10001)
        Attributes:
            (none)
            Requested Extensions:
    Signature Algorithm: sha256WithRSAEncryption
    Signature Value:
        e6:68:2e:f3:d7:18:87:c8:7f:5f:54:a3:80:99:6b:9f:ce:ad:
        ...
```

(I trimmed the long lines of numbers with `...`.)

**Key point:** the request only contains the **public key** (the "Public Key" section). The private key does not appear anywhere: it stays on my machine.

Finally, I check that the request is correctly signed:

```bash
openssl req -in servidor.csr -noout -verify
```

```
Certificate request self-signature verify OK
```

That signature is how I prove to the CA that I have the private key, without having to show it.

## Step 3: Create a self-signed certificate

Now, instead of asking a CA for the certificate, I sign it myself:

```bash
openssl req -x509 -newkey rsa:2048 -nodes -keyout auto.key \
  -out auto.crt -days 30 -subj "/CN=pruebas.laboratorio.local"
```

The `-x509` option tells OpenSSL to create the certificate directly, and `-days 30` makes it last 30 days.

Then I check **who** the certificate is for (subject) and **who** signed it (issuer):

```bash
openssl x509 -in auto.crt -noout -subject -issuer
```

```
subject=CN=pruebas.laboratorio.local
issuer=CN=pruebas.laboratorio.local
```

**Key point:** both names are the same. The certificate signed itself. It is like an ID card that says "this person is who they claim to be, signed: that same person".

I also check how long it is valid:

```bash
openssl x509 -in auto.crt -noout -dates
```

```
notBefore=Nov  3 00:52:39 2026 GMT
notAfter=Dec  3 00:52:39 2026 GMT
```

The dates are in universal time (GMT), which is why it shows a day ahead of my local time. After the end date, the certificate expires and is no longer valid.

## Step 4: Ask the system to trust the certificate

```bash
openssl verify auto.crt
```

```
CN=pruebas.laboratorio.local
error 18 at 0 depth lookup: self-signed certificate
error auto.crt: verification failed
```

The system rejects it with **error 18 (self-signed certificate)**. It looked for a trusted CA to back the certificate and found none. This is exactly what a browser sees when it shows the "Your connection is not private" warning.

### Extra test: telling the system to trust it

```bash
openssl verify -CAfile auto.crt auto.crt
```

```
auto.crt: OK
```

With `-CAfile` I tell OpenSSL: "trust this certificate". Now the check passes.

**Key point:** the certificate had no technical flaw. All it was missing was **someone trusted to back it**. Companies use this idea when they create their own internal CA and install it on their employees' computers.

---

## A hiccup during the lab

When pasting the terminal output into a chat app, the site name showed up with brackets and `https://`, as if it were a link. It looked like the certificate had the wrong name.

To be sure, I checked the file directly with a command that looks for brackets in the name:

```bash
openssl req -in servidor.csr -noout -subject | grep -q '\[' && echo "SUCIO" || echo "LIMPIO"
```

```
LIMPIO
```

("LIMPIO" means "clean".) The file was fine: the problem was only how the chat displayed the text. **Lesson:** verify data at its source instead of trusting how it looks on screen.

## Conclusions

A digital certificate proves that a website is who it claims to be. It does not create trust on its own: trust comes from whoever signs it. When a recognized Certificate Authority (CA) signs it, browsers accept it.

To get a certificate, you first create a **CSR** (Certificate Signing Request), which contains the site name and the public key. The **private key must never leave the machine**: if someone gets it, they could impersonate the site or decrypt communications.

A self-signed certificate is acceptable in labs, virtual machines and controlled internal environments, where we know who created it. It should not be used on public sites, because visitors have no way to verify that the site is authentic. That makes it easier for an attacker to impersonate it, and it also trains users to ignore browser warnings.

What I learned most is that **not all certificates are worth the same**, even if they are technically well made. With the `openssl verify` command I confirmed that my certificate was rejected (error 18), and that simply telling the system to trust it was enough for it to be accepted. In other words, the difference between a valid certificate and a rejected one is not in the file, but in the trust placed in whoever signed it.

## Relation to Security+ SY0-701

Domain 1.4: cryptographic solutions (PKI, public and private keys, CSR, self-signed certificates, trusted roots and certificate validity).

## Security note

Private keys (`*.key`) are **not uploaded** to this repository; they are excluded with `.gitignore`. Only the request and the certificate are published, since they are public information.

## Repository files

```
pki-autofirmado/
├── README.md      (Spanish)
├── README.en.md   (English)
├── .gitignore
├── servidor.csr   (the request)
└── auto.crt       (the self-signed certificate)
```

</div>
