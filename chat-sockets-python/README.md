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

## Próximas etapas

- Etapa 2: protocolo con prefijo de longitud
- Etapa 3: chat con varios clientes simultáneos
