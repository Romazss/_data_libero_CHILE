# /web_app/backend/models.py
"""
Modelos de base de datos para la Biblioteca de Datos Abiertos de Chile
"""

from datetime import datetime, timezone
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import json


@dataclass
class DatasetStatus:
    """Modelo para el estado de un dataset"""
    id: str
    name: str
    category: str
    url: str
    status: str  # 'up', 'down', 'unknown'
    http_code: Optional[int]
    latency_ms: Optional[float]
    error: Optional[str]
    checked_at: datetime
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'url': self.url,
            'status': self.status,
            'http_code': self.http_code,
            'latency_ms': self.latency_ms,
            'error': self.error,
            'checked_at': self.checked_at.isoformat()
        }


class Database:
    """Manejador de base de datos SQLite"""
    
    def __init__(self, db_path: str = "data/chile_data.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Inicializa las tablas de la base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dataset_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    http_code INTEGER,
                    latency_ms REAL,
                    error TEXT,
                    checked_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (dataset_id) REFERENCES datasets (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS datasets (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    url TEXT NOT NULL,
                    description TEXT,
                    method TEXT DEFAULT 'HEAD',
                    timeout INTEGER DEFAULT 10,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL UNIQUE,
                    total_datasets INTEGER NOT NULL,
                    available_count INTEGER NOT NULL,
                    avg_latency_ms REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices para mejor performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dataset_status_dataset_id ON dataset_status (dataset_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dataset_status_checked_at ON dataset_status (checked_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_datasets_category ON datasets (category)")
            
            conn.commit()
    
    def save_dataset_status(self, status: DatasetStatus):
        """Guarda el estado de un dataset"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO dataset_status 
                (dataset_id, name, category, url, status, http_code, latency_ms, error, checked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                status.id, status.name, status.category, status.url,
                status.status, status.http_code, status.latency_ms,
                status.error, status.checked_at
            ))
            conn.commit()
    
    def get_latest_status(self) -> List[Dict]:
        """Obtiene el estado más reciente de todos los datasets"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT 
                    dataset_id as id,
                    name,
                    category,
                    url,
                    status,
                    http_code,
                    latency_ms,
                    error,
                    checked_at,
                    ROW_NUMBER() OVER (PARTITION BY dataset_id ORDER BY checked_at DESC) as rn
                FROM dataset_status
            """)
            
            rows = cursor.fetchall()
            # Filtrar solo los más recientes
            latest = [dict(row) for row in rows if row['rn'] == 1]
            return latest
    
    def get_dataset_history(self, dataset_id: str, hours: int = 24) -> List[Dict]:
        """Obtiene el histórico de un dataset específico"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM dataset_status 
                WHERE dataset_id = ? 
                AND checked_at >= datetime('now', '-{} hours')
                ORDER BY checked_at DESC
            """.format(hours), (dataset_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_availability_stats(self, hours: int = 24) -> Dict:
        """Obtiene estadísticas de disponibilidad"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Estadísticas generales
            cursor = conn.execute("""
                SELECT 
                    COUNT(DISTINCT dataset_id) as total_datasets,
                    COUNT(*) as total_checks,
                    SUM(CASE WHEN status = 'up' THEN 1 ELSE 0 END) as successful_checks,
                    AVG(CASE WHEN latency_ms IS NOT NULL THEN latency_ms END) as avg_latency
                FROM dataset_status 
                WHERE checked_at >= datetime('now', '-{} hours')
            """.format(hours))
            
            stats = dict(cursor.fetchone())
            
            # Estadísticas por categoría
            cursor = conn.execute("""
                SELECT 
                    category,
                    COUNT(DISTINCT dataset_id) as dataset_count,
                    COUNT(*) as check_count,
                    SUM(CASE WHEN status = 'up' THEN 1 ELSE 0 END) as successful_count,
                    AVG(CASE WHEN latency_ms IS NOT NULL THEN latency_ms END) as avg_latency
                FROM dataset_status 
                WHERE checked_at >= datetime('now', '-{} hours')
                GROUP BY category
                ORDER BY category
            """.format(hours))
            
            stats['by_category'] = [dict(row) for row in cursor.fetchall()]
            
            return stats
    
    def register_datasets(self, datasets: List[Dict]):
        """Registra/actualiza datasets en la base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            for dataset in datasets:
                conn.execute("""
                    INSERT OR REPLACE INTO datasets 
                    (id, name, category, url, description, method, timeout, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dataset['id'],
                    dataset['name'],
                    dataset['category'],
                    dataset['url'],
                    dataset.get('description'),
                    dataset.get('method', 'HEAD'),
                    dataset.get('timeout', 10),
                    datetime.now(timezone.utc)
                ))
            conn.commit()
    
    def get_registered_datasets(self, active_only: bool = True) -> List[Dict]:
        """Obtiene los datasets registrados"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM datasets"
            if active_only:
                query += " WHERE active = 1"
            query += " ORDER BY category, name"
            
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_data(self, days: int = 30):
        """Limpia datos antiguos para mantener la base de datos ligera"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM dataset_status 
                WHERE checked_at < datetime('now', '-{} days')
            """.format(days))
            conn.commit()
