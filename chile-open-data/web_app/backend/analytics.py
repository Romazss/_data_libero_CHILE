"""
Módulo de Analytics para la Biblioteca de Datos Abiertos de Chile
Proporciona métricas avanzadas, reportes y análisis de tendencias
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import sqlite3
import json
import statistics
from collections import defaultdict, Counter

from models import Database

@dataclass
class AnalyticsMetrics:
    """Métricas de analytics del sistema"""
    timestamp: datetime
    total_datasets: int
    available_datasets: int
    unavailable_datasets: int
    error_datasets: int
    avg_latency: float
    max_latency: float
    min_latency: float
    uptime_percentage: float
    checks_performed: int
    categories_count: int
    most_problematic_category: str
    reliability_score: float  # 0-100
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

@dataclass
class DatasetAnalytics:
    """Analytics específicos de un dataset"""
    dataset_id: str
    dataset_name: str
    category: str
    total_checks: int
    successful_checks: int
    failed_checks: int
    uptime_percentage: float
    avg_latency: float
    last_failure: Optional[datetime]
    failure_frequency: float  # failures per day
    reliability_trend: str  # 'improving', 'declining', 'stable'
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        if self.last_failure:
            result['last_failure'] = self.last_failure.isoformat()
        return result

class AnalyticsEngine:
    """Motor de analytics para generar métricas y reportes"""
    
    def __init__(self, db: Database):
        self.db = db
        
    def generate_system_metrics(self, hours: int = 24) -> AnalyticsMetrics:
        """Genera métricas del sistema para las últimas X horas"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Obtener datos de las últimas X horas
                since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
                
                # Métricas básicas
                cursor = conn.execute("""
                    SELECT 
                        COUNT(DISTINCT dataset_id) as total_datasets,
                        COUNT(*) as total_checks,
                        SUM(CASE WHEN status = 'up' THEN 1 ELSE 0 END) as successful_checks,
                        SUM(CASE WHEN status = 'down' THEN 1 ELSE 0 END) as failed_checks,
                        AVG(CASE WHEN latency_ms IS NOT NULL THEN latency_ms ELSE 0 END) as avg_latency,
                        MAX(CASE WHEN latency_ms IS NOT NULL THEN latency_ms ELSE 0 END) as max_latency,
                        MIN(CASE WHEN latency_ms IS NOT NULL THEN latency_ms ELSE 0 END) as min_latency
                    FROM dataset_status 
                    WHERE checked_at >= ?
                """, (since_time.isoformat(),))
                
                basic_metrics = cursor.fetchone()
                
                # Estados actuales por dataset
                cursor = conn.execute("""
                    SELECT 
                        dataset_id,
                        status,
                        category,
                        ROW_NUMBER() OVER (PARTITION BY dataset_id ORDER BY checked_at DESC) as rn
                    FROM dataset_status
                    WHERE checked_at >= ?
                """, (since_time.isoformat(),))
                
                current_statuses = [row for row in cursor.fetchall() if row['rn'] == 1]
                
                # Contar estados actuales
                available = sum(1 for row in current_statuses if row['status'] == 'up')
                unavailable = sum(1 for row in current_statuses if row['status'] == 'down')
                
                # Contar categorías
                categories = set(row['category'] for row in current_statuses if row['category'])
                
                # Categoría más problemática
                category_problems = defaultdict(int)
                for row in current_statuses:
                    if row['status'] == 'down' and row['category']:
                        category_problems[row['category']] += 1
                
                most_problematic = max(category_problems.items(), key=lambda x: x[1])[0] if category_problems else "Ninguna"
                
                # Calcular uptime y reliability
                total_checks = basic_metrics['total_checks'] or 1
                successful_checks = basic_metrics['successful_checks'] or 0
                uptime_percentage = (successful_checks / total_checks) * 100
                
                # Reliability score (combina uptime y latencia)
                latency_penalty = min(basic_metrics['avg_latency'] / 1000, 20)  # Max 20 points penalty
                reliability_score = max(0, uptime_percentage - latency_penalty)
                
                return AnalyticsMetrics(
                    timestamp=datetime.now(timezone.utc),
                    total_datasets=basic_metrics['total_datasets'] or 0,
                    available_datasets=available,
                    unavailable_datasets=unavailable,
                    error_datasets=unavailable,  # For now, same as unavailable
                    avg_latency=basic_metrics['avg_latency'] or 0,
                    max_latency=basic_metrics['max_latency'] or 0,
                    min_latency=basic_metrics['min_latency'] or 0,
                    uptime_percentage=uptime_percentage,
                    checks_performed=total_checks,
                    categories_count=len(categories),
                    most_problematic_category=most_problematic,
                    reliability_score=reliability_score
                )
                
        except Exception as e:
            # Return default metrics in case of error
            return AnalyticsMetrics(
                timestamp=datetime.now(timezone.utc),
                total_datasets=0, available_datasets=0, unavailable_datasets=0,
                error_datasets=0, avg_latency=0, max_latency=0, min_latency=0,
                uptime_percentage=0, checks_performed=0, categories_count=0,
                most_problematic_category="Unknown", reliability_score=0
            )
    
    def generate_dataset_analytics(self, dataset_id: str, days: int = 7) -> Optional[DatasetAnalytics]:
        """Genera analytics para un dataset específico"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                since_time = datetime.now(timezone.utc) - timedelta(days=days)
                
                # Obtener datos del dataset
                cursor = conn.execute("""
                    SELECT * FROM dataset_status 
                    WHERE dataset_id = ? AND checked_at >= ?
                    ORDER BY checked_at DESC
                """, (dataset_id, since_time.isoformat()))
                
                records = cursor.fetchall()
                if not records:
                    return None
                
                # Calcular métricas
                total_checks = len(records)
                successful_checks = sum(1 for r in records if r['status'] == 'up')
                failed_checks = total_checks - successful_checks
                uptime_percentage = (successful_checks / total_checks) * 100 if total_checks > 0 else 0
                
                # Latencia promedio
                latencies = [r['latency_ms'] for r in records if r['latency_ms'] is not None]
                avg_latency = statistics.mean(latencies) if latencies else 0
                
                # Último fallo
                last_failure = None
                for record in records:
                    if record['status'] == 'down':
                        last_failure = datetime.fromisoformat(record['checked_at'])
                        break
                
                # Frecuencia de fallos (fallos por día)
                failure_frequency = failed_checks / days if days > 0 else 0
                
                # Tendencia de confiabilidad (últimos 3 vs primeros 3 días)
                reliability_trend = self._calculate_reliability_trend(records, days)
                
                dataset_info = records[0]  # Más reciente
                
                return DatasetAnalytics(
                    dataset_id=dataset_id,
                    dataset_name=dataset_info['name'],
                    category=dataset_info['category'],
                    total_checks=total_checks,
                    successful_checks=successful_checks,
                    failed_checks=failed_checks,
                    uptime_percentage=uptime_percentage,
                    avg_latency=avg_latency,
                    last_failure=last_failure,
                    failure_frequency=failure_frequency,
                    reliability_trend=reliability_trend
                )
                
        except Exception as e:
            return None
    
    def _calculate_reliability_trend(self, records: List, days: int) -> str:
        """Calcula la tendencia de confiabilidad"""
        if len(records) < 6:  # Necesitamos al menos 6 registros
            return 'stable'
        
        mid_point = len(records) // 2
        recent_records = records[:mid_point]
        older_records = records[mid_point:]
        
        recent_uptime = sum(1 for r in recent_records if r['status'] == 'up') / len(recent_records)
        older_uptime = sum(1 for r in older_records if r['status'] == 'up') / len(older_records)
        
        difference = recent_uptime - older_uptime
        
        if difference > 0.1:  # 10% improvement
            return 'improving'
        elif difference < -0.1:  # 10% decline
            return 'declining'
        else:
            return 'stable'
    
    def generate_category_analytics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Genera analytics por categoría"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
                
                cursor = conn.execute("""
                    SELECT 
                        category,
                        COUNT(DISTINCT dataset_id) as total_datasets,
                        COUNT(*) as total_checks,
                        SUM(CASE WHEN status = 'up' THEN 1 ELSE 0 END) as successful_checks,
                        AVG(CASE WHEN latency_ms IS NOT NULL THEN latency_ms ELSE 0 END) as avg_latency
                    FROM dataset_status 
                    WHERE checked_at >= ? AND category IS NOT NULL
                    GROUP BY category
                    ORDER BY total_datasets DESC
                """, (since_time.isoformat(),))
                
                categories = []
                for row in cursor.fetchall():
                    uptime = (row['successful_checks'] / row['total_checks']) * 100 if row['total_checks'] > 0 else 0
                    categories.append({
                        'category': row['category'],
                        'total_datasets': row['total_datasets'],
                        'uptime_percentage': round(uptime, 2),
                        'avg_latency': round(row['avg_latency'], 2),
                        'total_checks': row['total_checks']
                    })
                
                return categories
                
        except Exception as e:
            return []
    
    def generate_timeline_data(self, hours: int = 24, interval_minutes: int = 60) -> List[Dict[str, Any]]:
        """Genera datos de timeline para gráficos"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
                
                cursor = conn.execute("""
                    SELECT 
                        strftime('%Y-%m-%d %H:00:00', checked_at) as hour_bucket,
                        COUNT(*) as total_checks,
                        SUM(CASE WHEN status = 'up' THEN 1 ELSE 0 END) as successful_checks,
                        AVG(CASE WHEN latency_ms IS NOT NULL THEN latency_ms ELSE 0 END) as avg_latency
                    FROM dataset_status 
                    WHERE checked_at >= ?
                    GROUP BY hour_bucket
                    ORDER BY hour_bucket
                """, (since_time.isoformat(),))
                
                timeline = []
                for row in cursor.fetchall():
                    uptime = (row['successful_checks'] / row['total_checks']) * 100 if row['total_checks'] > 0 else 0
                    timeline.append({
                        'timestamp': row['hour_bucket'],
                        'uptime_percentage': round(uptime, 2),
                        'avg_latency': round(row['avg_latency'], 2),
                        'total_checks': row['total_checks']
                    })
                
                return timeline
                
        except Exception as e:
            return []
    
    def get_top_performing_datasets(self, limit: int = 10, hours: int = 24) -> List[Dict[str, Any]]:
        """Obtiene los datasets con mejor rendimiento"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
                
                cursor = conn.execute("""
                    SELECT 
                        dataset_id,
                        name,
                        category,
                        COUNT(*) as total_checks,
                        SUM(CASE WHEN status = 'up' THEN 1 ELSE 0 END) as successful_checks,
                        AVG(CASE WHEN latency_ms IS NOT NULL THEN latency_ms ELSE 0 END) as avg_latency
                    FROM dataset_status 
                    WHERE checked_at >= ?
                    GROUP BY dataset_id, name, category
                    HAVING total_checks >= 3
                    ORDER BY (successful_checks * 1.0 / total_checks) DESC, avg_latency ASC
                    LIMIT ?
                """, (since_time.isoformat(), limit))
                
                top_datasets = []
                for row in cursor.fetchall():
                    uptime = (row['successful_checks'] / row['total_checks']) * 100
                    top_datasets.append({
                        'dataset_id': row['dataset_id'],
                        'name': row['name'],
                        'category': row['category'],
                        'uptime_percentage': round(uptime, 2),
                        'avg_latency': round(row['avg_latency'], 2),
                        'total_checks': row['total_checks']
                    })
                
                return top_datasets
                
        except Exception as e:
            return []
    
    def get_problematic_datasets(self, limit: int = 10, hours: int = 24) -> List[Dict[str, Any]]:
        """Obtiene los datasets con más problemas"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
                
                cursor = conn.execute("""
                    SELECT 
                        dataset_id,
                        name,
                        category,
                        COUNT(*) as total_checks,
                        SUM(CASE WHEN status = 'down' THEN 1 ELSE 0 END) as failed_checks,
                        AVG(CASE WHEN latency_ms IS NOT NULL THEN latency_ms ELSE 0 END) as avg_latency
                    FROM dataset_status 
                    WHERE checked_at >= ?
                    GROUP BY dataset_id, name, category
                    HAVING total_checks >= 3
                    ORDER BY (failed_checks * 1.0 / total_checks) DESC, avg_latency DESC
                    LIMIT ?
                """, (since_time.isoformat(), limit))
                
                problematic_datasets = []
                for row in cursor.fetchall():
                    failure_rate = (row['failed_checks'] / row['total_checks']) * 100
                    problematic_datasets.append({
                        'dataset_id': row['dataset_id'],
                        'name': row['name'],
                        'category': row['category'],
                        'failure_rate': round(failure_rate, 2),
                        'avg_latency': round(row['avg_latency'], 2),
                        'total_checks': row['total_checks'],
                        'failed_checks': row['failed_checks']
                    })
                
                return problematic_datasets
                
        except Exception as e:
            return []
