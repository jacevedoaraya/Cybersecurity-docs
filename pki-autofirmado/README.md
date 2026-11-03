# Lab: Crear una solicitud de certificado y un certificado autofirmado

Laboratorio práctico del libro **CompTIA Security+ (SY0-701)**, tema de certificados digitales (PKI). Hecho en Kali Linux con la herramienta OpenSSL.

## ¿De qué trata este lab?

Cuando entras a una página con `https://`, tu navegador comprueba que el sitio es quien dice ser. Para eso usa un **certificado digital**.

Una forma sencilla de entenderlo es compararlo con una cédula de identidad:

- La **cédula** dice quién eres. El **certificado** dice qué sitio web es.
- La cédula la emite el gobierno, y por eso todos confían en ella. El certificado lo emite una **Autoridad de Certificación (CA)**, una empresa en la que los navegadores ya confían.
- Si te fabricas tu propia cédula en casa, puede verse bien, pero nadie la va a aceptar. Eso es un **certificado autofirmado**.

En este lab hago las dos cosas: preparo una solicitud como la que se enviaría a una CA, y luego creo un certificado firmado por mí mismo para ver por qué el sistema lo rechaza.

## Herramientas

| Componente | Versión |
|---|---|
| Sistema operativo | Kali GNU/Linux Rolling |
| OpenSSL | OpenSSL 3.6.3 (9 Jun 2026) |

## Palabras clave

- **Clave privada:** un secreto que solo tiene el dueño del sitio. Es como la llave de tu casa: nunca se le da a nadie.
- **Clave pública:** se puede compartir con todo el mundo. Sirve para comprobar cosas firmadas con la clave privada, pero no permite adivinarla.
- **CSR (Solicitud de firma de certificado):** el "formulario" que se envía a una CA para pedir un certificado. Lleva el nombre del sitio y la clave pública, nunca la privada.
- **Certificado autofirmado:** un certificado que se firma a sí mismo, sin que ninguna CA lo respalde.
- **Raíces de confianza:** la lista de CA en las que tu sistema y tu navegador confían desde el principio.

---

## Paso 1: Crear las claves y la solicitud (CSR)

Con un solo comando creo la clave privada y la solicitud para el sitio `www.laboratorio.local`:

```bash
openssl req -new -newkey rsa:2048 -nodes -keyout servidor.key \
  -out servidor.csr \
  -subj "/C=DO/O=Laboratorio/CN=www.laboratorio.local"
```

Qué hace cada parte:

| Parte del comando | Qué significa |
|---|---|
| `-new` | Crear una solicitud nueva |
| `-newkey rsa:2048` | Crear también un par de claves nuevo, de 2048 bits |
| `-nodes` | No proteger la clave privada con contraseña (solo aceptable en un lab) |
| `-keyout servidor.key` | Guardar la clave privada en este archivo |
| `-out servidor.csr` | Guardar la solicitud en este archivo |
| `-subj` | Los datos del sitio: país (C), organización (O) y nombre del sitio (CN) |

Mientras trabaja, OpenSSL llena la pantalla de `.` y `+`. Es normal: está buscando los números que forman la clave. Cuando aparece `-----`, terminó bien.

**Resultado:** dos archivos nuevos, `servidor.key` (el secreto) y `servidor.csr` (la solicitud).

## Paso 2: Revisar qué hay dentro de la solicitud

Primero veo a nombre de quién está la solicitud:

```bash
openssl req -in servidor.csr -noout -subject
```

```
subject=C=DO, O=Laboratorio, CN=www.laboratorio.local
```

Luego veo el contenido completo:

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

(Recorté las líneas largas de números con `...`.)

**Lo importante:** dentro de la solicitud solo está la **clave pública** (la sección "Public Key"). La clave privada no aparece por ningún lado: se queda guardada en mi equipo.

Por último, compruebo que la solicitud está bien firmada:

```bash
openssl req -in servidor.csr -noout -verify
```

```
Certificate request self-signature verify OK
```

Esa firma es la forma de demostrarle a la CA que tengo la clave privada, sin tener que enseñársela.

## Paso 3: Crear un certificado autofirmado

Ahora, en lugar de pedirle el certificado a una CA, me lo firmo yo mismo:

```bash
openssl req -x509 -newkey rsa:2048 -nodes -keyout auto.key \
  -out auto.crt -days 30 -subj "/CN=pruebas.laboratorio.local"
```

La parte `-x509` le dice a OpenSSL que cree el certificado directamente, y `-days 30` que dure 30 días.

