import socket
from protocolo import enviar_mensaje, recibir_mensaje

HOST = "127.0.0.1"
PORT = 5000

servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
servidor.bind((HOST, PORT))
servidor.listen(5)
print(f"Escuchando en {HOST}:{PORT}... (Ctrl+C para apagar)")

try:
    while True:
        conexion, direccion = servidor.accept()
        print(f"Cliente conectado desde {direccion}")

        while True:
            mensaje = recibir_mensaje(conexion)
            if mensaje is None:
                print("El cliente se desconectó")
                break
            tamano = len(mensaje.encode("utf-8"))
            print(f"Recibido ({tamano} bytes): {mensaje}")
            enviar_mensaje(conexion, mensaje)

        conexion.close()
except KeyboardInterrupt:
    print("\nApagando servidor...")
finally:
    servidor.close()
