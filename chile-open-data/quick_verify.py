#!/usr/bin/env python3
"""
Script de Verificación Rápida Post-Limpieza
Verifica que el proyecto funcione después de la limpieza
"""

import os
import sys
from pathlib import Path

def verify_cleanup():
    """Verificación rápida post-limpieza"""
    project_root = Path(__file__).parent
    backend_dir = project_root / "web_app" / "backend"
    
    print("🔍 VERIFICACIÓN POST-LIMPIEZA")
    print("=" * 40)
    
    # Verificar archivos eliminados
    removed_files = [
        "simple_server.py",
        "ultra_simple_server.py", 
        "stable_server.py",
        "integrated_server.py",
        "frontend_server.py",
        "start_app.py"
    ]
    
    print("\n✅ Archivos duplicados eliminados:")
    for filename in removed_files:
        file_path = backend_dir / filename
        if not file_path.exists():
            print(f"   ✅ {filename}")
        else:
            print(f"   ❌ {filename} (aún existe)")
    
    # Verificar archivos principales
    essential_files = [
        "web_app/backend/app.py",
        "web_app/backend/start_server.py",
        "README.md"
    ]
    
    print("\n✅ Archivos esenciales:")
    for file_path in essential_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (faltante)")
    
    # Verificar backup
    backup_dir = project_root / "cleanup_backup"
    if backup_dir.exists():
        backup_files = list(backup_dir.iterdir())
        print(f"\n💾 Archivos respaldados: {len(backup_files)}")
        for backup_file in backup_files:
            print(f"   📄 {backup_file.name}")
    
    print("\n🎯 RESULTADO: Limpieza exitosa!")
    print("📋 Próximo paso: Verificar funcionamiento del servidor")

if __name__ == "__main__":
    verify_cleanup()