Luego miro **para quién** es el certificado (subject) y **quién** lo firmó (issuer):

```bash
openssl x509 -in auto.crt -noout -subject -issuer
```

```
subject=CN=pruebas.laboratorio.local
issuer=CN=pruebas.laboratorio.local
```

**Lo importante:** los dos nombres son iguales. El certificado se firmó a sí mismo. Es como una cédula que dice "esta persona es quien dice ser, firmado: esa misma persona".

También veo cuánto tiempo es válido:

```bash
openssl x509 -in auto.crt -noout -dates
```

```
notBefore=Nov  3 00:52:39 2026 GMT
notAfter=Dec  3 00:52:39 2026 GMT
```

Las fechas están en hora universal (GMT), por eso aparece un día después de mi hora local. Pasada la fecha final, el certificado vence y deja de valer.

## Paso 4: Pedirle al sistema que confíe en el certificado

```bash
openssl verify auto.crt
```

```
CN=pruebas.laboratorio.local
error 18 at 0 depth lookup: self-signed certificate
error auto.crt: verification failed
```

El sistema lo rechaza con el **error 18 (certificado autofirmado)**. Buscó una CA de confianza que respaldara el certificado y no encontró ninguna. Esto es exactamente lo que ve un navegador cuando muestra la advertencia de "Tu conexión no es privada".

### Prueba extra: decirle al sistema que sí confíe

```bash
openssl verify -CAfile auto.crt auto.crt
```

```
auto.crt: OK
```

Con `-CAfile` le digo a OpenSSL: "confía en este certificado". Ahora la comprobación pasa.

**Lo importante:** el certificado no tenía ningún defecto técnico. Lo único que le faltaba era **alguien de confianza que lo respaldara**. Las empresas usan esta idea cuando crean su propia CA interna y la instalan en los computadores de sus empleados.

---

## Un tropiezo durante el lab

Al pegar los resultados de la terminal en una aplicación de chat, el nombre del sitio aparecía con corchetes y `https://`, como si fuera un enlace. Parecía que el certificado tenía un nombre equivocado.

Para salir de dudas, revisé el archivo directamente con un comando que busca corchetes en el nombre:

```bash
openssl req -in servidor.csr -noout -subject | grep -q '\[' && echo "SUCIO" || echo "LIMPIO"
```

```
LIMPIO
```

El archivo estaba bien: el problema era solo cómo el chat mostraba el texto. **Lección:** comprobar los datos en su origen, en vez de fiarse de cómo se ven en pantalla.

## Conclusiones

Un certificado digital sirve para demostrar que un sitio web es quien dice ser. No genera confianza por sí solo: la confianza viene de quién lo firma. Cuando una Autoridad de Certificación (CA) reconocida lo firma, los navegadores lo aceptan.

Para obtener un certificado se crea primero una **CSR** (solicitud de firma de certificado), que lleva el nombre del sitio y la clave pública. La **clave privada nunca debe salir del equipo**: si alguien la obtiene, podría hacerse pasar por el sitio o descifrar comunicaciones.

Un certificado autofirmado es aceptable en laboratorios, máquinas virtuales y entornos internos controlados, donde sabemos quién lo creó. En sitios públicos no se debe usar, porque los visitantes no tienen forma de comprobar que el sitio es auténtico. Eso facilita que un atacante se haga pasar por él, y además acostumbra a los usuarios a ignorar las advertencias del navegador.

Lo que más aprendí es que **no todos los certificados valen lo mismo**, aunque técnicamente estén bien hechos. Con el comando `openssl verify` comprobé que mi certificado era rechazado (error 18) y que bastaba con indicarle al sistema que confiara en él para que fuera aceptado. Es decir, la diferencia entre un certificado válido y uno rechazado no está en el archivo, sino en la confianza en quien lo firma.

## Relación con Security+ SY0-701

Dominio 1.4: soluciones criptográficas (PKI, claves pública y privada, CSR, certificados autofirmados, raíces de confianza y vigencia de certificados).

## Nota de seguridad

Las claves privadas (`*.key`) **no se suben** a este repositorio; están excluidas con `.gitignore`. Solo se publican la solicitud y el certificado, que son información pública.

## Archivos del repositorio

```
pki-autofirmado/
├── README.md      (español)
├── README.en.md   (inglés)
├── .gitignore
├── servidor.csr   (la solicitud)
└── auto.crt       (el certificado autofirmado)
```

