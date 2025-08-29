"""
Gestores de errores centralizados para la aplicación
"""
import logging
from functools import wraps
from flask import jsonify
from typing import Any, Dict, Optional
import traceback

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Excepción personalizada para errores de API"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

def handle_api_error(error: APIError):
    """Manejador para errores de API personalizados"""
    logger.error(f"API Error: {error.message} - Details: {error.details}")
    
    return jsonify({
        'error': error.message,
        'status_code': error.status_code,
        'details': error.details,
        'timestamp': logger.timestamp()
    }), error.status_code

def handle_validation_error(error):
    """Manejador para errores de validación"""
    logger.warning(f"Validation Error: {str(error)}")
    
    return jsonify({
        'error': 'Error de validación',
        'message': str(error),
        'status_code': 400
    }), 400

def handle_database_error(error):
    """Manejador para errores de base de datos"""
    logger.error(f"Database Error: {str(error)}")
    logger.error(traceback.format_exc())
    
    return jsonify({
        'error': 'Error interno de base de datos',
        'message': 'Ocurrió un error al acceder a los datos',
        'status_code': 500
    }), 500

def handle_generic_error(error):
    """Manejador genérico para errores no capturados"""
    logger.error(f"Unhandled Error: {str(error)}")
    logger.error(traceback.format_exc())
    
    return jsonify({
        'error': 'Error interno del servidor',
        'message': 'Ocurrió un error inesperado',
        'status_code': 500
    }), 500

def safe_api_call(default_response=None):
    """
    Decorador para manejar errores en endpoints de API de forma segura
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except APIError as e:
                return handle_api_error(e)
            except ValueError as e:
                return handle_validation_error(e)
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                logger.error(traceback.format_exc())
                
                if default_response:
                    return jsonify(default_response), 200
                
                return handle_generic_error(e)
        return wrapper
    return decorator

def safe_database_operation(default_value=None):
    """
    Decorador para operaciones de base de datos seguras
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Database operation failed in {func.__name__}: {str(e)}")
                logger.error(traceback.format_exc())
                return default_value
        return wrapper
    return decorator

def validate_params(required_params):
    """
    Decorador para validar parámetros requeridos
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request
            
            # Validar parámetros requeridos
            missing_params = []
            for param in required_params:
                if param not in request.args and param not in request.json:
                    missing_params.append(param)
            
            if missing_params:
                raise APIError(
                    f"Parámetros requeridos faltantes: {', '.join(missing_params)}",
                    status_code=400,
                    details={'missing_params': missing_params}
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
