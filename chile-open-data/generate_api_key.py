#!/usr/bin/env python3
"""
Script para generar API key directamente en la base de datos
Para pruebas de la Fase 4
"""

import sys
import os
sys.path.append('/Users/estebanroman/Documents/GitHub/_data_libero_CHILE/chile-open-data/web_app/backend')

from auth import api_key_manager

def main():
    print("🔑 Generando API Key de prueba para Fase 4...")
    
    # Generar API key de prueba
    key_id, raw_key = api_key_manager.generate_api_key(
        name="Prueba Fase 4",
        user_email="test@chile-open-data.cl",
        tier="pro",
        description="API key de prueba para validar funcionalidades de Fase 4"
    )
    
    print(f"\n✅ API Key generada exitosamente!")
    print(f"🆔 Key ID: {key_id}")
    print(f"🔐 API Key: {raw_key}")
    print(f"🎯 Tier: pro")
    print(f"📊 Límites:")
    print(f"   - Por hora: 1,000 requests")
    print(f"   - Por día: 10,000 requests")
    
    print(f"\n💡 Para usar esta API key, incluye este header en tus requests:")
    print(f"   Authorization: Bearer {raw_key}")
    print(f"\n🌐 O usa este header alternativo:")
    print(f"   X-API-Key: {raw_key}")
    
    print(f"\n🔍 Puedes probar con:")
    print(f"   curl -H 'Authorization: Bearer {raw_key}' http://localhost:5001/health")
    
    return raw_key

if __name__ == "__main__":
    api_key = main()
