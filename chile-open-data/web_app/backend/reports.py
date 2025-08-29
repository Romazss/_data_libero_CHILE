"""
Sistema de Reportes Automatizados para la Biblioteca de Datos Abiertos de Chile
Genera reportes programados y exportaciones de datos
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
import json
import csv
import io
from pathlib import Path
import tempfile
from dataclasses import asdict

from analytics import AnalyticsEngine, AnalyticsMetrics
from models import Database
from notifications import create_system_notification

class ReportGenerator:
    """Generador de reportes del sistema"""
    
    def __init__(self, db: Database, analytics: AnalyticsEngine):
        self.db = db
        self.analytics = analytics
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """Genera reporte diario del sistema"""
        today = datetime.now(timezone.utc)
        yesterday = today - timedelta(days=1)
        
        # Métricas del día
        daily_metrics = self.analytics.generate_system_metrics(hours=24)
        
        # Comparación con día anterior
        previous_metrics = self.analytics.generate_system_metrics(hours=48)  # Last 48h to compare
        
        # Analytics por categoría
        category_analytics = self.analytics.generate_category_analytics(hours=24)
        
        # Top y problematic datasets
        top_datasets = self.analytics.get_top_performing_datasets(limit=5, hours=24)
        problematic_datasets = self.analytics.get_problematic_datasets(limit=5, hours=24)
        
        # Timeline data para gráficos
        timeline_data = self.analytics.generate_timeline_data(hours=24, interval_minutes=60)
        
        report = {
            "report_id": f"daily_{today.strftime('%Y%m%d')}",
            "generated_at": today.isoformat(),
            "period": {
                "start": yesterday.isoformat(),
                "end": today.isoformat(),
                "type": "daily"
            },
            "summary": {
                "total_datasets": daily_metrics.total_datasets,
                "available_datasets": daily_metrics.available_datasets,
                "uptime_percentage": round(daily_metrics.uptime_percentage, 2),
                "avg_latency": round(daily_metrics.avg_latency, 2),
                "reliability_score": round(daily_metrics.reliability_score, 2),
                "checks_performed": daily_metrics.checks_performed
            },
            "trends": {
                "uptime_change": self._calculate_change(daily_metrics.uptime_percentage, previous_metrics.uptime_percentage),
                "latency_change": self._calculate_change(daily_metrics.avg_latency, previous_metrics.avg_latency, inverse=True),
                "availability_change": daily_metrics.available_datasets - previous_metrics.available_datasets
            },
            "categories": category_analytics,
            "top_performing_datasets": top_datasets,
            "problematic_datasets": problematic_datasets,
            "timeline": timeline_data,
            "alerts": self._generate_alerts(daily_metrics, problematic_datasets),
            "recommendations": self._generate_recommendations(daily_metrics, category_analytics, problematic_datasets)
        }
        
        return report
    
    def generate_weekly_report(self) -> Dict[str, Any]:
        """Genera reporte semanal del sistema"""
        today = datetime.now(timezone.utc)
        week_ago = today - timedelta(days=7)
        
        # Métricas de la semana
        weekly_metrics = self.analytics.generate_system_metrics(hours=168)  # 7 days * 24 hours
        
        # Analytics por categoría
        category_analytics = self.analytics.generate_category_analytics(hours=168)
        
        # Top y problematic datasets de la semana
        top_datasets = self.analytics.get_top_performing_datasets(limit=10, hours=168)
        problematic_datasets = self.analytics.get_problematic_datasets(limit=10, hours=168)
        
        # Timeline semanal (datos cada 6 horas)
        timeline_data = self.analytics.generate_timeline_data(hours=168, interval_minutes=360)
        
        report = {
            "report_id": f"weekly_{today.strftime('%Y%W')}",
            "generated_at": today.isoformat(),
            "period": {
                "start": week_ago.isoformat(),
                "end": today.isoformat(),
                "type": "weekly"
            },
            "summary": {
                "total_datasets": weekly_metrics.total_datasets,
                "avg_uptime": round(weekly_metrics.uptime_percentage, 2),
                "avg_latency": round(weekly_metrics.avg_latency, 2),
                "reliability_score": round(weekly_metrics.reliability_score, 2),
                "total_checks": weekly_metrics.checks_performed,
                "most_problematic_category": weekly_metrics.most_problematic_category
            },
            "categories": category_analytics,
            "top_performing_datasets": top_datasets,
            "problematic_datasets": problematic_datasets,
            "timeline": timeline_data,
            "insights": self._generate_weekly_insights(weekly_metrics, category_analytics),
            "action_items": self._generate_action_items(problematic_datasets)
        }
        
        return report
    
    def _calculate_change(self, current: float, previous: float, inverse: bool = False) -> Dict[str, Any]:
        """Calcula el cambio porcentual entre dos valores"""
        if previous == 0:
            return {"change": 0, "direction": "stable", "percentage": 0}
        
        change = current - previous
        percentage = (change / previous) * 100
        
        if inverse:  # Para métricas donde menor es mejor (ej: latencia)
            percentage = -percentage
        
        direction = "improved" if percentage > 0 else "declined" if percentage < 0 else "stable"
        
        return {
            "change": round(change, 2),
            "direction": direction,
            "percentage": round(abs(percentage), 2)
        }
    
    def _generate_alerts(self, metrics: AnalyticsMetrics, problematic_datasets: List[Dict]) -> List[Dict[str, Any]]:
        """Genera alertas basadas en métricas"""
        alerts = []
        
        # Alerta de uptime bajo
        if metrics.uptime_percentage < 90:
            alerts.append({
                "type": "warning",
                "title": "Uptime Bajo",
                "message": f"El uptime del sistema es {metrics.uptime_percentage:.1f}%, por debajo del 90% esperado",
                "severity": "high" if metrics.uptime_percentage < 80 else "medium"
            })
        
        # Alerta de latencia alta
        if metrics.avg_latency > 2000:  # > 2 segundos
            alerts.append({
                "type": "warning",
                "title": "Latencia Alta",
                "message": f"La latencia promedio es {metrics.avg_latency:.0f}ms, superior a los 2000ms recomendados",
                "severity": "high" if metrics.avg_latency > 5000 else "medium"
            })
        
        # Alerta de datasets problemáticos
        if len(problematic_datasets) > 3:
            alerts.append({
                "type": "error",
                "title": "Múltiples Datasets Problemáticos",
                "message": f"{len(problematic_datasets)} datasets presentan problemas frecuentes",
                "severity": "high"
            })
        
        # Alerta de reliability score bajo
        if metrics.reliability_score < 70:
            alerts.append({
                "type": "error",
                "title": "Score de Confiabilidad Bajo",
                "message": f"El score de confiabilidad es {metrics.reliability_score:.1f}/100",
                "severity": "critical" if metrics.reliability_score < 50 else "high"
            })
        
        return alerts
    
    def _generate_recommendations(self, metrics: AnalyticsMetrics, categories: List[Dict], problematic: List[Dict]) -> List[str]:
        """Genera recomendaciones basadas en el análisis"""
        recommendations = []
        
        if metrics.uptime_percentage < 95:
            recommendations.append("Considerar implementar redundancia para datasets críticos")
        
        if metrics.avg_latency > 1500:
            recommendations.append("Investigar optimizaciones de red o caching para reducir latencia")
        
        if len(problematic) > 2:
            recommendations.append("Priorizar el monitoreo y mantenimiento de datasets problemáticos")
        
        # Recomendaciones por categoría
        for cat in categories:
            if cat['uptime_percentage'] < 85:
                recommendations.append(f"Mejorar la infraestructura de la categoría '{cat['category']}'")
        
        if not recommendations:
            recommendations.append("El sistema está funcionando dentro de parámetros normales")
        
        return recommendations
    
    def _generate_weekly_insights(self, metrics: AnalyticsMetrics, categories: List[Dict]) -> List[str]:
        """Genera insights para el reporte semanal"""
        insights = []
        
        # Insight sobre reliability
        if metrics.reliability_score > 90:
            insights.append("Excelente confiabilidad del sistema durante la semana")
        elif metrics.reliability_score > 75:
            insights.append("Confiabilidad del sistema dentro de rangos aceptables")
        else:
            insights.append("La confiabilidad del sistema necesita atención")
        
        # Insight sobre categorías
        if categories:
            best_category = max(categories, key=lambda x: x['uptime_percentage'])
            insights.append(f"La categoría '{best_category['category']}' tuvo el mejor rendimiento con {best_category['uptime_percentage']:.1f}% uptime")
        
        # Insight sobre checks
        if metrics.checks_performed > 1000:
            insights.append(f"Se realizaron {metrics.checks_performed} verificaciones durante la semana")
        
        return insights
    
    def _generate_action_items(self, problematic: List[Dict]) -> List[str]:
        """Genera elementos de acción basados en datasets problemáticos"""
        actions = []
        
        for dataset in problematic[:3]:  # Top 3 más problemáticos
            actions.append(f"Investigar problemas en '{dataset['name']}' (tasa de fallo: {dataset['failure_rate']:.1f}%)")
        
        if len(problematic) > 5:
            actions.append("Realizar auditoría completa de infraestructura de datasets")
        
        return actions
    
    def export_to_json(self, report: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Exporta reporte a JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.json"
        
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def export_to_csv(self, report: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Exporta datos del reporte a CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_data_{timestamp}.csv"
        
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['Metric', 'Value'])
            
            # Summary data
            summary = report.get('summary', {})
            for key, value in summary.items():
                writer.writerow([key.replace('_', ' ').title(), value])
            
            # Categories
            writer.writerow([])
            writer.writerow(['Category Analysis'])
            writer.writerow(['Category', 'Total Datasets', 'Uptime %', 'Avg Latency'])
            
            for cat in report.get('categories', []):
                writer.writerow([
                    cat['category'],
                    cat['total_datasets'],
                    cat['uptime_percentage'],
                    cat['avg_latency']
                ])
        
        return str(filepath)
    
    def save_report(self, report: Dict[str, Any], format: str = "json") -> str:
        """Guarda reporte en el formato especificado"""
        if format.lower() == "json":
            return self.export_to_json(report)
        elif format.lower() == "csv":
            return self.export_to_csv(report)
        else:
            raise ValueError(f"Formato no soportado: {format}")

class ScheduledReporter:
    """Manejador de reportes programados"""
    
    def __init__(self, db: Database):
        self.db = db
        self.analytics = AnalyticsEngine(db)
        self.generator = ReportGenerator(db, self.analytics)
        self.last_daily_report = None
        self.last_weekly_report = None
    
    def should_generate_daily_report(self) -> bool:
        """Verifica si debe generar reporte diario"""
        now = datetime.now(timezone.utc)
        
        # Generar a las 8:00 AM
        if now.hour != 8:
            return False
        
        # No generar si ya se generó hoy
        if self.last_daily_report and self.last_daily_report.date() == now.date():
            return False
        
        return True
    
    def should_generate_weekly_report(self) -> bool:
        """Verifica si debe generar reporte semanal"""
        now = datetime.now(timezone.utc)
        
        # Generar los lunes a las 9:00 AM
        if now.weekday() != 0 or now.hour != 9:  # 0 = Monday
            return False
        
        # No generar si ya se generó esta semana
        if self.last_weekly_report:
            week_start = now - timedelta(days=now.weekday())
            if self.last_weekly_report >= week_start.date():
                return False
        
        return True
    
    def generate_and_notify_daily_report(self) -> Optional[str]:
        """Genera reporte diario y envía notificación"""
        try:
            report = self.generator.generate_daily_report()
            filepath = self.generator.save_report(report, "json")
            
            # Crear notificación
            create_system_notification(
                title="Reporte Diario Generado",
                message=f"Reporte diario del {datetime.now().strftime('%d/%m/%Y')} disponible. Uptime: {report['summary']['uptime_percentage']}%",
                notification_type="info",
                data={"report_id": report["report_id"], "filepath": filepath}
            )
            
            self.last_daily_report = datetime.now(timezone.utc).date()
            return filepath
            
        except Exception as e:
            create_system_notification(
                title="Error en Reporte Diario",
                message=f"No se pudo generar el reporte diario: {str(e)}",
                notification_type="error"
            )
            return None
    
    def generate_and_notify_weekly_report(self) -> Optional[str]:
        """Genera reporte semanal y envía notificación"""
        try:
            report = self.generator.generate_weekly_report()
            filepath = self.generator.save_report(report, "json")
            
            # Crear notificación
            create_system_notification(
                title="Reporte Semanal Generado",
                message=f"Reporte semanal disponible. Score de confiabilidad: {report['summary']['reliability_score']}/100",
                notification_type="info",
                data={"report_id": report["report_id"], "filepath": filepath}
            )
            
            self.last_weekly_report = datetime.now(timezone.utc).date()
            return filepath
            
        except Exception as e:
            create_system_notification(
                title="Error en Reporte Semanal",
                message=f"No se pudo generar el reporte semanal: {str(e)}",
                notification_type="error"
            )
            return None
    
    def check_and_generate_reports(self):
        """Verifica y genera reportes si es necesario"""
        if self.should_generate_daily_report():
            self.generate_and_notify_daily_report()
        
        if self.should_generate_weekly_report():
            self.generate_and_notify_weekly_report()
