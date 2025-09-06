# /web_app/backend/auth.py
"""
Sistema de autenticación y autorización para API pública
Manejo de API keys, rate limiting y permisos
"""

import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from functools import wraps
from flask import request, jsonify, g
import sqlite3
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class APIKey:
    """Modelo para API Keys"""
    key_id: str
    key_hash: str
    name: str
    description: str
    user_email: str
    tier: str  # 'free', 'pro', 'enterprise'
    created_at: datetime
    last_used: Optional[datetime]
    is_active: bool
    rate_limit_per_hour: int
    rate_limit_per_day: int
    allowed_endpoints: List[str]  # '*' para todos
    metadata: Dict

@dataclass 
class APIUsage:
    """Registro de uso de API"""
    key_id: str
    endpoint: str
    method: str
    timestamp: datetime
    response_time_ms: float
    status_code: int
    user_agent: Optional[str]
    ip_address: Optional[str]

class APIKeyManager:
    """Gestor de API Keys y autenticación"""
    
    def __init__(self, db_path: str = "data/chile_data.db"):
        self.db_path = db_path
        self._init_auth_tables()
        
        # Configuración de tiers
        self.TIER_LIMITS = {
            'free': {
                'requests_per_hour': 100,
                'requests_per_day': 1000,
                'allowed_endpoints': [
                    '/health', '/status', '/stats', '/categories',
                    '/api/analytics/system-metrics', '/api/analytics/top-datasets'
                ]
            },
            'pro': {
                'requests_per_hour': 1000,
                'requests_per_day': 10000,
                'allowed_endpoints': ['*']  # Todos los endpoints
            },
            'enterprise': {
                'requests_per_hour': 10000,
                'requests_per_day': 100000,
                'allowed_endpoints': ['*']  # Todos los endpoints
            }
        }
    
    def _init_auth_tables(self):
        """Inicializar tablas de autenticación"""
        with sqlite3.connect(self.db_path) as conn:
            # Tabla de API Keys
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    key_id TEXT PRIMARY KEY,
                    key_hash TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    user_email TEXT NOT NULL,
                    tier TEXT NOT NULL DEFAULT 'free',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    rate_limit_per_hour INTEGER,
                    rate_limit_per_day INTEGER,
                    allowed_endpoints TEXT,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Tabla de uso de API
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_id TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    response_time_ms REAL,
                    status_code INTEGER,
                    user_agent TEXT,
                    ip_address TEXT,
                    FOREIGN KEY (key_id) REFERENCES api_keys (key_id)
                )
            """)
            
            # Índices para optimización
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys (key_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys (is_active)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_usage_key_timestamp ON api_usage (key_id, timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage (endpoint)")
            
            conn.commit()
    
    def generate_api_key(self, name: str, user_email: str, tier: str = 'free', 
                        description: str = '') -> Tuple[str, str]:
        """
        Generar nueva API key
        Returns: (key_id, raw_key)
        """
        # Generar key_id y raw key
        key_id = f"ak_{secrets.token_hex(16)}"
        raw_key = f"sk_{secrets.token_hex(32)}"
        
        # Hash de la key para almacenamiento seguro
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Configuración del tier
        tier_config = self.TIER_LIMITS.get(tier, self.TIER_LIMITS['free'])
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO api_keys 
                (key_id, key_hash, name, description, user_email, tier, 
                 rate_limit_per_hour, rate_limit_per_day, allowed_endpoints)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                key_id, key_hash, name, description, user_email, tier,
                tier_config['requests_per_hour'], 
                tier_config['requests_per_day'],
                json.dumps(tier_config['allowed_endpoints'])
            ))
            conn.commit()
        
        logger.info(f"Nueva API key generada: {key_id} para {user_email} (tier: {tier})")
        return key_id, raw_key
    
    def validate_api_key(self, raw_key: str) -> Optional[APIKey]:
        """Validar API key y retornar información"""
        if not raw_key or not raw_key.startswith('sk_'):
            return None
        
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM api_keys 
                WHERE key_hash = ? AND is_active = 1
            """, (key_hash,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Actualizar last_used
            conn.execute("""
                UPDATE api_keys SET last_used = CURRENT_TIMESTAMP 
                WHERE key_id = ?
            """, (row['key_id'],))
            conn.commit()
            
            return APIKey(
                key_id=row['key_id'],
                key_hash=row['key_hash'],
                name=row['name'],
                description=row['description'] or '',
                user_email=row['user_email'],
                tier=row['tier'],
                created_at=datetime.fromisoformat(row['created_at']),
                last_used=datetime.fromisoformat(row['last_used']) if row['last_used'] else None,
                is_active=bool(row['is_active']),
                rate_limit_per_hour=row['rate_limit_per_hour'],
                rate_limit_per_day=row['rate_limit_per_day'],
                allowed_endpoints=json.loads(row['allowed_endpoints']),
                metadata=json.loads(row['metadata'])
            )
    
    def check_rate_limit(self, key_id: str) -> Tuple[bool, Dict]:
        """
        Verificar rate limit para una API key
        Returns: (allowed, info_dict)
        """
        with sqlite3.connect(self.db_path) as conn:
            # Obtener límites de la key
            cursor = conn.execute("""
                SELECT rate_limit_per_hour, rate_limit_per_day 
                FROM api_keys WHERE key_id = ?
            """, (key_id,))
            
            row = cursor.fetchone()
            if not row:
                return False, {'error': 'API key not found'}
            
            hour_limit, day_limit = row
            now = datetime.now()
            
            # Contar requests en la última hora
            hour_ago = now - timedelta(hours=1)
            cursor = conn.execute("""
                SELECT COUNT(*) FROM api_usage 
                WHERE key_id = ? AND timestamp >= ?
            """, (key_id, hour_ago))
            hour_count = cursor.fetchone()[0]
            
            # Contar requests en el último día
            day_ago = now - timedelta(days=1)
            cursor = conn.execute("""
                SELECT COUNT(*) FROM api_usage 
                WHERE key_id = ? AND timestamp >= ?
            """, (key_id, day_ago))
            day_count = cursor.fetchone()[0]
            
            # Verificar límites
            hour_exceeded = hour_count >= hour_limit
            day_exceeded = day_count >= day_limit
            
            return not (hour_exceeded or day_exceeded), {
                'hour_count': hour_count,
                'hour_limit': hour_limit,
                'hour_remaining': max(0, hour_limit - hour_count),
                'day_count': day_count,
                'day_limit': day_limit,
                'day_remaining': max(0, day_limit - day_count),
                'reset_time_hour': (now + timedelta(hours=1)).isoformat(),
                'reset_time_day': (now + timedelta(days=1)).isoformat()
            }
    
    def check_endpoint_permission(self, api_key: APIKey, endpoint: str) -> bool:
        """Verificar si la API key tiene permiso para el endpoint"""
        if '*' in api_key.allowed_endpoints:
            return True
        
        return endpoint in api_key.allowed_endpoints
    
    def log_api_usage(self, usage: APIUsage):
        """Registrar uso de API"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO api_usage 
                (key_id, endpoint, method, response_time_ms, status_code, user_agent, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                usage.key_id, usage.endpoint, usage.method,
                usage.response_time_ms, usage.status_code,
                usage.user_agent, usage.ip_address
            ))
            conn.commit()
    
    def get_api_key_stats(self, key_id: str, hours: int = 24) -> Dict:
        """Obtener estadísticas de uso para una API key"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            since = datetime.now() - timedelta(hours=hours)
            
            # Estadísticas generales
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_requests,
                    AVG(response_time_ms) as avg_response_time,
                    MIN(timestamp) as first_request,
                    MAX(timestamp) as last_request
                FROM api_usage 
                WHERE key_id = ? AND timestamp >= ?
            """, (key_id, since))
            
            stats = dict(cursor.fetchone())
            
            # Top endpoints
            cursor = conn.execute("""
                SELECT endpoint, COUNT(*) as count
                FROM api_usage 
                WHERE key_id = ? AND timestamp >= ?
                GROUP BY endpoint
                ORDER BY count DESC
                LIMIT 10
            """, (key_id, since))
            
            stats['top_endpoints'] = [dict(row) for row in cursor.fetchall()]
            
            # Códigos de status
            cursor = conn.execute("""
                SELECT status_code, COUNT(*) as count
                FROM api_usage 
                WHERE key_id = ? AND timestamp >= ?
                GROUP BY status_code
                ORDER BY count DESC
            """, (key_id, since))
            
            stats['status_codes'] = [dict(row) for row in cursor.fetchall()]
            
            return stats

# Instancia global del manager
api_key_manager = APIKeyManager()

def require_api_key(f):
    """Decorator para endpoints que requieren API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Obtener API key del header
        auth_header = request.headers.get('Authorization', '')
        api_key = request.headers.get('X-API-Key', '')
        
        # Soportar tanto Authorization: Bearer como X-API-Key
        if auth_header.startswith('Bearer '):
            api_key = auth_header[7:]
        
        if not api_key:
            return jsonify({
                'error': 'API key required',
                'message': 'Include API key in Authorization header or X-API-Key header'
            }), 401
        
        # Validar API key
        key_info = api_key_manager.validate_api_key(api_key)
        if not key_info:
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is invalid or inactive'
            }), 401
        
        # Verificar permisos de endpoint
        if not api_key_manager.check_endpoint_permission(key_info, request.endpoint):
            return jsonify({
                'error': 'Endpoint not allowed',
                'message': f'Your API key tier ({key_info.tier}) does not have access to this endpoint'
            }), 403
        
        # Verificar rate limit
        allowed, rate_info = api_key_manager.check_rate_limit(key_info.key_id)
        if not allowed:
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': 'You have exceeded your rate limit',
                'rate_limit': rate_info
            }), 429
        
        # Almacenar info en g para uso en la función
        g.api_key = key_info
        g.rate_limit_info = rate_info
        
        # Registrar inicio de request
        g.request_start_time = time.time()
        
        # Ejecutar función
        response = f(*args, **kwargs)
        
        # Registrar uso de API
        response_time = (time.time() - g.request_start_time) * 1000
        status_code = response[1] if isinstance(response, tuple) else 200
        
        usage = APIUsage(
            key_id=key_info.key_id,
            endpoint=request.endpoint or request.path,
            method=request.method,
            timestamp=datetime.now(),
            response_time_ms=response_time,
            status_code=status_code,
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr
        )
        
        api_key_manager.log_api_usage(usage)
        
        # Agregar headers de rate limit a la respuesta
        if isinstance(response, tuple):
            response_data, status_code = response
            headers = {
                'X-RateLimit-Limit-Hour': str(rate_info['hour_limit']),
                'X-RateLimit-Remaining-Hour': str(rate_info['hour_remaining']),
                'X-RateLimit-Limit-Day': str(rate_info['day_limit']),
                'X-RateLimit-Remaining-Day': str(rate_info['day_remaining']),
                'X-RateLimit-Reset-Hour': rate_info['reset_time_hour'],
                'X-RateLimit-Reset-Day': rate_info['reset_time_day']
            }
            return response_data, status_code, headers
        else:
            # Para respuestas simples
            return response
        
    return decorated_function

def optional_api_key(f):
    """Decorator para endpoints que opcionalmente aceptan API key (para analytics)"""
    @wraps(f)
    def optional_decorated_function(*args, **kwargs):
        # Intentar obtener API key
        auth_header = request.headers.get('Authorization', '')
        api_key = request.headers.get('X-API-Key', '')
        
        if auth_header.startswith('Bearer '):
            api_key = auth_header[7:]
        
        g.api_key = None
        g.rate_limit_info = None
        
        if api_key:
            key_info = api_key_manager.validate_api_key(api_key)
            if key_info:
                g.api_key = key_info
                allowed, rate_info = api_key_manager.check_rate_limit(key_info.key_id)
                g.rate_limit_info = rate_info
        
        return f(*args, **kwargs)
    
    return optional_decorated_function
