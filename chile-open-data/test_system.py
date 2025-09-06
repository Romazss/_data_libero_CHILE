#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de Chile Open Data
Verifica que todos los componentes estén funcionando correctamente
"""

import sys
import os
import requests
import time
import json
from datetime import datetime
from pathlib import Path

# Obtener directorios de forma dinámica
project_root = Path(__file__).parent.absolute()
backend_dir = project_root / "web_app" / "backend"
sys.path.append(str(backend_dir))

def test_imports():
    """Verificar que todas las importaciones funcionen"""
    print("🔍 Verificando importaciones...")
    try:
        # Cambiar al directorio correcto
        os.chdir(str(backend_dir))
        
        # Importar módulos principales
        from services.sources import load_sources
        from services.checker import check_all
        from models import Database
        from cache import cache
        from scheduler import init_scheduler
        from notifications import notification_manager
        from analytics import AnalyticsEngine
        from reports import ReportGenerator
        
        print("✅ Todas las importaciones exitosas")
        return True
    except Exception as e:
        print(f"❌ Error en importaciones: {e}")
        return False

def test_database():
    """Verificar que la base de datos funcione"""
    print("🗄️ Verificando base de datos...")
    try:
        from models import Database
        db = Database('data/test_chile_data.db')
        
        # Verificar tablas
        tables = ['datasets', 'dataset_status', 'analytics_data', 'notifications']
        for table in tables:
            result = db.execute(f"SELECT COUNT(*) FROM {table}")
            count = result.fetchone()[0] if result else 0
            print(f"  📊 Tabla {table}: {count} registros")
        
        print("✅ Base de datos funcionando correctamente")
        return True
    except Exception as e:
        print(f"❌ Error en base de datos: {e}")
        return False

def test_sources_config():
    """Verificar configuración de fuentes"""
    print("📋 Verificando configuración de fuentes...")
    try:
        from services.sources import load_sources
        sources = load_sources()
        print(f"✅ Cargadas {len(sources)} fuentes de datos:")
        for source in sources:
            print(f"  📄 {source.get('name', 'Sin nombre')} ({source.get('category', 'Sin categoría')})")
        return True
    except Exception as e:
        print(f"❌ Error cargando fuentes: {e}")
        return False

def test_scraper_pipeline():
    """Verificar pipeline del scraper"""
    print("🔧 Verificando pipeline del scraper...")
    try:
        # Verificar archivos del scraper
        scraper_files = [
            'base.py', 'schema.py', 'fetch.py', 'diff.py', 'emit.py'
        ]
        
        base_path = '/Users/estebanroman/Documents/GitHub/_data_libero_CHILE/chile-open-data/data_sources/scripts/scraper'
        
        for file in scraper_files:
            file_path = os.path.join(base_path, file)
            if os.path.exists(file_path):
                print(f"  ✅ {file} encontrado")
            else:
                print(f"  ❌ {file} faltante")
                return False
        
        # Verificar extractors
        extractors_path = os.path.join(base_path, 'extractors')
        if os.path.exists(extractors_path):
            extractors = os.listdir(extractors_path)
            print(f"  📁 Extractors disponibles: {len(extractors)} archivos")
            for extractor in extractors:
                if extractor.endswith('.py'):
                    print(f"    📄 {extractor}")
        
        print("✅ Pipeline del scraper verificado")
        return True
    except Exception as e:
        print(f"❌ Error verificando scraper: {e}")
        return False

def test_server_components():
    """Verificar componentes del servidor sin iniciar Flask"""
    print("🖥️ Verificando componentes del servidor...")
    try:
        # Test analytics engine
        from analytics import AnalyticsEngine
        analytics = AnalyticsEngine()
        print("  ✅ AnalyticsEngine inicializado")
        
        # Test cache
        from cache import cache
        cache.set('test_key', 'test_value', timeout=60)
        value = cache.get('test_key')
        if value == 'test_value':
            print("  ✅ Cache funcionando")
        else:
            print("  ⚠️ Cache no retorna valores correctos")
        
        # Test notification manager
        from notifications import notification_manager
        print("  ✅ NotificationManager inicializado")
        
        print("✅ Componentes del servidor verificados")
        return True
    except Exception as e:
        print(f"❌ Error en componentes: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 INICIANDO VERIFICACIÓN DEL SISTEMA CHILE OPEN DATA")
    print("=" * 60)
    
    tests = [
        ("Importaciones", test_imports),
        ("Base de Datos", test_database),
        ("Configuración de Fuentes", test_sources_config),
        ("Pipeline del Scraper", test_scraper_pipeline),
        ("Componentes del Servidor", test_server_components),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 EJECUTANDO: {test_name}")
        print("-" * 40)
        success = test_func()
        results.append((test_name, success))
        print("")
    
    # Resumen final
    print("🏁 RESUMEN DE VERIFICACIÓN")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n📊 RESULTADO FINAL: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("🎉 ¡SISTEMA COMPLETAMENTE FUNCIONAL!")
        print("✨ Listo para continuar con la Fase 4")
    else:
        print("⚠️ Hay problemas que necesitan ser resueltos")
        print("🔧 Revisa los errores anteriores")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
