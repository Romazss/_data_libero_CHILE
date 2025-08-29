# Introducción

La **Biblioteca de Datos Abiertos de Chile** es un esfuerzo comunitario por unificar fuentes públicas en un único lugar, con **trazabilidad**, **reproducibilidad** y una **experiencia de usuario cuidada**.

## Visión
- Facilitar la descarga e integración de datos de alta demanda (economía, salud, elecciones, trabajo, educación, etc.).
- Proveer **librerías en R y Python** para importar datasets con una sola función.
- Auditar la **disponibilidad de los servidores** y registrar caídas para visibilizar brechas de acceso.

## Alcance Fase 1
- Estructura base del repositorio.
- Catálogo inicial de fuentes (`sources.yaml`).
- Scripts de descarga en R y Python.
- Documentación mínima para empezar.

## Próximos pasos
- Monitoreo (cron + logs, checks de estado HTTP, tiempos de respuesta).
- Portal web minimalista con buscador y fichas de dataset.
- Paquetes `chileDataR` y `chiledata` (helpers de importación).