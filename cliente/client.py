# ==============================================================================
# PRÁCTICA ACADÉMICA: CHAT MULTIUSUARIO EN RED LAN
# ROL: INTEGRANTE 3 - CLIENTE CONCURRENTE (THREADING & ENTORNO DE CONSOLA)
# ARCHIVO: client.py
# ==============================================================================

# PASO 1: Importar los módulos del sistema estándar necesarios.
# - socket: Manejo de la conexión TCP/IP hacia el servidor.
# - threading: Permite la concurrencia (escuchar y escribir al mismo tiempo).
# - sys y logging: Registro de eventos de diagnóstico y control de ejecución.
import socket
import threading
import sys
import logging

# PASO 2: Configurar el sistema de logs para registrar eventos y errores con marcas de tiempo.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# PASO 3: Definir la clase principal del cliente bajo el principio de Responsabilidad Única (SRP).
# Su función exclusiva es gestionar la comunicación de red del usuario con el servidor LAN.
class ConcurrentChatClient:
    def __init__(self, host: str, port: int, username: str):
        # 3.1. Almacenar los parámetros de red: IP del servidor, puerto y alias del usuario.
        self._host = host
        self._port = port
        self._username = username
        self._buffer_size = 1024  # Tamaño del búfer en bytes para recibir paquetes TCP
        
        # 3.2. Crear el socket cliente TCP (IPv4 + SOCK_STREAM).
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # 3.3. Bandera de control para detener de forma segura los hilos cuando se cierre la sesión.
        self._is_running = False

    # PASO 4: Definir el método del HILO RECEPTOR (Escucha permanente).
    # Se ejecuta en segundo plano para no congelar la consola mientras se esperan mensajes.
    def _receive_messages(self) -> None:
        while self._is_running:
            try:
                # 4.1. Operación bloqueante: esperar a que el servidor envíe datos.
                data = self._socket.recv(self._buffer_size)
                
                # Si data está vacío, significa que el servidor cerró el socket.
                if not data:
                    print("\n\r[AVISO] Conexión cerrada por el servidor.")
                    self._is_running = False
                    break

                # 4.2. Decodificar el mensaje recibido a texto legible UTF-8.
                mensaje = data.decode('utf-8')
                
                # 4.3. Mostrar el mensaje en pantalla usando '\r' para limpiar el cursor
                # y volver a pintar el prompt '> ' sin estropear lo que el usuario esté escribiendo.
                print(f"\r{mensaje}\n> ", end="", flush=True)

            except (socket.error, ConnectionResetError):
                # Captura la desconexión del servidor si ocurre abruptamente
                break

    # PASO 5: Definir el método del HILO EMISOR (Lectura del teclado).
    # Se ejecuta en el hilo principal atendiendo al usuario.
    def _send_messages(self) -> None:
        while self._is_running:
            try:
                # 5.1. Bloquear a la espera de que el usuario escriba algo y presione Enter.
                mensaje = input("> ")

                # Ignorar si el usuario solo presionó Enter sin texto.
                if not mensaje.strip():
                    continue

                # 5.2. Comando especial de salida para desconexión limpia.
                if mensaje.strip().lower() == "/exit":
                    print("[INFO] Cerrando sesión...")
                    break

                # 5.3. Convertir el texto a bytes UTF-8 y enviarlo al servidor.
                self._socket.sendall(mensaje.encode('utf-8'))

            except (KeyboardInterrupt, EOFError):
                # Capturar Ctrl+C o Ctrl+D en la terminal de Ubuntu para no arrojar trazas de error
                print("\n[INFO] Desconectando...")
                break

        # Si el usuario sale del bucle, desactivamos la bandera general
        self._is_running = False

    # PASO 6: Orquestador del ciclo de vida del cliente (Conectar, Handshake y Lanzar Concurrencia).
    def start(self) -> None:
        try:
            print(f"Conectando al servidor {self._host}:{self._port}...")
            
            # 6.1. Tocar la puerta del servidor en la IP y puerto LAN especificados.
            self._socket.connect((self._host, self._port))
            self._is_running = True

            # 6.2. PROTOCOLO INICIAL (Handshake): Enviar el alias antes de cualquier mensaje.
            # El servidor espera esto como primer dato para registrar quién es este cliente.
            self._socket.sendall(self._username.encode('utf-8'))

            # 6.3. CREAR Y ARRANCAR EL HILO SECUNDARIO (Receptor).
            # daemon=True garantiza que si el programa principal se cierra, el hilo muera automáticamente.
            hilo_receptor = threading.Thread(target=self._receive_messages, daemon=True)
            hilo_receptor.start()

            # 6.4. Mensaje visual de bienvenida para la consola.
            print("=" * 60)
            print(f"  ¡Conectado al Chat LAN como '{self._username}'!")
            print("  Escribe un mensaje y presiona Enter.")
            print("  Comando para salir: /exit (o presiona Ctrl+C)")
            print("=" * 60)

            # 6.5. El hilo principal asume el control del bucle de envío.
            self._send_messages()

        except ConnectionRefusedError:
            logging.error(f"No se pudo conectar a {self._host}:{self._port}. ¿Está el servidor encendido?")
        except Exception as e:
            logging.error(f"Error inesperado: {e}")
        finally:
            # 6.6. Limpieza final de descriptores de socket al terminar la ejecución.
            self._is_running = False
            self._socket.close()
            print("[INFO] Socket desconectado.")


# ==============================================================================
# PASO 7: PUNTO DE ENTRADA (Lógica de Interfaz y Parámetros)
# ==============================================================================
if __name__ == "__main__":
    print("=== CLIENTE DE CHAT LAN ===")
    
    # PASO 8: Definir los parámetros de red por defecto y permitir ingreso dinámico.
    DEFAULT_IP = "172.17.44.248"
    DEFAULT_PORT = 8080

    ip_input = input(f"IP del Servidor (Enter para {DEFAULT_IP}): ").strip()
    SERVER_HOST = ip_input if ip_input else DEFAULT_IP
    SERVER_PORT = DEFAULT_PORT

    # PASO 9: Solicitar y validar el alias obligatorio del usuario.
    alias = ""
    while not alias:
        alias = input("Ingresa tu Alias / Nombre de usuario: ").strip()
        if not alias:
            print("El alias no puede quedar vacío.")

    # PASO 10: Instanciar la clase y poner en marcha el cliente con concurrencia activa.
    cliente = ConcurrentChatClient(SERVER_HOST, SERVER_PORT, alias)
    cliente.start()