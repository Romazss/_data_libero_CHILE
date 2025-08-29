# backend app.py - Fase 2
# /web_app/backend/app.py
"""
Backend robusto para la Biblioteca de Datos Abiertos de Chile - Fase 2
API REST completa con base de datos, cache y monitoreo automático
"""

import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from datetime import datetime, timezone
import logging

# Imports locales
from services.sources import load_sources, SourceConfigError
from services.checker import check_all
from models import Database
from cache import cache, cached, invalidate_datasets_cache
from scheduler import init_scheduler, get_scheduler
from notifications import notification_manager, create_system_notification
from websockets import WebSocketManager
from analytics import AnalyticsEngine
from reports import ReportGenerator, ScheduledReporter


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)
CORS(app)  # habilita CORS para el frontend

# Configurar SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Inicializar WebSocket Manager
ws_manager = WebSocketManager(socketio)

# Configuración
app.config['DATABASE_PATH'] = os.getenv('DATABASE_PATH', 'data/chile_data.db')
app.config['CACHE_DEFAULT_TIMEOUT'] = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))
app.config['MONITOR_ENABLED'] = os.getenv('MONITOR_ENABLED', 'true').lower() == 'true'
app.config['MONITOR_INTERVAL'] = int(os.getenv('MONITOR_INTERVAL', '300'))

# Inicializar base de datos
db = Database(app.config['DATABASE_PATH'])

# Inicializar analytics y reportes
analytics_engine = AnalyticsEngine(db)
report_generator = ReportGenerator(db, analytics_engine)
scheduled_reporter = ScheduledReporter(db)

# Inicializar scheduler si está habilitado
if app.config['MONITOR_ENABLED']:
    scheduler = init_scheduler(db)
    scheduler.start()
    logger.info("Monitoreo automático iniciado")


