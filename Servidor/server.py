# ==============================================================================
# MÓDULO DEL SERVIDOR TCP MULTIHILO Y DIFUSIÓN (BROADCAST)
# Integrante 1: Responsable de Red, Concurrencia y Sockets
# ==============================================================================

import socket
import threading
import logging
from abc import ABC, abstractmethod

# Importamos las abstracciones y reglas de negocio diseñadas por el Integrante 2
from formatters import StandardChatMessageFormatter, MessageValidator, MessageFormatter

# Configuración del sistema de logs para imprimir la actividad en consola con la fecha/hora
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


# ==============================================================================
# GESTOR DE CONEXIÓN INDIVIDUAL POR CLIENTE (Principio SRP: Single Responsibility)
# ==============================================================================
class ClientHandler:
    """
    Clase dedicada EXCLUSIVAMENTE a gestionar el flujo de datos con UN solo cliente.
    Se ejecuta de forma independiente dentro de su propio hilo (Thread).
    """
    def __init__(self, client_socket: socket.socket, address: tuple, server: 'ThreadedSocketServer'):
        self._client_socket = client_socket  # Socket exclusivo asignado para esta conexión
        self._address = address              # Tupla con (IP, Puerto) del cliente
        self._server = server                # Referencia al servidor principal para poder hacer broadcast
        self._username = f"{address[0]}:{address[1]}"  # Identificador temporal usando IP:Puerto
        self._buffer_size = 1024             # Tamaño máximo del paquete de lectura en bytes

    def process(self) -> None:
        """
        Ciclo principal del hilo: Lee el nombre de usuario, escucha mensajes continuos
        y gestiona las desconexiones limpiamente.
        """
        try:
            # ------------------------------------------------------------------
            # PASO 1: HANDSHAKE / IDENTIFICACIÓN DEL USUARIO
            # El primer paquete enviado por el cliente contiene su Alias/Username
            # ------------------------------------------------------------------
            raw_username = self._client_socket.recv(self._buffer_size).decode('utf-8').strip()
            if MessageValidator.is_valid(raw_username):
                self._username = raw_username

            # Notificación del sistema a la red de que un usuario ingresó
            join_msg = self._server.formatter.format_system(f"{self._username} se ha unido al chat")
            logging.info(f"Conexión establecida con {self._address} como '{self._username}'")
            self._server.broadcast(join_msg, sender_socket=None)

            # ------------------------------------------------------------------
            # PASO 2: BUCLE INFINITO DE LECTURA DE MENSAJES DE CHAT
            # ------------------------------------------------------------------
            while True:
                # Método bloqueante: espera a que el cliente envíe datos
                data = self._client_socket.recv(self._buffer_size)
                
                # Si 'data' viene vacío (0 bytes), significa que el cliente cerró el socket
                if not data:
                    break
                
                message = data.decode('utf-8')
                
                # Se delega la validación de texto al módulo del Integrante 2
                if MessageValidator.is_valid(message):
                    # Se aplica el formato [Hora] [Usuario]: Mensaje
                    formatted_msg = self._server.formatter.format_chat(self._username, message)
                    
                    # Se difunde el mensaje a todos los demás clientes en la LAN
                    self._server.broadcast(formatted_msg, sender_socket=self._client_socket)

        except (ConnectionResetError, socket.error):
            # Captura desconexiones repentinas (Ctrl+C en la consola del cliente o pérdida de señal Wi-Fi)
            logging.warning(f"Conexión interrumpida abruptamente por {self._address}")
        finally:
            # ------------------------------------------------------------------
            # PASO 3: LIMPIEZA OBLIGATORIA DEL SOCKET
            # Se ejecuta siempre al salir del ciclo, asegurando que no queden 'sockets fantasma'
            # ------------------------------------------------------------------
            self._server.remove_client(self._client_socket)
            leave_msg = self._server.formatter.format_system(f"{self._username} ha salido del chat")
            logging.info(f"Conexión finalizada con {self._address}")
            self._server.broadcast(leave_msg, sender_socket=None)
            self._client_socket.close()


# ==============================================================================
# SERVIDOR PRINCIPAL Y INFRAESTRUCTURA DE RED (Principio SRP y DIP)
# ==============================================================================
class ThreadedSocketServer:
    """
    Servidor TCP de difusión. Abre el puerto, escucha nuevas conexiones
    y mantiene el registro thread-safe de todos los clientes activos.
    """
    def __init__(self, host: str, port: int, formatter: MessageFormatter):
        self._host = host
        self._port = port
        self.formatter = formatter   # Inyección de dependencias (DIP): Recibe el formateador
        self._clients = []            # Lista dinámica para registrar los sockets conectados
        self._lock = threading.Lock() # Candado (Lock) para evitar condiciones de carrera entre hilos
        
        # Creación del Socket TCP IPv4
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Opción para reutilizar el puerto al reiniciar la app (evita 'Address already in use')
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def broadcast(self, message: str, sender_socket: socket.socket = None) -> None:
        """
        Método de Difusión: Recorre la lista de clientes y les envía el mensaje.
        Usa self._lock para garantizar Thread-Safety durante la iteración.
        """
        with self._lock:
            for client in self._clients:
                # Opcional: No reenviar el mensaje al propio usuario que lo escribió
                if client != sender_socket:
                    try:
                        client.sendall(message.encode('utf-8'))
                    except socket.error:
                        # Si el envío falla, la limpieza se delega al hilo propio del cliente en ClientHandler
                        pass

    def remove_client(self, client_socket: socket.socket) -> None:
        """Remueve un socket de la lista activa de forma segura con exclusión mutua."""
        with self._lock:
            if client_socket in self._clients:
                self._clients.remove(client_socket)

    def start(self) -> None:
        """Inicia la escucha en la interfaz de red y el bucle para aceptar clientes."""
        # Enlaza el socket a la dirección y puerto especificados
        self._server_socket.bind((self._host, self._port))
        self._server_socket.listen()
        logging.info(f"Servidor de Chat iniciado y escuchando en {self._host}:{self._port}")

        try:
            while True:
                # Queda a la espera de un cliente (operación bloqueante)
                client_socket, address = self._server_socket.accept()
                
                # Agrega el nuevo cliente a la lista protegida por Lock
                with self._lock:
                    self._clients.append(client_socket)
                
                # Instancia el manejador y dispara un hilo independiente para atenderlo
                handler = ClientHandler(client_socket, address, self)
                thread = threading.Thread(target=handler.process, daemon=True)
                thread.start()

        except KeyboardInterrupt:
            # Cierre limpio del servidor con Ctrl+C desde la terminal de Ubuntu
            logging.info("Servidor detenido manualmente por el usuario.")
        finally:
            # Cierra el socket principal al finalizar
            self._server_socket.close()


# ==============================================================================
# PUNTO DE ENTRADA DEL PROGRAMA
# ==============================================================================
if __name__ == "__main__":
    # '0.0.0.0' indica que el servidor escuchará en todas las tarjetas de red de la PC (Wi-Fi y Ethernet LAN)
    HOST = '0.0.0.0'
    PORT = 8080
    
    # Se crea e inyecta la instancia del formateador del Integrante 2
    formatter = StandardChatMessageFormatter()
    
    # Se arranca el servidor
    server = ThreadedSocketServer(HOST, PORT, formatter)
    server.start()