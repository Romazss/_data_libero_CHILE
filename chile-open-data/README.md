# Biblioteca de Datos Abiertos de Chile

<div align="center">

![Chile Flag](https://img.shields.io/badge/🇨🇱-Chile-red)
![Phase](https://img.shields.io/badge/Phase-1%20Complete-green)
![License](https://img.shields.io/badge/License-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![R](https://img.shields.io/badge/R-4.0+-blue)

**Centraliza, organiza y facilita el acceso a datos públicos de Chile**

[🚀 Inicio Rápido](#-inicio-rápido) • [📊 Datasets](#-datasets-disponibles) • [🔍 Demo](#-demo) • [🤝 Contribuir](#-contribuir)

</div>

## 🎯 Introducción

La **Biblioteca de Datos Abiertos de Chile** busca centralizar y organizar las principales fuentes de datos del país en un solo espacio abierto, accesible y escrutinable.

### Objetivos de la Fase 1 ✅
- ✅ Construir una estructura inicial de repositorio
- ✅ Integrar un archivo de configuración (`sources.yaml`) que defina las fuentes
- ✅ Implementar scripts de descarga en Python y R
- ✅ Portal web básico con monitoreo de disponibilidad
- ✅ Sentar las bases para futuras fases

### Principios
- **Transparencia** en las fuentes de datos
- **Acceso libre** y sencillo
- **Diseño estético** y experiencia de usuario cuidada
- **Reproducibilidad** y código abierto

## 🚀 Inicio Rápido

### 1. Verificar disponibilidad de datasets

**Python:**
```bash
# Instalar dependencias
pip install pyyaml requests

# Verificar todos los datasets
python data_sources/scripts/download_example.py --check-only

# Verificar por categoría
python data_sources/scripts/download_example.py --category economía --check-only
```

**R:**
```r
# Instalar dependencias (si es necesario)
install.packages(c("yaml", "httr", "jsonlite"))

# Cargar script
source("data_sources/scripts/download_example.R")

# Verificar disponibilidad
download_chile_data(check_only = TRUE)

# Por categoría
download_chile_data(category = "economía", check_only = TRUE)
```

### 2. Portal Web

```bash
# Instalar dependencias del backend
cd web_app/backend
pip install -r requirements.txt

# Ejecutar servidor
python app.py
```

Luego abrir `web_app/frontend/index.html` en el navegador.

## 📊 Datasets Disponibles

| Dataset | Categoría | Estado | Fuente |
|---------|-----------|--------|--------|
| PIB Trimestral | Economía | ✅ | Banco Central |
| Censo Población | Demografía | ✅ | INE |
| Defunciones DEIS | Salud | ⚠️ | MINSAL |
| Matrículas Educación | Educación | ⚠️ | MINEDUC |
| Encuesta Empleo | Trabajo | ⚠️ | Min. Trabajo |

> Estado en tiempo real disponible en el portal web

## 🔍 Demo

El portal web incluye:

- **Monitoreo en tiempo real** de disponibilidad de datasets
- **Filtros por categoría** y estado
- **Auto-refresh** configurable
- **Links directos** a las fuentes oficiales
- **Métricas de latencia** y códigos HTTP

## 🏗️ Estructura del Proyecto

```
chile-open-data/
├── README.md                    # Este archivo
├── LICENSE                      # Licencia MIT
├── .gitignore                   # Exclusiones de Git
├── data_sources/
│   ├── config/
│   │   └── sources.yaml        # ⭐ Catálogo central de fuentes
│   └── scripts/
│       ├── download_example.py  # Script Python de descarga
│       ├── download_example.R   # Script R de descarga
│       └── scraper/            # Sistema de extracción avanzado
├── web_app/
│   ├── backend/                # API Flask con monitoreo
│   └── frontend/               # Portal web moderno
├── libraries/                  # Futuras librerías R y Python
└── docs/                       # Documentación detallada
```

## 📝 Agregar Nuevas Fuentes

Edita `data_sources/config/sources.yaml`:

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

## 🤝 Contribuir

Este es un proyecto comunitario. Las contribuciones son bienvenidas:

1. **Nuevas fuentes**: Agrega datasets al `sources.yaml`
2. **Mejoras de código**: Backend, frontend, scripts
3. **Documentación**: Guías y ejemplos
4. **Diseño**: UX/UI y visualizaciones

### Próximas Fases

- **Fase 2**: Portal web robusto con API REST
- **Fase 3**: Librerías `chileDataR` y `chiledata`
- **Fase 4**: Monitoreo avanzado y analytics

## 📄 Licencia

Este proyecto está bajo licencia **MIT**. Ver [LICENSE](LICENSE) para más detalles.

---

<div align="center">

**Desarrollado con ❤️ para la comunidad chilena**

[⭐ Star este repo](../../stargazers) • [🐛 Reportar issue](../../issues) • [💬 Discusión](../../discussions)

</div>