@app.route("/health")
def health():
    """Endpoint de salud del servicio"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
        "database": "connected",
        "cache_stats": cache.stats()
    })


@app.route("/status")
@cached(ttl=60, key_prefix="api")  # Cache por 1 minuto
def status():
    """Estado actual de todos los datasets"""
    try:
        # Intentar obtener de la base de datos primero
        latest_status = db.get_latest_status()
        
        if not latest_status:
            # Si no hay datos en BD, hacer check en vivo
            datasets = load_sources()
            db.register_datasets(datasets)
            results = check_all(datasets)
            
            # Guardar en BD
            check_time = datetime.now(timezone.utc)
            for result in results:
                from models import DatasetStatus
                status_obj = DatasetStatus(
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
                db.save_dataset_status(status_obj)
            
            latest_status = results
        
        return jsonify({
            "count": len(latest_status),
            "results": latest_status,
            "last_updated": latest_status[0]['checked_at'] if latest_status else None
        })
        
    except SourceConfigError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(f"Error in /status: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/datasets")
@cached(ttl=300, key_prefix="api")  # Cache por 5 minutos
def get_datasets():
    """Lista todos los datasets registrados"""
    try:
        category = request.args.get('category')
        active_only = request.args.get('active', 'true').lower() == 'true'
        
        datasets = db.get_registered_datasets(active_only=active_only)
        
        if category:
            datasets = [ds for ds in datasets if ds['category'].lower() == category.lower()]
        
        return jsonify({
            "count": len(datasets),
            "datasets": datasets
        })
        
    except Exception as e:
        logger.error(f"Error in /datasets: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/datasets/<dataset_id>/history")
def get_dataset_history(dataset_id: str):
    """Histórico de un dataset específico"""
    try:
        hours = int(request.args.get('hours', 24))
        history = db.get_dataset_history(dataset_id, hours=hours)
        
        if not history:
            return jsonify({"error": "Dataset not found or no history available"}), 404
        
        return jsonify({
            "dataset_id": dataset_id,
            "hours": hours,
            "count": len(history),
            "history": history
        })
        
    except ValueError:
        return jsonify({"error": "Invalid hours parameter"}), 400
    except Exception as e:
        logger.error(f"Error in /datasets/{dataset_id}/history: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/stats")
@cached(ttl=120, key_prefix="api")  # Cache por 2 minutos
def get_stats():
    """Estadísticas generales de disponibilidad"""
    try:
        hours = int(request.args.get('hours', 24))
        stats = db.get_availability_stats(hours=hours)
        
        return jsonify({
            "hours": hours,
            "stats": stats,
            "generated_at": datetime.now(timezone.utc).isoformat()
        })
        
    except ValueError:
        return jsonify({"error": "Invalid hours parameter"}), 400
    except Exception as e:
        logger.error(f"Error in /stats: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/categories")
@cached(ttl=600, key_prefix="api")  # Cache por 10 minutos
def get_categories():
    """Lista todas las categorías disponibles"""
    try:
        datasets = db.get_registered_datasets()
        categories = {}
        
        for dataset in datasets:
            cat = dataset['category']
            if cat not in categories:
                categories[cat] = {
                    'name': cat,
                    'count': 0,
                    'datasets': []
                }
            categories[cat]['count'] += 1
            categories[cat]['datasets'].append({
                'id': dataset['id'],
                'name': dataset['name']
            })
        
        return jsonify({
            "count": len(categories),
            "categories": list(categories.values())
        })
        
    except Exception as e:
        logger.error(f"Error in /categories: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/check", methods=['POST'])
def force_check():
    """Fuerza una verificación inmediata de todos los datasets"""
    try:
        # Solo permitir si el monitoreo está habilitado
        if not app.config['MONITOR_ENABLED']:
            return jsonify({"error": "Monitoring is disabled"}), 503
        
        scheduler = get_scheduler()
        scheduler.monitor.force_check()
        
        # Invalidar cache
        invalidate_datasets_cache()
        
        return jsonify({
            "message": "Check forced successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in /check: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/admin/cache", methods=['DELETE'])
def clear_cache():
    """Limpia el cache (endpoint de administración)"""
    try:
        cache.clear()
        return jsonify({"message": "Cache cleared successfully"})
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/admin/cache/stats")
def cache_stats():
    """Estadísticas del cache"""
    try:
        stats = cache.stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/admin/scheduler")
def scheduler_status():
    """Estado del scheduler"""
    try:
        if not app.config['MONITOR_ENABLED']:
            return jsonify({"status": "disabled"})
        
        scheduler = get_scheduler()
        status = scheduler.get_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return jsonify({"error": "Internal server error"}), 500


# Servir archivos estáticos del frontend
@app.route('/')
def serve_frontend():
    """Servir la página principal del frontend"""
    return send_from_directory('../frontend', 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Servir archivos estáticos"""
    return send_from_directory('../frontend', filename)


# Manejador de errores
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


# === ENDPOINTS DE NOTIFICACIONES ===

@app.route("/api/notifications")
def get_notifications():
    """Obtiene las notificaciones recientes"""
    try:
        limit = request.args.get('limit', 50, type=int)
        notifications = notification_manager.get_notifications(limit)
        unread_count = notification_manager.get_unread_count()
        
        return jsonify({
            "notifications": notifications,
            "unread_count": unread_count,
            "total": len(notifications)
        })
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({"error": "Failed to get notifications"}), 500


@app.route("/api/notifications/<notification_id>/read", methods=["POST"])
def mark_notification_read(notification_id):
    """Marca una notificación como leída"""
    try:
        success = notification_manager.mark_as_read(notification_id)
        unread_count = notification_manager.get_unread_count()
        
        if success:
            # Notificar via WebSocket
            ws_manager.socketio.emit('notification_marked_read', {
                'notification_id': notification_id,
                'unread_count': unread_count
            }, room='general')
            
            return jsonify({
                "success": True,
                "unread_count": unread_count
            })
        else:
            return jsonify({"error": "Notification not found"}), 404
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return jsonify({"error": "Failed to mark notification as read"}), 500


@app.route("/api/notifications/clear", methods=["POST"])
def clear_notifications():
    """Limpia todas las notificaciones"""
    try:
        notification_manager.clear_notifications()
        
        # Notificar via WebSocket
        ws_manager.socketio.emit('notifications_cleared', room='general')
        
        return jsonify({"success": True, "message": "All notifications cleared"})
    except Exception as e:
        logger.error(f"Error clearing notifications: {e}")
        return jsonify({"error": "Failed to clear notifications"}), 500


