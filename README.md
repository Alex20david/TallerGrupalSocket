# Sistema de Chat Multiusuario en Red LAN por Consola

Sistema de mensajería distribuido en tiempo real sobre red local (LAN) desarrollado en **Python 3**. La aplicación evoluciona un modelo de eco básico hacia un entorno de chat concurrente multiusuario, utilizando sockets TCP y programación orientada a objetos bajo principios de diseño **SOLID**.

---

## Organización del Equipo y Roles

El proyecto fue coordinado, organizado y liderado por **Alex Chacha (Participante 2)**, quien distribuyó el trabajo técnico de manera modular entre los tres integrantes del grupo:

* **Alex Chacha — Participante 2 (Líder del Proyecto & Desarrollador de Dominio/Formato):**
  * **Liderazgo y Organización:** Diseñó la arquitectura general del sistema, coordinó la integración de los componentes, definió la división de responsabilidades y estructuró el flujo de trabajo en equipo.
  * **Desarrollo (`formatters.py`):** Implementó la abstracción `MessageFormatter` (DIP/OCP), el formateador `StandardChatMessageFormatter` (`[Usuario]: mensaje` y `*** Notificaciones ***`) y la clase `MessageValidator` para el filtrado de mensajes (SRP).

* **Esteban Melo — Participante 1 (Desarrollador del Servidor de Red & Concurrencia):**
  * **Desarrollo (`server.py`):** Implementó el servidor TCP multihilo `ThreadedSocketServer` escuchando en `0.0.0.0:8080`, el gestor de sockets individuales `ClientHandler`, la difusión de mensajes (`broadcast`) y el control de concurrencia segura (*Thread-Safety*) mediante `threading.Lock`.

* **Christian Carrión — Participante 3 (Desarrollador del Cliente Concurrente & Interfaz):**
  * **Desarrollo (`client.py`):** Implementó el cliente multihilo `ConcurrentChatClient`, la recepción de mensajes en segundo plano (`_receive_messages`), la lectura continua de la consola (`_send_messages`), el manejo de comandos de salida (`/exit`) y la experiencia de usuario en terminal.

---

## Arquitectura y Principios SOLID

El código fuente se encuentra dividido de forma modular para garantizar el desacoplamiento entre la infraestructura de red, la lógica de presentación y la interfaz del cliente:

### 1. Principios SOLID Aplicados

* **Single Responsibility Principle (SRP - Responsabilidad Única):**
  * `ThreadedSocketServer` (`server.py`): Encargado exclusivamente de administrar la apertura del socket servidor TCP, escuchar peticiones entrantes y gestionar la lista global de conexiones.
  * `ClientHandler` (`server.py`): Encargado únicamente de gestionar el ciclo de vida de un socket individual y delegar sus datos al sistema de difusión.
  * `StandardChatMessageFormatter` (`formatters.py`): Responsable único del formato visual y la maquetación estética del texto (`[Usuario]: mensaje` y `*** Notificaciones ***`).
  * `MessageValidator` (`formatters.py`): Clase utilitaria cuya única responsabilidad es validar que las entradas no contengan cadenas vacías o espacios en blanco.

* **Open/Closed Principle (OCP - Abierto/Cerrado) & Dependency Inversion Principle (DIP - Inversión de Dependencias):**
  * Se define la abstracción `MessageFormatter` (`formatters.py`) como un contrato de interfaz. El servidor depende directamente de esta abstracción y no de implementaciones concretas. Esto permite cambiar el formato visual (por ejemplo, agregar timestamps `[HH:MM]`) extendiendo la clase abstracta sin necesidad de alterar una sola línea de código del servidor de red.

---

## Concurrencia y Thread-Safety

### Servidor Multihilo (`server.py`)
* Cada cliente que establece conexión genera la instanciación de un hilo dedicado (`threading.Thread` con `daemon=True`) corriendo la función `ClientHandler.process()`. Esto evita que la lectura bloqueante de un cliente detenga las comunicaciones de los demás.
* **Manejo de Exclusiones Mutuas (`threading.Lock`):** El acceso a la lista dinámica de clientes activos (`_clients`) está protegido por un cerrojo de exclusión mutua (`self._lock`) dentro de los métodos `broadcast()` y `remove_client()`, garantizando seguridad en entornos multihilo (*Thread-Safety*) durante operaciones concurrentes de entrada y salida.

### Cliente Concurrente (`client.py`)
* **Hilo Secundario (`_receive_messages`):** Mantiene una escucha continua e ininterrumpida de los paquetes entrantes del socket (`recv`). Redibuja la terminal en tiempo real utilizando retornos de carro (`\r`) y vaciado de buffer (`flush=True`).
* **Hilo Principal (`_send_messages`):** Mantiene la consola desbloqueada para la lectura continua del teclado (`input()`), permitiendo al usuario redactar mensajes sin ser interrumpido por las entradas del chat.

---

## Instrucciones de Ejecución Paso a Paso

### Prerrequisitos
* Tener **Python 3.8+** instalado en todas las máquinas.
* Asegurar que todos los equipos estén conectados a la misma red LAN (Wi-Fi o cable Ethernet).

### Paso 1: Iniciar el Servidor (PC Servidor — Esteban Melo)
1. Abrir una terminal en el equipo que actuará como servidor.
2. Obtener la dirección IP del equipo en la red local (en Ubuntu/Linux ejecutar `hostname -I`).
3. Iniciar el servidor (escuchará en `0.0.0.0:8080` para aceptar todas las interfaces):
   ```bash
   python3 server.py
   ```

### Paso 2: Conectar los Clientes (PCs Clientes — Alex Chacha / Christian Carrión)
1. En cada computadora cliente, ejecutar el cliente de chat:
   ```bash
   python3 client.py
   ```
2. La consola solicitará los siguientes datos:
   * **IP del Servidor LAN:** Introducir la IP obtenida en la máquina servidor (ejemplo: `172.17.44.248`).
   * **Alias / Nombre de usuario:** Ingresar el nombre visible dentro del chat.
3. Para finalizar la sesión de forma limpia, ingresar el comando `/exit` o presionar `Ctrl + C`.

---

## Tolerancia a Fallos y Excepciones

El sistema está diseñado para prevenir caídas imprevistas (*crashes*):
* Intercepta excepciones de red de tipo `ConnectionResetError` y `socket.error` producidas por desconexiones abruptas de clientes (cierre repentino de la terminal o pérdida de señal Wi-Fi).
* Mediante el bloque `finally`, el servidor remueve automáticamente el socket inactivo de la lista global, libera recursos y notifica a la sala el evento de desconexión.


