"""
===============================================================================
MÓDULO DE FORMATO Y VALIDACIÓN DE MENSAJES (formatters.py)
-------------------------------------------------------------------------------
Desarrollado por: Integrante 2
Objetivo: Desacoplar la lógica de presentación visual y la validación de datos
          del motor principal de red del servidor TCP.
===============================================================================
"""

from abc import ABC, abstractmethod


# =============================================================================
# PASO 1: DEFINICIÓN DE LA INTERFAZ ABSTRACTA (Abstracción / Contrato)
# =============================================================================
# Aplicamos el Principio de Inversión de Dependencias (DIP - SOLID):
# El servidor no dependerá de una implementación concreta de texto, sino de esta
# interfaz abstracta. Esto permite que la lógica de red esté completamente limpia.
#
# También aplicamos el Principio Abierto/Cerrado (OCP - SOLID):
# El sistema queda abierto a la extensión (podemos crear nuevos estilos de formato)
# pero cerrado a la modificación (no necesitamos alterar el código del servidor).
# =============================================================================

class MessageFormatter(ABC):
    """
    Interfaz abstracta (Contrato). 
    Establece los métodos obligatorios que cualquier formateador de chat debe implementar.
    """
    
    @abstractmethod
    def format_chat(self, username: str, message: str) -> str:
        """
        Método abstracto para dar formato estético a un mensaje enviado por un usuario.
        
        Parámetros:
            username (str): El alias o nombre del usuario emisor.
            message (str): El contenido del mensaje enviado.
            
        Retorna:
            str: La cadena de texto formateada para el chat.
        """
        pass

    @abstractmethod
    def format_system(self, notification: str) -> str:
        """
        Método abstracto para dar formato a los eventos de sistema (entradas y salidas).
        
        Parámetros:
            notification (str): El texto descriptivo del evento de red.
            
        Retorna:
            str: La cadena formateada para alertas del sistema.
        """
        pass


# =============================================================================
# PASO 2: IMPLEMENTACIÓN CONCRETA DEL FORMATEADOR ESTÁNDAR
# =============================================================================
# Aplicamos el Principio de Responsabilidad Única (SRP - SOLID):
# Esta clase tiene UNA SOLA responsabilidad: maquetar estéticamente los textos
# que se mostrarán en la pantalla de la consola de cada cliente.
# =============================================================================

class StandardChatMessageFormatter(MessageFormatter):
    """
    Implementación concreta de MessageFormatter.
    Aplica el diseño visual por defecto para los mensajes de la terminal.
    """
    
    def format_chat(self, username: str, message: str) -> str:
        """
        Paso 2.1: Limpia espacios innecesarios al inicio/final del mensaje (.strip())
        y concatena el alias entre corchetes con el mensaje enviado.
        Ejemplo de salida: "[Liseth]: Hola a todos"
        """
        return f"[{username}]: {message.strip()}"

    def format_system(self, notification: str) -> str:
        """
        Paso 2.2: Limpia espacios y rodea el mensaje con asteriscos para
        destacar alertas de eventos del servidor.
        Ejemplo de salida: "*** Alex se ha unido al chat ***"
        """
        return f"*** {notification.strip()} ***"


# =============================================================================
# PASO 3: MÓDULO UTILITARIO DE VALIDACIÓN DE CONTENIDO
# =============================================================================
# Aplicamos el Principio de Responsabilidad Única (SRP - SOLID):
# Separamos la regla de validación de texto en su propia clase utilitaria para
# evitar que ni el servidor ni el formateador tengan que procesar mensajes vacíos.
# =============================================================================

class MessageValidator:
    """
    Clase utilitaria con métodos estáticos para la validación previa de datos.
    """
    
    @staticmethod
    def is_valid(message: str) -> bool:
        """
        Paso 3.1: Evalúa si la cadena recibida es válida antes de ser difundida.
        
        Retorna:
            bool: True si el mensaje contiene texto visible.
                  False si el mensaje es None, está vacío o contiene solo espacios.
        """
        return bool(message and message.strip())