@app.route("/api/notifications/test", methods=["POST"])
def create_test_notification():
    """Crea una notificación de prueba (solo para desarrollo)"""
    try:
        data = request.get_json() or {}
        notification_type = data.get('type', 'info')
        title = data.get('title', 'Notificación de prueba')
        message = data.get('message', 'Esta es una notificación de prueba generada desde la API')
        
        notification = create_system_notification(
            title=title,
            message=message,
            notification_type=notification_type,
            data={'test': True, 'created_via': 'api'}
        )
        
        return jsonify({
            "success": True,
            "notification": notification.to_dict()
        })
    except Exception as e:
        logger.error(f"Error creating test notification: {e}")
        return jsonify({"error": "Failed to create test notification"}), 500


# === ENDPOINTS DE WEBSOCKETS STATUS ===

@app.route("/api/websockets/status")
def websocket_status():
    """Estado de las conexiones WebSocket"""
    try:
        client_info = ws_manager.get_client_info()
        return jsonify({
            "websocket_enabled": True,
            "connected_clients": client_info['total_clients'],
            "clients_info": client_info['clients']
        })
    except Exception as e:
        logger.error(f"Error getting WebSocket status: {e}")
        return jsonify({"error": "Failed to get WebSocket status"}), 500


# === ENDPOINTS DE ANALYTICS ===

@app.route("/api/analytics/metrics")
def get_analytics_metrics():
    """Obtiene métricas de analytics del sistema"""
    try:
        hours = request.args.get('hours', 24, type=int)
        metrics = analytics_engine.generate_system_metrics(hours=hours)
        
        return jsonify({
            "success": True,
            "metrics": metrics.to_dict(),
            "period_hours": hours
        })
    except Exception as e:
        logger.error(f"Error getting analytics metrics: {e}")
        return jsonify({"error": "Failed to get analytics metrics"}), 500


@app.route("/api/analytics/categories")
def get_category_analytics():
    """Obtiene analytics por categoría"""
    try:
        hours = request.args.get('hours', 24, type=int)
        categories = analytics_engine.generate_category_analytics(hours=hours)
        
        return jsonify({
            "success": True,
            "categories": categories,
            "period_hours": hours
        })
    except Exception as e:
        logger.error(f"Error getting category analytics: {e}")
        return jsonify({"error": "Failed to get category analytics"}), 500


@app.route("/api/analytics/timeline")
def get_timeline_analytics():
    """Obtiene datos de timeline para gráficos"""
    try:
        hours = request.args.get('hours', 24, type=int)
        interval = request.args.get('interval', 60, type=int)
        timeline = analytics_engine.generate_timeline_data(hours=hours, interval_minutes=interval)
        
        return jsonify({
            "success": True,
            "timeline": timeline,
            "period_hours": hours,
            "interval_minutes": interval
        })
    except Exception as e:
        logger.error(f"Error getting timeline analytics: {e}")
        return jsonify({"error": "Failed to get timeline analytics"}), 500


@app.route("/api/analytics/datasets/top")
def get_top_datasets():
    """Obtiene los datasets con mejor rendimiento"""
    try:
        limit = request.args.get('limit', 10, type=int)
        hours = request.args.get('hours', 24, type=int)
        top_datasets = analytics_engine.get_top_performing_datasets(limit=limit, hours=hours)
        
        return jsonify({
            "success": True,
            "datasets": top_datasets,
            "limit": limit,
            "period_hours": hours
        })
    except Exception as e:
        logger.error(f"Error getting top datasets: {e}")
        return jsonify({"error": "Failed to get top datasets"}), 500


@app.route("/api/analytics/datasets/problematic")
def get_problematic_datasets():
    """Obtiene los datasets con más problemas"""
    try:
        limit = request.args.get('limit', 10, type=int)
        hours = request.args.get('hours', 24, type=int)
        problematic = analytics_engine.get_problematic_datasets(limit=limit, hours=hours)
        
        return jsonify({
            "success": True,
            "datasets": problematic,
            "limit": limit,
            "period_hours": hours
        })
    except Exception as e:
        logger.error(f"Error getting problematic datasets: {e}")
        return jsonify({"error": "Failed to get problematic datasets"}), 500


