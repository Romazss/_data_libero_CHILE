"""
WebSocket handler para comunicación en tiempo real
"""
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
import logging
from typing import Dict, Any
from notifications import notification_manager, Notification

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Gestor de conexiones WebSocket"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.connected_clients: Dict[str, Dict[str, Any]] = {}
        
        # Suscribirse al gestor de notificaciones
        notification_manager.add_subscriber(self.broadcast_notification)
        
        # Registrar eventos
        self._register_events()
    
    def _register_events(self):
        """Registra todos los eventos de WebSocket"""
        
        @self.socketio.on('connect')
        def handle_connect():
            client_id = request.sid
            self.connected_clients[client_id] = {
                'connected_at': None,
                'rooms': ['general'],
                'user_agent': request.headers.get('User-Agent', 'Unknown')
            }
            
            # Unir a la sala general
            join_room('general', sid=client_id)
            
            logger.info(f"Cliente conectado: {client_id}")
            
            # Enviar notificaciones recientes al cliente recién conectado
            recent_notifications = notification_manager.get_notifications(limit=10)
            emit('recent_notifications', {
                'notifications': recent_notifications,
                'unread_count': notification_manager.get_unread_count()
            })
            
            # Enviar estadísticas iniciales
            self._send_initial_stats(client_id)
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            client_id = request.sid
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
            logger.info(f"Cliente desconectado: {client_id}")
        
        @self.socketio.on('join_room')
        def handle_join_room(data):
            room = data.get('room')
            if room:
                join_room(room)
                if request.sid in self.connected_clients:
                    self.connected_clients[request.sid]['rooms'].append(room)
                logger.info(f"Cliente {request.sid} se unió a la sala: {room}")
        
        @self.socketio.on('leave_room')
        def handle_leave_room(data):
            room = data.get('room')
            if room:
                leave_room(room)
                if request.sid in self.connected_clients:
                    rooms = self.connected_clients[request.sid]['rooms']
                    if room in rooms:
                        rooms.remove(room)
                logger.info(f"Cliente {request.sid} salió de la sala: {room}")
        
        @self.socketio.on('mark_notification_read')
        def handle_mark_notification_read(data):
            notification_id = data.get('notification_id')
            if notification_id:
                success = notification_manager.mark_as_read(notification_id)
                emit('notification_marked_read', {
                    'notification_id': notification_id,
                    'success': success,
                    'unread_count': notification_manager.get_unread_count()
                })
        
        @self.socketio.on('get_notifications')
        def handle_get_notifications(data):
            limit = data.get('limit', 50)
            notifications = notification_manager.get_notifications(limit)
            emit('notifications_list', {
                'notifications': notifications,
                'unread_count': notification_manager.get_unread_count()
            })
        
        @self.socketio.on('clear_notifications')
        def handle_clear_notifications():
            notification_manager.clear_notifications()
            self.socketio.emit('notifications_cleared', room='general')
        
        @self.socketio.on('ping')
        def handle_ping():
            emit('pong', {'timestamp': str(datetime.now())})
    
    def _send_initial_stats(self, client_id: str):
        """Envía estadísticas iniciales al cliente"""
        try:
            # Aquí podrías obtener estadísticas reales del sistema
            initial_stats = {
                'connected_clients': len(self.connected_clients),
                'system_status': 'healthy',
                'last_update': str(datetime.now())
            }
            self.socketio.emit('initial_stats', initial_stats, room=client_id)
        except Exception as e:
            logger.error(f"Error enviando estadísticas iniciales: {e}")
    
    def broadcast_notification(self, notification: Notification):
        """Envía una notificación a todos los clientes conectados"""
        try:
            self.socketio.emit('new_notification', {
                'notification': notification.to_dict(),
                'unread_count': notification_manager.get_unread_count()
            }, room='general')
            logger.info(f"Notificación enviada via WebSocket: {notification.title}")
        except Exception as e:
            logger.error(f"Error enviando notificación via WebSocket: {e}")
    
    def broadcast_dataset_update(self, dataset_info: Dict[str, Any]):
        """Envía actualizaciones de datasets a todos los clientes"""
        try:
            self.socketio.emit('dataset_update', dataset_info, room='general')
            logger.info(f"Actualización de dataset enviada: {dataset_info.get('name', 'Unknown')}")
        except Exception as e:
            logger.error(f"Error enviando actualización de dataset: {e}")
    
    def broadcast_stats_update(self, stats: Dict[str, Any]):
        """Envía actualizaciones de estadísticas a todos los clientes"""
        try:
            self.socketio.emit('stats_update', stats, room='general')
        except Exception as e:
            logger.error(f"Error enviando actualización de estadísticas: {e}")
    
    def get_connected_clients_count(self) -> int:
        """Obtiene el número de clientes conectados"""
        return len(self.connected_clients)
    
    def get_client_info(self) -> Dict[str, Any]:
        """Obtiene información de todos los clientes conectados"""
        return {
            'total_clients': len(self.connected_clients),
            'clients': self.connected_clients
        }

# Import datetime aquí para evitar problemas de importación circular
from datetime import datetime
