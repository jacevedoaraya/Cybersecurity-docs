import socket

HOST = "127.0.0.1"
PORT = 5000

cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    cliente.connect((HOST, PORT))
    print(f"Conectado a {HOST}:{PORT}. Escribe 'salir' para terminar.")

    while True:
        mensaje = input("Tú> ")
        if mensaje == "salir":
            break
        if not mensaje:
            continue
        cliente.sendall(mensaje.encode("utf-8"))
        respuesta = cliente.recv(1024)
        if not respuesta:
            print("El servidor cerró la conexión")
            break
        print(f"Eco: {respuesta.decode('utf-8')}")
except ConnectionRefusedError:
    print("No se pudo conectar. ¿Está corriendo el servidor?")
except (BrokenPipeError, ConnectionResetError):
    print("Se perdió la conexión con el servidor")
except KeyboardInterrupt:
    print()
finally:
    cliente.close()
    print("Desconectado")