@app.route("/api/analytics/dataset/<dataset_id>")
def get_dataset_analytics(dataset_id):
    """Obtiene analytics de un dataset específico"""
    try:
        days = request.args.get('days', 7, type=int)
        analytics = analytics_engine.generate_dataset_analytics(dataset_id=dataset_id, days=days)
        
        if analytics:
            return jsonify({
                "success": True,
                "analytics": analytics.to_dict(),
                "period_days": days
            })
        else:
            return jsonify({"error": "Dataset not found or no data available"}), 404
    except Exception as e:
        logger.error(f"Error getting dataset analytics: {e}")
        return jsonify({"error": "Failed to get dataset analytics"}), 500


# === ENDPOINTS DE REPORTES ===

@app.route("/api/reports/daily")
def generate_daily_report():
    """Genera reporte diario"""
    try:
        report = report_generator.generate_daily_report()
        
        # Opcionalmente guardar el reporte
        save = request.args.get('save', 'false').lower() == 'true'
        filepath = None
        if save:
            format_type = request.args.get('format', 'json')
            filepath = report_generator.save_report(report, format_type)
        
        return jsonify({
            "success": True,
            "report": report,
            "saved_to": filepath
        })
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        return jsonify({"error": "Failed to generate daily report"}), 500


@app.route("/api/reports/weekly")
def generate_weekly_report():
    """Genera reporte semanal"""
    try:
        report = report_generator.generate_weekly_report()
        
        # Opcionalmente guardar el reporte
        save = request.args.get('save', 'false').lower() == 'true'
        filepath = None
        if save:
            format_type = request.args.get('format', 'json')
            filepath = report_generator.save_report(report, format_type)
        
        return jsonify({
            "success": True,
            "report": report,
            "saved_to": filepath
        })
    except Exception as e:
        logger.error(f"Error generating weekly report: {e}")
        return jsonify({"error": "Failed to generate weekly report"}), 500


@app.route("/api/reports/export/<report_type>")
def export_report(report_type):
    """Exporta un reporte en el formato especificado"""
    try:
        format_type = request.args.get('format', 'json')
        
        if report_type == 'daily':
            report = report_generator.generate_daily_report()
        elif report_type == 'weekly':
            report = report_generator.generate_weekly_report()
        else:
            return jsonify({"error": "Invalid report type"}), 400
        
        filepath = report_generator.save_report(report, format_type)
        
        return jsonify({
            "success": True,
            "report_type": report_type,
            "format": format_type,
            "filepath": filepath,
            "download_url": f"/api/reports/download/{filepath.split('/')[-1]}"
        })
    except Exception as e:
        logger.error(f"Error exporting report: {e}")
        return jsonify({"error": "Failed to export report"}), 500


@app.route("/api/reports/download/<filename>")
def download_report(filename):
    """Descarga un archivo de reporte"""
    try:
        reports_dir = "reports"
        return send_from_directory(reports_dir, filename, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        return jsonify({"error": "File not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# Limpieza al cerrar la aplicación
@app.teardown_appcontext
def cleanup(error):
    """Limpieza al cerrar contexto"""
    if error:
        logger.error(f"Application error: {error}")


def shutdown_handler():
    """Manejador de cierre limpio"""
    try:
        if app.config['MONITOR_ENABLED']:
            scheduler = get_scheduler()
            scheduler.stop()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


if __name__ == "__main__":
    import atexit
    atexit.register(shutdown_handler)
    
    # Configuración para desarrollo
    host = os.getenv('BACKEND_HOST', '0.0.0.0')
    port = int(os.getenv('BACKEND_PORT', '5001'))
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    
    logger.info(f"Iniciando servidor con WebSockets en {host}:{port} (debug={debug})")
    
    # Crear notificación de inicio del sistema
    create_system_notification(
        title="Sistema Iniciado",
        message=f"El servidor se ha iniciado correctamente en {host}:{port}",
        notification_type="success"
    )
    
    # Usar SocketIO en lugar de app.run() para soporte de WebSockets
    socketio.run(app, host=host, port=port, debug=debug)