import socket
from protocolo import enviar_mensaje, recibir_mensaje

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
        if mensaje == "largo":
            mensaje = "A" * 1500 + "FIN"
        enviar_mensaje(cliente, mensaje)
        respuesta = recibir_mensaje(cliente)
        if respuesta is None:
            print("El servidor cerró la conexión")
            break
        print(f"Eco: {respuesta}")
except ConnectionRefusedError:
    print("No se pudo conectar. ¿Está corriendo el servidor?")
except (BrokenPipeError, ConnectionResetError):
    print("Se perdió la conexión con el servidor")
except KeyboardInterrupt:
    print()
finally:
    cliente.close()
    print("Desconectado")
