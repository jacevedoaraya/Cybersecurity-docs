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


## Etapa 3: Chat con varios clientes simultáneos

En la Etapa 2, el servidor atendía a un solo cliente a la vez. Si se
conectaba un segundo cliente, quedaba esperando en la cola de `listen()`
hasta que el primero se desconectaba.

Lo resolví con hilos. Cada vez que un cliente se conecta, el servidor
crea un hilo dedicado a conversar con él, como un restaurante que
contrata un mesero nuevo para cada mesa. El programa principal se queda
en la puerta haciendo `accept()` para recibir al siguiente cliente.

La función `difundir` recorre la lista de clientes conectados y le
reenvía a todos cada mensaje que llega, junto con los avisos de quién
entra y quién sale. Por eso ahora todos ven lo que escribe cada uno.

Al conectar el cliente de la Etapa 2 al servidor nuevo, el cliente
quedó desfasado: mostraba la respuesta anterior en vez de la actual.
Además, mientras esperaba en `input()`, no podía mostrar los mensajes
de los demás. Por eso el cliente también necesitó un hilo: uno atiende
el teclado y otro solo escucha lo que llega del servidor.

### Cómo ejecutarlo

En una terminal, el servidor:

    cd etapa3_chat
    python3 servidor.py

En otras terminales, varios clientes al mismo tiempo:

    cd etapa3_chat
    python3 cliente.py

### Lo que aprendí

- Un hilo permite que un programa haga varias cosas a la vez. El
  servidor usa un hilo por cliente, y el cliente usa uno para escribir
  y otro para escuchar.
- Una condición de carrera ocurre cuando varios hilos modifican el
  mismo dato al mismo tiempo, como la lista de clientes. El `Lock`
  (candado) la evita: solo el hilo que lo tiene puede tocar la lista,
  y los demás esperan su turno.
- El cliente viejo quedó desfasado porque leía una respuesta por cada
  mensaje enviado, pero el servidor nuevo enviaba más mensajes de los
  que recibía (avisos de entrada y mensajes de otros clientes).
- `daemon=True` hace que los hilos se cierren junto con el programa
  principal. Sin esto, el programa quedaría colgado al salir.
