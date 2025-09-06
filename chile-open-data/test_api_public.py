#!/usr/bin/env python3
"""
Script de prueba para la API Pública de Chile Open Data - Fase 4
Prueba la funcionalidad de autenticación, rate limiting y endpoints
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5001"
API_BASE_URL = f"{BASE_URL}/api/v1"
DEVELOPER_URL = f"{BASE_URL}/developer"

def print_header(title):
    """Imprimir header decorativo"""
    print("\n" + "="*60)
    print(f"🔥 {title}")
    print("="*60)

def print_step(step):
    """Imprimir paso"""
    print(f"\n📋 {step}")
    print("-" * 40)

def test_api_key_generation():
    """Probar generación de API key"""
    print_step("1. Generando API Key de prueba")
    
    # Datos para generar API key
    key_data = {
        "name": "Prueba API Fase 4",
        "user_email": "desarrollador@test.cl",
        "tier": "pro",
        "description": "API key de prueba para validar Fase 4"
    }
    
    try:
        response = requests.post(f"{DEVELOPER_URL}/api/generate-key", json=key_data)
        
        if response.status_code == 200:
            result = response.json()
            api_key = result.get('api_key')
            key_id = result.get('key_id')
            tier = result.get('tier')
            
            print(f"✅ API Key generada exitosamente!")
            print(f"   🔑 Key ID: {key_id}")
            print(f"   🎯 Tier: {tier}")
            print(f"   🔐 API Key: {api_key[:10]}...{api_key[-10:]}")
            
            return api_key
        else:
            print(f"❌ Error generando API key: {response.status_code}")
            print(f"   📄 Respuesta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def test_authenticated_endpoints(api_key):
    """Probar endpoints que requieren autenticación"""
    print_step("2. Probando endpoints autenticados")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Lista de endpoints a probar
    endpoints_to_test = [
        ("GET", "/datasets", "Listar todos los datasets"),
        ("GET", "/analytics/export?format=json&hours=24", "Exportar analytics JSON"),
        ("GET", "/usage/stats", "Estadísticas de uso de API key"),
    ]
    
    results = []
    
    for method, endpoint, description in endpoints_to_test:
        try:
            print(f"\n🔍 Probando: {description}")
            print(f"   📡 {method} {API_BASE_URL}{endpoint}")
            
            if method == "GET":
                response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers)
            elif method == "POST":
                response = requests.post(f"{API_BASE_URL}{endpoint}", headers=headers, json={})
            
            print(f"   📊 Status: {response.status_code}")
            
            # Verificar headers de rate limiting
            rate_headers = {}
            for header_name in response.headers:
                if header_name.startswith('X-RateLimit'):
                    rate_headers[header_name] = response.headers[header_name]
            
            if rate_headers:
                print(f"   🛡️ Rate Limit Headers:")
                for header, value in rate_headers.items():
                    print(f"      {header}: {value}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"   ✅ Respuesta exitosa")
                    
                    # Mostrar información específica según el endpoint
                    if 'datasets' in endpoint:
                        total = data.get('total', 0)
                        print(f"      📊 Total datasets: {total}")
                        api_info = data.get('api_info', {})
                        if api_info:
                            print(f"      👤 Usuario: {api_info.get('user', 'N/A')}")
                            print(f"      🎯 Tier: {api_info.get('tier', 'N/A')}")
                    
                    elif 'usage' in endpoint:
                        stats = data.get('usage_stats', {})
                        limits = data.get('current_limits', {})
                        print(f"      📈 Requests totales: {stats.get('total_requests', 0)}")
                        print(f"      ⏱️ Tiempo respuesta promedio: {stats.get('avg_response_time', 0):.2f}ms")
                        print(f"      🔄 Remaining hora: {limits.get('hour_remaining', 0)}")
                        print(f"      🔄 Remaining día: {limits.get('day_remaining', 0)}")
                    
                    results.append((endpoint, True, response.status_code))
                else:
                    print(f"   ❌ Error en respuesta: {data.get('error', 'Unknown')}")
                    results.append((endpoint, False, response.status_code))
            else:
                print(f"   ❌ Error HTTP: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"      📄 Error: {error_data.get('error', 'Unknown')}")
                except:
                    print(f"      📄 Respuesta: {response.text[:100]}")
                results.append((endpoint, False, response.status_code))
                
        except Exception as e:
            print(f"   ❌ Error de conexión: {e}")
            results.append((endpoint, False, 0))
    
    return results

def test_rate_limiting(api_key):
    """Probar rate limiting"""
    print_step("3. Probando Rate Limiting")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print("🚀 Enviando múltiples requests para probar rate limiting...")
    
    # Hacer varias requests rápidas
    for i in range(10):
        try:
            response = requests.get(f"{API_BASE_URL}/datasets", headers=headers)
            
            # Obtener headers de rate limit
            hour_remaining = response.headers.get('X-RateLimit-Remaining-Hour', 'N/A')
            day_remaining = response.headers.get('X-RateLimit-Remaining-Day', 'N/A')
            
            print(f"   Request {i+1:2d}: Status {response.status_code} | "
                  f"Hour remaining: {hour_remaining:>4} | Day remaining: {day_remaining:>4}")
            
            if response.status_code == 429:
                print("   🛑 Rate limit alcanzado (esperado)")
                error_data = response.json()
                print(f"      📄 Mensaje: {error_data.get('message', 'N/A')}")
                break
                
            time.sleep(0.1)  # Pequeña pausa entre requests
            
        except Exception as e:
            print(f"   ❌ Error en request {i+1}: {e}")
            break

def test_custom_report_generation(api_key):
    """Probar generación de reportes personalizados"""
    print_step("4. Probando generación de reportes personalizados")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Configuración del reporte personalizado
    report_config = {
        "hours": 48,
        "include_datasets": True,
        "include_analytics": True,
        "include_categories": True,
        "categories": ["economía", "salud", "educación"]
    }
    
    try:
        print(f"📊 Generando reporte personalizado...")
        print(f"   ⏰ Período: {report_config['hours']} horas")
        print(f"   📋 Categorías: {', '.join(report_config['categories'])}")
        
        response = requests.post(f"{API_BASE_URL}/reports/custom", 
                               headers=headers, json=report_config)
        
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                report = data.get('report', {})
                report_info = report.get('report_info', {})
                
                print("   ✅ Reporte generado exitosamente!")
                print(f"      🕐 Generado: {report_info.get('generated_at', 'N/A')}")
                print(f"      👤 Solicitado por: {report_info.get('requested_by', 'N/A')}")
                print(f"      🎯 Tier: {report_info.get('api_tier', 'N/A')}")
                
                # Mostrar contenido del reporte
                if 'system_metrics' in report:
                    metrics = report['system_metrics']
                    print(f"      📈 Métricas del sistema incluidas: {len(metrics)} items")
                
                if 'category_analytics' in report:
                    categories = report['category_analytics']
                    print(f"      📊 Analytics por categoría: {len(categories)} categorías")
                
                if 'dataset_status' in report:
                    datasets = report['dataset_status']
                    print(f"      📋 Estados de datasets: {len(datasets)} datasets")
                
            else:
                print(f"   ❌ Error en reporte: {data.get('error', 'Unknown')}")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
            try:
                error_data = response.json()
                print(f"      📄 Error: {error_data.get('error', 'Unknown')}")
            except:
                print(f"      📄 Respuesta: {response.text[:100]}")
                
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")

def test_csv_export(api_key):
    """Probar exportación CSV"""
    print_step("5. Probando exportación CSV")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        print("📊 Exportando datos en formato CSV...")
        
        response = requests.get(f"{API_BASE_URL}/analytics/export?format=csv&hours=24", 
                              headers=headers)
        
        print(f"   📊 Status: {response.status_code}")
        print(f"   📄 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'text/csv' in content_type:
                csv_content = response.text
                lines = csv_content.split('\n')
                
                print("   ✅ CSV exportado exitosamente!")
                print(f"      📏 Líneas totales: {len(lines)}")
                print(f"      📋 Headers: {lines[0] if lines else 'N/A'}")
                print("      📄 Primeras 3 líneas de datos:")
                for i, line in enumerate(lines[1:4]):
                    if line.strip():
                        print(f"         {i+1}: {line[:80]}...")
            else:
                print(f"   ⚠️ Tipo de contenido inesperado: {content_type}")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")

def test_unauthorized_access():
    """Probar acceso sin autenticación"""
    print_step("6. Probando acceso sin autenticación (debe fallar)")
    
    # Probar sin headers
    try:
        response = requests.get(f"{API_BASE_URL}/datasets")
        print(f"   📊 Sin headers - Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Correctamente rechazado (401 Unauthorized)")
        else:
            print("   ❌ Debería rechazar con 401")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Probar con API key inválida
    try:
        headers = {"Authorization": "Bearer sk_invalid_key_12345"}
        response = requests.get(f"{API_BASE_URL}/datasets", headers=headers)
        print(f"   📊 Key inválida - Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Correctamente rechazado (401 Unauthorized)")
        else:
            print("   ❌ Debería rechazar con 401")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    """Ejecutar todas las pruebas"""
    print_header("PRUEBAS DE API PÚBLICA - FASE 4")
    print("🔥 Sistema de Autenticación y Rate Limiting")
    print(f"📡 Base URL: {BASE_URL}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    
    # Verificar que el servidor esté funcionando
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor funcionando correctamente")
        else:
            print(f"❌ Servidor respondió con status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        return False
    
    # 1. Generar API key de prueba
    api_key = test_api_key_generation()
    if not api_key:
        print("❌ No se pudo generar API key. Abortando pruebas.")
        return False
    
    # 2. Probar endpoints autenticados
    endpoint_results = test_authenticated_endpoints(api_key)
    
    # 3. Probar rate limiting
    test_rate_limiting(api_key)
    
    # 4. Probar reportes personalizados
    test_custom_report_generation(api_key)
    
    # 5. Probar exportación CSV
    test_csv_export(api_key)
    
    # 6. Probar acceso no autorizado
    test_unauthorized_access()
    
    # Resumen final
    print_header("RESUMEN DE PRUEBAS")
    
    successful_endpoints = sum(1 for _, success, _ in endpoint_results if success)
    total_endpoints = len(endpoint_results)
    
    print(f"📊 Endpoints probados: {total_endpoints}")
    print(f"✅ Exitosos: {successful_endpoints}")
    print(f"❌ Fallidos: {total_endpoints - successful_endpoints}")
    
    if successful_endpoints == total_endpoints:
        print("\n🎉 ¡TODAS LAS PRUEBAS EXITOSAS!")
        print("✨ API Pública Fase 4 implementada correctamente")
    else:
        print(f"\n⚠️ {total_endpoints - successful_endpoints} pruebas fallaron")
        print("🔧 Revisar logs para más detalles")
    
    print(f"\n🔑 API Key de prueba generada: {api_key[:10]}...{api_key[-10:]}")
    print("💡 Puedes usar esta key para pruebas adicionales")
    
    return successful_endpoints == total_endpoints

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
