# Chat con Sockets en Python

Laboratorio para entender cómo se comunican dos programas por red usando
sockets TCP. Está basado en la guía oficial
[Socket Programming HOWTO](https://docs.python.org/3/howto/sockets.html).

## Etapa 1: Servidor y cliente eco

El servidor es el "command center" de la operación: espera conexiones,
recibe los mensajes y los devuelve al cliente (eco). El cliente se conecta
al servidor, envía los mensajes que escribe el usuario y muestra la respuesta.

### Cómo ejecutarlo

Se necesitan dos terminales. En la primera, iniciar el servidor:

    cd etapa1_eco
    python3 servidor.py

En la segunda, iniciar el cliente:

    cd etapa1_eco
    python3 cliente.py

Escribir `salir` en el cliente para terminar y `Ctrl+C` para apagar el servidor.

### Lo que aprendí

- El servidor atiende un solo cliente a la vez. Si se conecta un segundo
  cliente, queda esperando en la cola de `listen()` hasta que el primero
  se desconecta. Sus mensajes no se pierden, llegan tarde, salvo que el
  servidor se apague antes de atenderlo.
- `accept()` crea un socket nuevo para cada cliente, y el cliente sale
  desde un puerto temporal distinto en cada conexión.
- El cliente no detecta en vivo que el servidor se cayó: se entera recién
  cuando intenta usar la conexión. `recv()` devuelve 0 bytes, y si sigue
  enviando aparece un `BrokenPipeError`. Por eso el código debe manejar
  esos casos.
- Los sockets transportan bytes, no texto: hay que usar `encode()` al
  enviar y `decode()` al recibir.

## Etapa 2: Protocolo con prefijo de longitud

La Etapa 1 tenía un problema escondido: el servidor y el cliente leían
como máximo 1024 bytes por `recv()` y asumían que cada mensaje llegaba
completo. Lo descubrí enviando un mensaje de 1503 bytes con el comando
especial `largo`:

- El servidor recibió el mensaje partido en dos pedazos (1024 + 479 bytes).
- El cliente mostró solo la primera parte. El resto quedó en el buffer,
  y al enviar el siguiente mensaje recibió la respuesta anterior.
- No apareció ningún error: el chat quedó desfasado en silencio.

La solución fue diseñar un protocolo propio. Cada mensaje viaja con una
cabecera de 4 bytes que indica cuánto mide:

    [ cabecera: 4 bytes con la longitud ][ mensaje ]

Quien recibe lee primero la cabecera y después exactamente esa cantidad
de bytes, aunque lleguen en varios pedazos.

### Cómo ejecutarlo

En una terminal, el servidor:

    cd etapa2_protocolo
    python3 servidor.py

En otra terminal, el cliente:

    cd etapa2_protocolo
    python3 cliente.py

`protocolo.py` no se ejecuta directamente: es un módulo que importan el
servidor y el cliente. Escribir `largo` en el cliente envía un mensaje
de 1503 bytes para probar que llega completo.

### Lo que aprendí

- TCP no tiene mensajes, solo un flujo continuo de bytes. Separar un
  mensaje del siguiente es responsabilidad del programador.
- `recv(1024)` no significa "dame un mensaje", sino "dame hasta 1024
  bytes de lo que haya".
- La función `recibir_exacto` repite `recv()` y pide solo los bytes que
  faltan, para no leer el inicio del mensaje siguiente.
- `struct.pack("!I", n)` convierte un número en 4 bytes en orden de red
  (big-endian), así ambos lados interpretan la cabecera igual.
- La longitud se mide en bytes, no en letras: en UTF-8, "canción" tiene
  7 letras pero ocupa 8 bytes.

