#!/usr/bin/env python3
"""
Script para iniciar el servidor de la API
"""

import os
import sys
from pathlib import Path

# Obtener directorio del backend de forma dinámica
backend_dir = Path(__file__).parent.absolute()
os.chdir(backend_dir)

# Agregar al path para importar módulos
sys.path.append(str(backend_dir))

# Importar y ejecutar la aplicación
if __name__ == "__main__":
    from app import socketio, app
    
    print("🚀 Iniciando servidor de la API en puerto 5001...")
    print("📡 WebSockets habilitados")
    print("🔄 Modo debug activado")
    print("=" * 50)
    
    # Ejecutar servidor con SocketIO
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=5001, 
        debug=False,  # Cambiar a False para evitar reinicios
        allow_unsafe_werkzeug=True
    )
