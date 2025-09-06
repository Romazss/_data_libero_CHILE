#!/usr/bin/env python3
"""
Script de Limpieza Automatizada - Chile Open Data
Implementa las recomendaciones de la auditoría del proyecto

Ejecutar con: python3 cleanup_project.py
"""

import os
import shutil
import sys
from pathlib import Path

class ProjectCleanup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "web_app" / "backend"
        self.changes_made = []
        self.errors = []
        
    def log_change(self, action, description):
        """Registrar cambio realizado"""
        self.changes_made.append(f"{action}: {description}")
        print(f"✅ {action}: {description}")
        
    def log_error(self, error_msg):
        """Registrar error"""
        self.errors.append(error_msg)
        print(f"❌ ERROR: {error_msg}")
        
    def backup_file(self, file_path):
        """Crear backup de archivo antes de eliminarlo"""
        backup_dir = self.project_root / "cleanup_backup"
        backup_dir.mkdir(exist_ok=True)
        
        file_path = Path(file_path)
        if file_path.exists():
            backup_path = backup_dir / file_path.name
            shutil.copy2(file_path, backup_path)
            return backup_path
        return None
        
    def remove_duplicate_servers(self):
        """Eliminar servidores duplicados"""
        print("\n🔥 FASE 1: Eliminando servidores duplicados...")
        
        # Lista de archivos a eliminar
        files_to_remove = [
            "simple_server.py",
            "ultra_simple_server.py", 
            "stable_server.py",
            "integrated_server.py",
            "frontend_server.py",
            "start_app.py"
        ]
        
        for filename in files_to_remove:
            file_path = self.backend_dir / filename
            if file_path.exists():
                # Crear backup
                backup_path = self.backup_file(file_path)
                # Eliminar archivo
                file_path.unlink()
                self.log_change("ELIMINADO", f"{filename} (backup en {backup_path.name})")
            else:
                print(f"⚠️  {filename} no encontrado")
                
    def consolidate_test_files(self):
        """Consolidar archivos de prueba duplicados"""
        print("\n🧪 FASE 2: Consolidando archivos de prueba...")
        
        backend_test = self.backend_dir / "test_system.py"
        root_test = self.project_root / "test_system.py"
        
        if backend_test.exists() and root_test.exists():
            # Renombrar el del backend para evitar conflictos
            new_name = self.project_root / "test_system_backend.py"
            backup_path = self.backup_file(backend_test)
            backend_test.rename(new_name)
            self.log_change("CONSOLIDADO", f"test_system.py del backend → test_system_backend.py")
            
    def clean_documentation(self):
        """Limpiar documentación duplicada"""
        print("\n📚 FASE 3: Limpiando documentación...")
        
        readme_old = self.project_root / "README_1.md"
        if readme_old.exists():
            # Verificar si README_1.md tiene contenido único
            with open(readme_old, 'r', encoding='utf-8') as f:
                old_content = f.read()
                
            # Si es muy corto o parece obsoleto, crear backup y eliminar
            if len(old_content) < 1000:  # Umbral arbitrario
                backup_path = self.backup_file(readme_old)
                readme_old.unlink()
                self.log_change("ELIMINADO", f"README_1.md (backup en {backup_path.name})")
            else:
                self.log_change("MANTENIDO", "README_1.md contiene información única")
                
    def clean_empty_directories(self):
        """Limpiar directorios vacíos o con solo .gitkeep"""
        print("\n📁 FASE 4: Limpiando directorios vacíos...")
        
        # Verificar libraries
        libs_dir = self.project_root / "libraries"
        if libs_dir.exists():
            python_pkg = libs_dir / "python_package"
            r_pkg = libs_dir / "r_package"
            
            # Verificar si solo contienen .gitkeep
            for pkg_dir in [python_pkg, r_pkg]:
                if pkg_dir.exists():
                    contents = list(pkg_dir.iterdir())
                    if len(contents) <= 1 and (len(contents) == 0 or contents[0].name == '.gitkeep'):
                        self.log_change("MARCADO", f"{pkg_dir.name} está vacío (solo .gitkeep)")
                        
        # Verificar backend/reports
        reports_dir = self.backend_dir / "reports"
        if reports_dir.exists():
            contents = list(reports_dir.iterdir())
            if len(contents) == 0:
                self.log_change("MARCADO", "backend/reports está vacío")
                
    def identify_hardcoded_paths(self):
        """Identificar rutas hardcodeadas"""
        print("\n🔍 FASE 5: Identificando rutas hardcodeadas...")
        
        files_to_check = [
            self.backend_dir / "start_server.py",
            self.project_root / "test_system.py", 
            self.project_root / "Makefile"
        ]
        
        hardcoded_pattern = "/Users/estebanroman/Documents/GitHub/_data_libero_CHILE"
        
        for file_path in files_to_check:
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if hardcoded_pattern in content:
                            self.log_change("ENCONTRADO", f"Ruta hardcodeada en {file_path.name}")
                except Exception as e:
                    self.log_error(f"No se pudo leer {file_path.name}: {e}")
                    
    def create_cleanup_report(self):
        """Crear reporte de limpieza"""
        report_path = self.project_root / "CLEANUP_REPORT.md"
        
        report_content = f"""# 🧹 REPORTE DE LIMPIEZA DEL PROYECTO

**Fecha:** {os.popen('date').read().strip()}
**Script:** cleanup_project.py

## ✅ Cambios Realizados

"""
        
        for change in self.changes_made:
            report_content += f"- {change}\n"
            
        if self.errors:
            report_content += "\n## ❌ Errores Encontrados\n\n"
            for error in self.errors:
                report_content += f"- {error}\n"
                
        report_content += f"""
## 📊 Resumen

- **Cambios totales:** {len(self.changes_made)}
- **Errores:** {len(self.errors)}
- **Archivos respaldados:** backup en carpeta `cleanup_backup/`

## 🔧 Próximos Pasos Manuales

1. **Revisar rutas hardcodeadas identificadas**
2. **Crear archivo .env para configuración**
3. **Implementar libraries/ o documentar como futuras**
4. **Verificar que el sistema funciona después de la limpieza**

## 🚀 Verificación Post-Limpieza

```bash
# Verificar que el servidor principal funciona
cd web_app/backend
python3 start_server.py

# Ejecutar pruebas
python3 ../../test_system.py
```
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
        self.log_change("CREADO", f"Reporte de limpieza en {report_path.name}")
        
    def run_cleanup(self):
        """Ejecutar proceso completo de limpieza"""
        print("🚀 Iniciando limpieza automatizada del proyecto...")
        print("=" * 60)
        
        try:
            # Ejecutar fases de limpieza
            self.remove_duplicate_servers()
            self.consolidate_test_files() 
            self.clean_documentation()
            self.clean_empty_directories()
            self.identify_hardcoded_paths()
            
            # Crear reporte
            self.create_cleanup_report()
            
            print("\n" + "=" * 60)
            print("✅ LIMPIEZA COMPLETADA")
            print(f"📊 Total de cambios: {len(self.changes_made)}")
            print(f"❌ Errores: {len(self.errors)}")
            print("📄 Reporte detallado: CLEANUP_REPORT.md")
            print("💾 Archivos respaldados en: cleanup_backup/")
            
            if self.errors:
                print("\n⚠️  Revisar errores en el reporte")
                return False
            return True
            
        except Exception as e:
            self.log_error(f"Error crítico durante limpieza: {e}")
            return False

def main():
    """Función principal"""
    print("🔍 AUDITORÍA Y LIMPIEZA - Chile Open Data")
    print("¿Deseas proceder con la limpieza automatizada? (y/N): ", end="")
    
    response = input().strip().lower()
    if response not in ['y', 'yes', 'sí', 'si']:
        print("❌ Limpieza cancelada")
        return
        
    cleanup = ProjectCleanup()
    success = cleanup.run_cleanup()
    
    if success:
        print("\n🎉 ¡Proyecto limpiado exitosamente!")
        print("💡 Revisa CLEANUP_REPORT.md para próximos pasos")
    else:
        print("\n⚠️  Limpieza completada con errores")
        print("🔍 Revisa CLEANUP_REPORT.md para detalles")

if __name__ == "__main__":
    main()
