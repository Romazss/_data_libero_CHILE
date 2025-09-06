#!/usr/bin/env python3
"""
Script de Verificación Post-Auditoría
Verifica que el proyecto funcione correctamente después de la limpieza

Ejecutar con: python3 verify_project.py
"""

import os
import sys
import subprocess
import time
import requests
import json
from pathlib import Path

class ProjectVerifier:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "web_app" / "backend"
        self.results = []
        self.server_process = None
        
    def log_result(self, test_name, status, message=""):
        """Registrar resultado de prueba"""
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        self.results.append({
            "test": test_name,
            "status": status,
            "message": message
        })
        print(f"{icon} {test_name}: {message}")
        
    def check_file_structure(self):
        """Verificar estructura de archivos esenciales"""
        print("\n📁 Verificando estructura de archivos...")
        
        essential_files = [
            ("app.py", self.backend_dir / "app.py"),
            ("start_server.py", self.backend_dir / "start_server.py"),
            ("models.py", self.backend_dir / "models.py"),
            ("requirements.txt", self.backend_dir / "requirements.txt"),
            ("README.md", self.project_root / "README.md"),
            ("Makefile", self.project_root / "Makefile")
        ]
        
        for name, path in essential_files:
            if path.exists():
                self.log_result(f"Archivo {name}", "PASS", "Existe")
            else:
                self.log_result(f"Archivo {name}", "FAIL", "No encontrado")
                
    def check_removed_duplicates(self):
        """Verificar que los archivos duplicados fueron eliminados"""
        print("\n🗑️  Verificando eliminación de duplicados...")
        
        should_be_removed = [
            "simple_server.py",
            "ultra_simple_server.py",
            "stable_server.py", 
            "integrated_server.py",
            "frontend_server.py"
        ]
        
        for filename in should_be_removed:
            file_path = self.backend_dir / filename
            if not file_path.exists():
                self.log_result(f"Eliminación {filename}", "PASS", "Archivo eliminado correctamente")
            else:
                self.log_result(f"Eliminación {filename}", "FAIL", "Archivo aún existe")
                
    def check_imports(self):
        """Verificar que las importaciones funcionen"""
        print("\n📦 Verificando importaciones...")
        
        # Cambiar al directorio del backend
        original_dir = os.getcwd()
        os.chdir(self.backend_dir)
        sys.path.insert(0, str(self.backend_dir))
        
        modules_to_test = [
            "models",
            "cache", 
            "services.sources",
            "services.checker",
            "analytics",
            "auth",
            "websockets"
        ]
        
        for module in modules_to_test:
            try:
                __import__(module)
                self.log_result(f"Import {module}", "PASS", "Importación exitosa")
            except ImportError as e:
                self.log_result(f"Import {module}", "FAIL", f"Error: {e}")
            except Exception as e:
                self.log_result(f"Import {module}", "WARN", f"Advertencia: {e}")
                
        # Restaurar directorio
        os.chdir(original_dir)
        
    def start_test_server(self):
        """Iniciar servidor para pruebas"""
        print("\n🚀 Iniciando servidor de prueba...")
        
        try:
            # Cambiar al directorio del backend
            os.chdir(self.backend_dir)
            
            # Iniciar servidor en background
            self.server_process = subprocess.Popen(
                [sys.executable, "start_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Esperar un momento para que inicie
            time.sleep(5)
            
            # Verificar que esté ejecutándose
            if self.server_process.poll() is None:
                self.log_result("Inicio del servidor", "PASS", "Servidor iniciado correctamente")
                return True
            else:
                stdout, stderr = self.server_process.communicate()
                self.log_result("Inicio del servidor", "FAIL", f"Error: {stderr}")
                return False
                
        except Exception as e:
            self.log_result("Inicio del servidor", "FAIL", f"Excepción: {e}")
            return False
            
    def test_api_endpoints(self):
        """Probar endpoints principales de la API"""
        print("\n🌐 Probando endpoints de la API...")
        
        base_url = "http://localhost:5001"
        
        endpoints_to_test = [
            ("/health", "Health check"),
            ("/api/datasets", "Lista de datasets"),
            ("/api/stats", "Estadísticas"),
            ("/", "Frontend principal")
        ]
        
        for endpoint, description in endpoints_to_test:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    self.log_result(f"API {endpoint}", "PASS", f"{description} - Status 200")
                else:
                    self.log_result(f"API {endpoint}", "WARN", f"{description} - Status {response.status_code}")
            except requests.exceptions.ConnectionError:
                self.log_result(f"API {endpoint}", "FAIL", "No se pudo conectar al servidor")
            except Exception as e:
                self.log_result(f"API {endpoint}", "FAIL", f"Error: {e}")
                
    def stop_test_server(self):
        """Detener servidor de prueba"""
        if self.server_process:
            print("\n🛑 Deteniendo servidor de prueba...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
                self.log_result("Detener servidor", "PASS", "Servidor detenido correctamente")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.log_result("Detener servidor", "WARN", "Servidor forzado a terminar")
                
    def check_configuration_issues(self):
        """Verificar problemas de configuración conocidos"""
        print("\n⚙️  Verificando configuración...")
        
        # Verificar rutas hardcodeadas en archivos clave
        files_to_check = [
            self.backend_dir / "start_server.py",
            self.project_root / "Makefile"
        ]
        
        hardcoded_pattern = "/Users/estebanroman/"
        
        for file_path in files_to_check:
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if hardcoded_pattern in content:
                            self.log_result(f"Config {file_path.name}", "WARN", "Contiene rutas hardcodeadas")
                        else:
                            self.log_result(f"Config {file_path.name}", "PASS", "Sin rutas hardcodeadas")
                except Exception as e:
                    self.log_result(f"Config {file_path.name}", "FAIL", f"Error leyendo: {e}")
                    
    def generate_verification_report(self):
        """Generar reporte de verificación"""
        report_path = self.project_root / "VERIFICATION_REPORT.md"
        
        # Contar resultados
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        warnings = len([r for r in self.results if r["status"] == "WARN"])
        total = len(self.results)
        
        report_content = f"""# 🔍 REPORTE DE VERIFICACIÓN POST-LIMPIEZA

**Fecha:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Script:** verify_project.py

## 📊 Resumen de Resultados

- **Total de pruebas:** {total}
- **✅ Exitosas:** {passed}
- **❌ Fallidas:** {failed}  
- **⚠️ Advertencias:** {warnings}
- **📈 Tasa de éxito:** {(passed/total)*100:.1f}%

## 📋 Resultados Detallados

"""
        
        for result in self.results:
            icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            report_content += f"- {icon} **{result['test']}**: {result['message']}\n"
            
        # Recomendaciones basadas en resultados
        report_content += "\n## 🎯 Recomendaciones\n\n"
        
        if failed > 0:
            report_content += "### ❌ Acciones Requeridas\n"
            for result in self.results:
                if result["status"] == "FAIL":
                    report_content += f"- Corregir: {result['test']} - {result['message']}\n"
                    
        if warnings > 0:
            report_content += "\n### ⚠️ Mejoras Sugeridas\n"
            for result in self.results:
                if result["status"] == "WARN":
                    report_content += f"- Revisar: {result['test']} - {result['message']}\n"
                    
        if failed == 0:
            report_content += "### 🎉 ¡Excelente!\n"
            report_content += "- El proyecto está funcionando correctamente después de la limpieza\n"
            report_content += "- Todas las pruebas esenciales pasaron\n"
            
        report_content += """
## 🚀 Próximos Pasos

1. **Si hay fallos:** Corregir los problemas identificados
2. **Si hay advertencias:** Evaluar e implementar mejoras
3. **Si todo está bien:** El proyecto está listo para uso/desarrollo

## 🔧 Comandos Útiles

```bash
# Iniciar el servidor manualmente
cd web_app/backend && python3 start_server.py

# Ejecutar pruebas del sistema  
python3 test_system.py

# Ver logs del sistema
tail -f web_app/backend/data/*.log
```
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
        print(f"\n📄 Reporte de verificación creado: {report_path}")
        
    def run_verification(self):
        """Ejecutar verificación completa"""
        print("🔍 VERIFICACIÓN POST-LIMPIEZA - Chile Open Data")
        print("=" * 60)
        
        # Ejecutar pruebas
        self.check_file_structure()
        self.check_removed_duplicates() 
        self.check_imports()
        self.check_configuration_issues()
        
        # Pruebas del servidor (opcional)
        print("\n❓ ¿Deseas probar el servidor en vivo? (y/N): ", end="")
        test_server = input().strip().lower() in ['y', 'yes', 'sí', 'si']
        
        if test_server:
            server_started = self.start_test_server()
            if server_started:
                self.test_api_endpoints()
                self.stop_test_server()
        
        # Generar reporte
        self.generate_verification_report()
        
        # Mostrar resumen
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        warnings = len([r for r in self.results if r["status"] == "WARN"])
        total = len(self.results)
        
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE VERIFICACIÓN")
        print(f"✅ Exitosas: {passed}/{total}")
        print(f"❌ Fallidas: {failed}/{total}")
        print(f"⚠️ Advertencias: {warnings}/{total}")
        print(f"📈 Tasa de éxito: {(passed/total)*100:.1f}%")
        
        if failed == 0:
            print("\n🎉 ¡VERIFICACIÓN EXITOSA!")
            print("El proyecto está funcionando correctamente")
        else:
            print("\n⚠️ PROBLEMAS DETECTADOS")
            print("Revisar VERIFICATION_REPORT.md para detalles")

def main():
    verifier = ProjectVerifier()
    verifier.run_verification()

if __name__ == "__main__":
    main()
