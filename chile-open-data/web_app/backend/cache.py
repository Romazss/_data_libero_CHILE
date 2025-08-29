# /web_app/backend/cache.py
"""
Sistema de cache para la Biblioteca de Datos Abiertos de Chile
"""

import json
import time
from typing import Any, Optional, Dict
from functools import wraps
import hashlib


class SimpleCache:
    """Cache en memoria simple con TTL"""
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._default_ttl = 300  # 5 minutos por defecto
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Genera una clave única para los argumentos"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del cache"""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() < entry['expires_at']:
                return entry['value']
            else:
                # Expirado, eliminar
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Guarda un valor en el cache"""
        ttl = ttl or self._default_ttl
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
    
    def delete(self, key: str) -> None:
        """Elimina una clave del cache"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Limpia todo el cache"""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Limpia entradas expiradas y retorna cantidad eliminada"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time >= entry['expires_at']
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        # Limpieza automática si el cache está muy grande
        if len(self._cache) > 1000:  # Límite de seguridad
            # Ordenar por timestamp y mantener solo los 500 más recientes
            sorted_items = sorted(
                self._cache.items(), 
                key=lambda x: x[1]['created_at'], 
                reverse=True
            )
            self._cache = dict(sorted_items[:500])
        
        return len(expired_keys)
    
    def stats(self) -> Dict:
        """Estadísticas del cache"""
        current_time = time.time()
        valid_entries = sum(
            1 for entry in self._cache.values()
            if current_time < entry['expires_at']
        )
        expired_entries = len(self._cache) - valid_entries
        
        return {
            'total_entries': len(self._cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_size_mb': len(json.dumps(self._cache, default=str)) / 1024 / 1024
        }


# Instancia global del cache
cache = SimpleCache()


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorador para cachear resultados de funciones
    
    Args:
        ttl: Tiempo de vida en segundos
        key_prefix: Prefijo para la clave del cache
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave única
            cache_key = f"{key_prefix}:{func.__name__}:{cache._generate_key(*args, **kwargs)}"
            
            # Intentar obtener del cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # No está en cache, ejecutar función
            result = func(*args, **kwargs)
            
            # Guardar en cache
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def cache_key_for_datasets():
    """Genera clave de cache específica para datasets"""
    return f"datasets:{int(time.time() // 60)}"  # Cambia cada minuto


def invalidate_datasets_cache():
    """Invalida el cache relacionado con datasets"""
    # Buscar y eliminar todas las claves que empiecen con 'datasets:'
    keys_to_delete = [key for key in cache._cache.keys() if key.startswith('datasets:')]
    for key in keys_to_delete:
        cache.delete(key)
