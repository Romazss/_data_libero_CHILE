# Makefile para Biblioteca de Datos Abiertos de Chile
# Facilita las tareas comunes de desarrollo y mantenimiento

.PHONY: help install check-python check-r run-backend test-api clean docs

# Configuración
PYTHON = python3
BACKEND_DIR = web_app/backend
FRONTEND_DIR = web_app/frontend
SCRIPTS_DIR = data_sources/scripts

# Ayuda por defecto
help:
	@echo "📚 Biblioteca de Datos Abiertos de Chile - Comandos Disponibles"
	@echo ""
	@echo "🔧 Configuración:"
	@echo "  install        Instalar dependencias Python"
	@echo "  setup-env      Configurar entorno virtual"
	@echo ""
	@echo "🏃 Ejecución:"
	@echo "  run-backend    Ejecutar servidor Flask"
	@echo "  open-frontend  Abrir frontend en navegador"
	@echo ""
	@echo "✅ Verificación:"
	@echo "  check-python   Verificar datasets con script Python"
	@echo "  check-r        Verificar datasets con script R (requiere R)"
	@echo "  test-api       Probar endpoints del backend"
	@echo ""
	@echo "📊 Utilidades:"
	@echo "  status         Estado actual de todos los datasets"
	@echo "  clean          Limpiar archivos temporales"
	@echo "  docs           Generar/actualizar documentación"

# Instalación de dependencias
install:
	@echo "📦 Instalando dependencias Python..."
	pip install -r $(BACKEND_DIR)/requirements.txt

setup-env:
	@echo "🔧 Configurando entorno virtual..."
	python3 -m venv .venv
	@echo "✅ Entorno creado. Activa con: source .venv/bin/activate"

# Ejecución del backend
run-backend:
	@echo "🚀 Iniciando servidor Flask..."
	cd $(BACKEND_DIR) && $(PYTHON) app.py

# Abrir frontend
open-frontend:
	@echo "🌐 Abriendo frontend en navegador..."
	@if command -v open >/dev/null 2>&1; then \
		open file://$(PWD)/$(FRONTEND_DIR)/index.html; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open file://$(PWD)/$(FRONTEND_DIR)/index.html; \
	else \
		echo "❌ No se pudo abrir automáticamente. Abre manualmente:"; \
		echo "   file://$(PWD)/$(FRONTEND_DIR)/index.html"; \
	fi

# Verificación con Python
check-python:
	@echo "🔍 Verificando datasets con Python..."
	$(PYTHON) $(SCRIPTS_DIR)/download_example.py --check-only

# Verificación con R (si está disponible)
check-r:
	@echo "🔍 Verificando datasets con R..."
	@if command -v Rscript >/dev/null 2>&1; then \
		Rscript -e "source('$(SCRIPTS_DIR)/download_example.R'); download_chile_data(check_only = TRUE)"; \
	else \
		echo "❌ R no está instalado. Instala R para usar esta función."; \
	fi

# Probar API del backend
test-api:
	@echo "🧪 Probando endpoints del backend..."
	@echo "Endpoint /health:"
	@curl -s http://localhost:5001/health || echo "❌ Backend no está ejecutándose"
	@echo ""
	@echo "Endpoint /status:"
	@curl -s http://localhost:5001/status | head -c 200 || echo "❌ Backend no está ejecutándose"
	@echo "..."

# Estado de datasets
status:
	@echo "📊 Estado actual de datasets:"
	@$(PYTHON) $(SCRIPTS_DIR)/download_example.py --check-only

# Limpiar archivos temporales
clean:
	@echo "🧹 Limpiando archivos temporales..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true
	find . -name ".DS_Store" -delete 2>/dev/null || true
	rm -rf downloads/ tmp/ logs/ 2>/dev/null || true
	@echo "✅ Limpieza completada"

# Generar documentación (placeholder para futuras expansiones)
docs:
	@echo "📖 Generando documentación..."
	@echo "✅ Documentación disponible en docs/"
	@echo "   • docs/intro.md - Introducción general"
	@echo "   • docs/Fase1.md - Documentación de Fase 1"
	@echo "   • README.md - Guía principal"

# Comandos para desarrollo
dev-install: setup-env install
	@echo "🔧 Entorno de desarrollo configurado"

dev-start: run-backend
	@echo "🚀 Entorno de desarrollo iniciado"

# Comando compuesto: verificar todo
check-all: check-python
	@echo ""
	@echo "✅ Verificación completa terminada"

# Comando compuesto: inicio completo
start: run-backend open-frontend
	@echo "🎉 Aplicación iniciada completamente"
