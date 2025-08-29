# Biblioteca de Datos Abiertos de Chile

La **Biblioteca de Datos Abiertos de Chile** centraliza y organiza fuentes públicas relevantes en un repositorio abierto, reproducible y estético. La Fase 1 se enfoca en dejar operativo el esqueleto del proyecto (estructura, configuración, y primeros scripts de descarga).

## Objetivos Fase 1
- Estructura de repositorio estandarizada.
- `sources.yaml` con fuentes iniciales.
- Scripts de descarga en Python y R.
- Documentación básica.

## Estructura
/
├── README.md
├── LICENSE
├── .gitignore
├── /data_sources
│   ├── config/
│   │   └── sources.yaml
│   └── scripts/
│       ├── download_example.py
│       └── download_example.R
├── /web_app
|
├── backend/
│   ├── app.py
│   ├── services/
│   │   ├── sources.py
│   │   └── checker.py
│   └── requirements.txt
|
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js
│   ├── frontend/
│   └── backend/
|
├── /libraries
│   ├── r_package/
│   └── python_package/
└── /docs
└── intro.md
## Requisitos
•	Python 3.11.7+

•	R 4.2+ 

## Fuentes iniciales
	•	Banco Central de Chile (TPM, IPC)
	•	INE (Censos/Encuestas)
	•	DEIS (MINSAL, defunciones)
	•	SERVEL (elecciones)
	•	Biblioteca del Congreso (leyes)
	•	Data.gob.cl (catálogo CKAN)

## Principios
	•	Transparencia y trazabilidad (YAML + scripts reproducibles).
	•	Acceso libre y simple.
	•	UX y diseño cuidados (a desarrollar en fases siguientes).
	•	Monitoreo y registro de caídas (base para Fase 2).