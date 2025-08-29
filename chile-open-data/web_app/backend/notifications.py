"""
Sistema de notificaciones en tiempo real con WebSockets
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class Notification:
    """Estructura de una notificación"""
    id: str
    type: str  # 'info', 'warning', 'error', 'success'
    title: str
    message: str
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None
    read: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la notificación a diccionario para JSON"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

class NotificationManager:
    """Gestor centralizado de notificaciones"""
    
    def __init__(self):
        self._notifications: List[Notification] = []
        self._subscribers: List[callable] = []
        self._max_notifications = 100  # Límite de notificaciones en memoria
        
        # Configurar limpieza automática cada 1 hora
        import threading
        import time
        
        def cleanup_worker():
            while True:
                time.sleep(3600)  # 1 hora
                self._cleanup_old_notifications()
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        
    def _cleanup_old_notifications(self):
        """Limpia notificaciones antiguas (más de 7 días)"""
        cutoff_time = datetime.now() - timedelta(days=7)
        before_count = len(self._notifications)
        self._notifications = [
            notif for notif in self._notifications 
            if notif.timestamp > cutoff_time
        ]
        cleaned = before_count - len(self._notifications)
        if cleaned > 0:
            logger.info(f"Limpiadas {cleaned} notificaciones antiguas")
        
    def add_subscriber(self, callback: callable):
        """Añade un callback que se ejecutará cuando haya nuevas notificaciones"""
        self._subscribers.append(callback)
        
    def remove_subscriber(self, callback: callable):
        """Remueve un callback de la lista de suscriptores"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def create_notification(self, 
                          notification_type: str,
                          title: str, 
                          message: str,
                          data: Optional[Dict[str, Any]] = None) -> Notification:
        """Crea una nueva notificación"""
        notification = Notification(
            id=f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            type=notification_type,
            title=title,
            message=message,
            timestamp=datetime.now(),
            data=data or {}
        )
        
        # Añadir a la lista
        self._notifications.append(notification)
        
        # Mantener solo las últimas notificaciones
        if len(self._notifications) > self._max_notifications:
            self._notifications = self._notifications[-self._max_notifications:]
        
        # Notificar a todos los suscriptores
        self._notify_subscribers(notification)
        
        logger.info(f"Notificación creada: {notification.type} - {notification.title}")
        return notification
    
    def _notify_subscribers(self, notification: Notification):
        """Notifica a todos los suscriptores sobre la nueva notificación"""
        for callback in self._subscribers:
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"Error notificando suscriptor: {e}")
    
    def get_notifications(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene las últimas notificaciones"""
        recent_notifications = self._notifications[-limit:] if limit else self._notifications
        return [notif.to_dict() for notif in reversed(recent_notifications)]
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Marca una notificación como leída"""
        for notification in self._notifications:
            if notification.id == notification_id:
                notification.read = True
                return True
        return False
    
    def get_unread_count(self) -> int:
        """Obtiene el número de notificaciones no leídas"""
        return sum(1 for notif in self._notifications if not notif.read)
    
    def clear_notifications(self):
        """Limpia todas las notificaciones"""
        self._notifications.clear()
        logger.info("Todas las notificaciones han sido eliminadas")

# Instancia global del gestor de notificaciones
notification_manager = NotificationManager()

def create_dataset_change_notification(dataset_name: str, change_type: str, details: Dict[str, Any]):
    """Crea una notificación específica para cambios en datasets"""
    type_mapping = {
        'updated': 'info',
        'error': 'error',
        'new': 'success',
        'removed': 'warning'
    }
    
    title_mapping = {
        'updated': f'Dataset {dataset_name} actualizado',
        'error': f'Error en dataset {dataset_name}',
        'new': f'Nuevo dataset disponible: {dataset_name}',
        'removed': f'Dataset {dataset_name} no disponible'
    }
    
    message_mapping = {
        'updated': f'Se detectaron cambios en el dataset {dataset_name}',
        'error': f'Error al verificar el dataset {dataset_name}: {details.get("error", "Error desconocido")}',
        'new': f'Se ha añadido un nuevo dataset: {dataset_name}',
        'removed': f'El dataset {dataset_name} ya no está disponible'
    }
    
    notification_type = type_mapping.get(change_type, 'info')
    title = title_mapping.get(change_type, f'Cambio en dataset {dataset_name}')
    message = message_mapping.get(change_type, f'Cambio detectado en {dataset_name}')
    
    return notification_manager.create_notification(
        notification_type=notification_type,
        title=title,
        message=message,
        data={
            'dataset_name': dataset_name,
            'change_type': change_type,
            'details': details
        }
    )

def create_system_notification(title: str, message: str, notification_type: str = 'info', data: Optional[Dict[str, Any]] = None):
    """Crea una notificación del sistema"""
    return notification_manager.create_notification(
        notification_type=notification_type,
        title=title,
        message=message,
        data=data or {}
    )
