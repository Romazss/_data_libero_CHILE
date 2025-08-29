# Introducción - Biblioteca de Datos Abiertos de Chile

## ¿Qué es este proyecto?

La **Biblioteca de Datos Abiertos de Chile** es una iniciativa comunitaria que busca **centralizar, organizar y facilitar el acceso** a las principales fuentes de datos públicos del país.

## 🎯 Objetivos

- **Unificar fuentes**: Centralizar datasets dispersos en un solo lugar accesible
- **Facilitar acceso**: Proveer librerías en R y Python para importar datos con una función
- **Monitorear disponibilidad**: Auditar la disponibilidad de servidores y registrar caídas
- **Experiencia cuidada**: Diseño estético y documentación clara para todos los usuarios

## 🔥 Principios

1. **Transparencia total**: Código abierto, fuentes documentadas, metodología clara
2. **Acceso libre**: Sin restricciones de uso, datos disponibles para todos
3. **Reproducibilidad**: Scripts y procesos documentados y replicables
4. **Estética cuidada**: Interfaz moderna y experiencia de usuario pensada

## 📋 Alcances por Fase

### Fase 1: Base del Repositorio ✅
- [x] Estructura inicial del repositorio
- [x] Catálogo de fuentes (`sources.yaml`)
- [x] Scripts de descarga en Python y R
- [x] Web app básica con monitoreo de estado
- [x] Documentación fundamental

### Fase 2: Portal Web 🚧
- [ ] Backend robusto (Flask/FastAPI) que lea `sources.yaml`
- [ ] Frontend con buscador y filtros
- [ ] API REST para acceso programático
- [ ] Sistema de monitoreo automatizado

### Fase 3: Librerías Especializadas
- [ ] Paquete R (`chileDataR`)
- [ ] Paquete Python (`chiledata`)
- [ ] Funciones de carga directa desde el portal
- [ ] Cache inteligente y sincronización

### Fase 4: Monitoreo y Análisis
- [ ] Dashboard de disponibilidad histórica
- [ ] Alertas automáticas por caídas
- [ ] Métricas de uso y adopción
- [ ] Reportes de calidad de datos

## 🏗️ Arquitectura

```
/
├── data_sources/           # Configuración y scripts de descarga
│   ├── config/
│   │   └── sources.yaml   # Catálogo central de fuentes
│   └── scripts/
│       ├── download_example.py
│       ├── download_example.R
│       └── scraper/       # Sistema de extracción avanzado
├── web_app/               # Aplicación web
│   ├── backend/           # API REST en Flask
│   └── frontend/          # Interface HTML/CSS/JS
├── libraries/             # Librerías R y Python
│   ├── python_package/
│   └── r_package/
└── docs/                  # Documentación
```

## 🚀 Inicio Rápido

### 1. Verificar disponibilidad de datasets

**Python:**
```bash
python data_sources/scripts/download_example.py --check-only
```

**R:**
```r
source("data_sources/scripts/download_example.R")
download_chile_data(check_only = TRUE)
```

### 2. Ejecutar portal web

```bash
cd web_app/backend
pip install -r requirements.txt
python app.py
```

Luego abrir `web_app/frontend/index.html` en el navegador.

### 3. Agregar nuevas fuentes

Editar `data_sources/config/sources.yaml`:

```yaml
datasets:
  - id: "mi_dataset"
    name: "Mi Dataset Personalizado"
    category: "mi_categoria"
    url: "https://ejemplo.cl/datos"
    description: "Descripción del dataset"
    method: "HEAD"  # o "GET"
    timeout: 10
```

## 📊 Fuentes Actuales

El catálogo inicial incluye datasets de:

- **Economía**: Banco Central (PIB, indicadores)
- **Demografía**: INE (Censo, población)
- **Salud**: DEIS MINSAL (defunciones, causas)
- **Educación**: MINEDUC (matrículas, rendimiento)
- **Trabajo**: Ministerio del Trabajo (empleo, salarios)

## 🤝 Contribuir

Este es un proyecto comunitario. Las contribuciones son bienvenidas en:

1. **Nuevas fuentes de datos**: Agregar al `sources.yaml`
2. **Mejoras de código**: Scripts, backend, frontend
3. **Documentación**: Guías, ejemplos, tutoriales
4. **Diseño**: UX/UI, visualizaciones, iconografía

## 📄 Licencia

Este proyecto está bajo licencia **MIT** - ver archivo `LICENSE` para detalles.

---

**¿Dudas o sugerencias?** Abre un issue o contribuye directamente al repositorio.
