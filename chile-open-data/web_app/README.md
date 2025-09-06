# 🇨🇱 Biblioteca de Datos Abiertos de Chile

## 🚀 Aplicación Web Completa - Backend + Frontend

### ✅ Estado del Sistema
- **Backend API**: ✅ Funcionando (puerto 5001)
- **Frontend Web**: ✅ Funcionando (puerto 8080)
- **Datasets monitoreados**: 5 fuentes de datos
- **Disponibilidad actual**: 4/5 (80%) - ⚡ 595ms latencia promedio

---

## 🌐 Acceso a la Aplicación

### 🖥️ Interfaz Web Principal
```
http://localhost:8080
```

### 🔧 API Endpoints
```bash
# Estado del sistema
http://localhost:5001/health

# Lista de datasets
http://localhost:5001/api/v1/datasets

# Estadísticas del sistema
http://localhost:5001/api/v1/stats

# Categorías de datos
http://localhost:5001/api/v1/categories

# Forzar actualización
http://localhost:5001/api/v1/refresh
```

---

## 🚀 Cómo Iniciar la Aplicación

### Opción 1: Script Python (Recomendado)
```bash
cd web_app/backend
python3 start_app.py
```

### Opción 2: Script Bash
```bash
cd web_app/backend
./start_app.sh
```

### Opción 3: Manual (Desarrollo)
```bash
# Terminal 1 - Backend
cd web_app/backend
python3 ultra_simple_server.py

# Terminal 2 - Frontend
cd web_app/backend
python3 frontend_server.py
```

---

## 📊 Datasets Monitoreados

| ID | Nombre | Categoría | Estado | URL |
|---|---|---|---|---|
| `bcentral_pib` | PIB Trimestral - Banco Central | economía | ✅ | https://si3.bcentral.cl/... |
| `ine_censo` | Censo de Población y Vivienda - INE | demografía | ✅ | https://www.ine.cl/... |
| `datos_gob_cl` | Portal Nacional de Datos Abiertos | gobierno | ✅ | https://www.datos.gob.cl |
| `sernac_reclamos` | SERNAC - Portal de Reclamos | consumidor | ✅ | https://www.sernac.cl/... |
| `ine_portal_estadisticas` | Portal Estadísticas INE | estadísticas | ❌ | https://www.ine.cl/estadisticas |

---

## 🔧 Características Técnicas

### Backend API
- **Tecnología**: Python HTTP Server (sin dependencias externas)
- **Puerto**: 5001
- **Actualización automática**: Cada 5 minutos
- **Verificación paralela**: 3 workers simultáneos
- **CORS**: Habilitado para frontend

### Frontend Web
- **Tecnología**: HTML5 + CSS3 + JavaScript
- **Puerto**: 8080
- **Conexión API**: http://localhost:5001
- **Interfaz**: Dashboard en tiempo real

---

## 🛠️ Desarrollo y Personalización

### Agregar Nuevos Datasets
Editar el archivo `ultra_simple_server.py` en la sección `DATASETS_CONFIG`:

```python
DATASETS_CONFIG = [
    {
        'id': 'nuevo_dataset',
        'name': 'Nombre del Dataset',
        'category': 'categoria',
        'url': 'https://ejemplo.cl/datos',
        'description': 'Descripción del dataset',
        'timeout': 10
    },
    # ... otros datasets
]
```

### Personalizar Frontend
Los archivos del frontend están en `/web_app/frontend/`:
- `index.html` - Estructura HTML
- `style.css` - Estilos CSS
- `app.js` - Lógica JavaScript

### API Response Format
```json
{
  "status": "success",
  "datasets": [...],
  "statistics": {
    "total_datasets": 5,
    "available_datasets": 4,
    "availability_rate": 80.0,
    "average_latency_ms": 595.71
  }
}
```

---

## 🐛 Solución de Problemas

### Puerto en uso
```bash
# Limpiar puerto 5001
lsof -ti:5001 | xargs kill -9

# Limpiar puerto 8080  
lsof -ti:8080 | xargs kill -9
```

### Verificar conectividad
```bash
# Test backend
curl http://localhost:5001/health

# Test frontend
curl http://localhost:8080
```

### Logs de depuración
Los servidores muestran logs en tiempo real:
- ✅ Cache actualizado: X/Y datasets disponibles
- 🔄 Actualizando cache de datasets...
- 127.0.0.1 - - [timestamp] "GET /api/v1/stats HTTP/1.1" 200

---

## 📈 Próximas Funcionalidades

- [ ] WebSockets para actualizaciones en tiempo real
- [ ] Autenticación con API keys
- [ ] Base de datos persistente
- [ ] Panel de administración
- [ ] Exportación de datos (CSV, JSON)
- [ ] Alertas por email
- [ ] Métricas históricas

---

## 🎯 Resumen de Comandos Rápidos

```bash
# Iniciar aplicación completa
python3 start_app.py

# Solo backend
python3 ultra_simple_server.py

# Solo frontend  
python3 frontend_server.py

# Verificar estado
curl http://localhost:5001/health

# Abrir en navegador
open http://localhost:8080
```

¡Tu Biblioteca de Datos Abiertos de Chile está lista para usar! 🇨🇱📊
