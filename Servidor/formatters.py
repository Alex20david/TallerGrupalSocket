from abc import ABC, abstractmethod

# --- PRINCIPIO DE INVERSIÃ“N DE DEPENDENCIAS (DIP) ---
class MessageFormatter(ABC):
    """Interfaz abstracta: define el contrato para el formato de mensajes."""
    
    @abstractmethod
    def format_chat(self, username: str, message: str) -> str:
        """Formatea un mensaje enviado por un usuario."""
        pass

    @abstractmethod
    def format_system(self, notification: str) -> str:
        """Formatea notificaciones de entrada/salida del sistema."""
        pass


# --- PRINCIPIO DE RESPONSABILIDAD ÃšNICA (SRP) ---
class StandardChatMessageFormatter(MessageFormatter):
    """Clase encargada ÃšNICAMENTE del formato visual del texto."""
    
    def format_chat(self, username: str, message: str) -> str:
        return f"[{username}]: {message.strip()}"

    def format_system(self, notification: str) -> str:
        return f"*** {notification.strip()} ***"


class MessageValidator:
    """Clase utilitaria para validar que no entren mensajes vacÃ­os."""
    
    @staticmethod
    def is_valid(message: str) -> bool:
        return bool(message and message.strip())