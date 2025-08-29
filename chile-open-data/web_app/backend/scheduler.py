# /web_app/backend/scheduler.py
"""
Scheduler para monitoreo automático de datasets
"""

import threading
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict
import signal
import sys

from services.sources import load_sources
from services.checker import check_all
from models import Database, DatasetStatus
from cache import invalidate_datasets_cache


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatasetMonitor:
    """Monitor automático de datasets"""
    
    def __init__(self, db: Database, check_interval: int = 300):  # 5 minutos por defecto
        self.db = db
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        self._stop_event = threading.Event()
        
        # Registrar manejador de señales para cierre limpio
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Manejador de señales para cierre limpio"""
        logger.info(f"Recibida señal {signum}, iniciando cierre limpio...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """Inicia el monitoreo en un hilo separado"""
        if self.running:
            logger.warning("El monitor ya está ejecutándose")
            return
        
        logger.info(f"Iniciando monitor de datasets (intervalo: {self.check_interval}s)")
        self.running = True
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Detiene el monitoreo"""
        if not self.running:
            return
        
        logger.info("Deteniendo monitor de datasets...")
        self.running = False
        self._stop_event.set()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        logger.info("Monitor detenido")
    
    def _monitor_loop(self):
        """Loop principal de monitoreo"""
        logger.info("Monitor iniciado")
        
        while self.running and not self._stop_event.is_set():
            try:
                self._check_datasets()
                
                # Limpiar datos antiguos periódicamente (cada hora)
                if int(time.time()) % 3600 == 0:
                    self._cleanup_old_data()
                
            except Exception as e:
                logger.error(f"Error en check de datasets: {e}")
            
            # Esperar el intervalo o hasta que se solicite parada
            self._stop_event.wait(self.check_interval)
        
        logger.info("Loop de monitoreo terminado")
    
    def _check_datasets(self):
        """Verifica todos los datasets y guarda resultados"""
        try:
            # Cargar datasets desde sources.yaml
            datasets = load_sources()
            logger.info(f"Verificando {len(datasets)} datasets...")
            
            # Registrar datasets en la BD si no existen
            self.db.register_datasets(datasets)
            
            # Obtener estados anteriores para detectar cambios
            previous_states = {}
            for dataset in datasets:
                prev_status = self.db.get_latest_dataset_status(dataset['id'])
                if prev_status:
                    previous_states[dataset['id']] = prev_status.status
            
            # Verificar estado de cada dataset
            results = check_all(datasets)
            check_time = datetime.now(timezone.utc)
            
            # Guardar resultados y detectar cambios
            changes_detected = []
            for result in results:
                status = DatasetStatus(
                    id=result['id'],
                    name=result['name'],
                    category=result['category'],
                    url=result['url'],
                    status=result['status'],
                    http_code=result.get('http_code'),
                    latency_ms=result.get('latency_ms'),
                    error=result.get('error'),
                    checked_at=check_time
                )
                self.db.save_dataset_status(status)
                
                # Detectar cambios de estado
                prev_status = previous_states.get(result['id'])
                if prev_status and prev_status != result['status']:
                    changes_detected.append({
                        'dataset_id': result['id'],
                        'dataset_name': result['name'],
                        'previous_status': prev_status,
                        'new_status': result['status'],
                        'error': result.get('error')
                    })
            
            # Enviar notificaciones de cambios
            self._send_change_notifications(changes_detected)
            
            # Invalidar cache para forzar actualización
            invalidate_datasets_cache()
            
            # Log de resumen
            available = len([r for r in results if r['status'] == 'up'])
            logger.info(f"Check completado: {available}/{len(results)} datasets disponibles")
            
            if changes_detected:
                logger.info(f"Detectados {len(changes_detected)} cambios de estado")
            
        except Exception as e:
            logger.error(f"Error verificando datasets: {e}")
    
    def _send_change_notifications(self, changes: List[Dict]):
        """Envía notificaciones por cambios detectados"""
        try:
            # Importar aquí para evitar importación circular
            from notifications import create_dataset_change_notification
            
            for change in changes:
                change_type = 'updated' if change['new_status'] == 'up' else 'error'
                
                create_dataset_change_notification(
                    dataset_name=change['dataset_name'],
                    change_type=change_type,
                    details={
                        'previous_status': change['previous_status'],
                        'new_status': change['new_status'],
                        'error': change.get('error'),
                        'dataset_id': change['dataset_id']
                    }
                )
        except Exception as e:
            logger.error(f"Error enviando notificaciones de cambios: {e}")
    
    def _cleanup_old_data(self):
        """Limpia datos antiguos de la base de datos"""
        try:
            logger.info("Limpiando datos antiguos...")
            self.db.cleanup_old_data(days=7)  # Mantener solo 7 días
            logger.info("Limpieza completada")
        except Exception as e:
            logger.error(f"Error en limpieza: {e}")
    
    def force_check(self):
        """Fuerza una verificación inmediata"""
        logger.info("Forzando verificación inmediata...")
        self._check_datasets()


class BackgroundScheduler:
    """Scheduler en background para tareas periódicas"""
    
    def __init__(self, db: Database):
        self.db = db
        self.monitor = DatasetMonitor(db)
        self.running = False
    
    def start(self):
        """Inicia todas las tareas en background"""
        if self.running:
            return
        
        logger.info("Iniciando scheduler en background...")
        self.running = True
        
        # Iniciar monitor de datasets
        self.monitor.start()
        
        # Hacer una verificación inicial
        self.monitor.force_check()
        
        logger.info("Scheduler iniciado correctamente")
    
    def stop(self):
        """Detiene todas las tareas"""
        if not self.running:
            return
        
        logger.info("Deteniendo scheduler...")
        self.running = False
        
        # Detener monitor
        self.monitor.stop()
        
        logger.info("Scheduler detenido")
    
    def get_status(self) -> Dict:
        """Obtiene el estado del scheduler"""
        return {
            'running': self.running,
            'monitor_running': self.monitor.running,
            'check_interval': self.monitor.check_interval,
            'database_stats': self.db.get_availability_stats(hours=1)
        }


# Instancia global del scheduler
scheduler = None


def init_scheduler(db: Database):
    """Inicializa el scheduler global"""
    global scheduler
    scheduler = BackgroundScheduler(db)
    return scheduler


def get_scheduler() -> BackgroundScheduler:
    """Obtiene la instancia del scheduler"""
    global scheduler
    if scheduler is None:
        raise RuntimeError("Scheduler no inicializado. Llama a init_scheduler() primero.")
    return scheduler
