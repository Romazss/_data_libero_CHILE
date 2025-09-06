# /web_app/backend/developer_portal.py
"""
Portal para desarrolladores - Gestión de API keys y documentación
"""

from flask import Blueprint, render_template_string, jsonify, request, g
from auth import api_key_manager, require_api_key, optional_api_key
from error_handlers import safe_api_call, APIError
import json
from datetime import datetime, timedelta

# Blueprint para el portal de desarrolladores
developer_bp = Blueprint('developer', __name__, url_prefix='/developer')

# HTML Template para el dashboard de desarrolladores
DEVELOPER_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portal de Desarrolladores - Chile Open Data</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .content {
            padding: 30px;
        }
        
        .tabs {
            display: flex;
            border-bottom: 2px solid #f0f0f0;
            margin-bottom: 30px;
        }
        
        .tab {
            padding: 15px 25px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 1rem;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
        }
        
        .tab.active {
            color: #2a5298;
            border-bottom-color: #2a5298;
            font-weight: 600;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .card {
            background: #f8f9ff;
            border: 1px solid #e1e8ff;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .api-key-form {
            display: grid;
            gap: 15px;
            max-width: 500px;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
        }
        
        .form-group label {
            margin-bottom: 5px;
            font-weight: 600;
            color: #333;
        }
        
        .form-group input, .form-group select, .form-group textarea {
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 1rem;
        }
        
        .btn {
            padding: 12px 25px;
            border: none;
            border-radius: 6px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: #2a5298;
            color: white;
        }
        
        .btn-primary:hover {
            background: #1e3c72;
        }
        
        .api-key-display {
            background: #f0f8ff;
            border: 1px solid #b3d9ff;
            padding: 15px;
            border-radius: 6px;
            margin-top: 15px;
        }
        
        .api-key-value {
            font-family: 'Courier New', monospace;
            background: #fff;
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #ccc;
            margin-top: 5px;
            word-break: break-all;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border: 1px solid #e1e8ff;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #2a5298;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9rem;
        }
        
        .endpoint-list {
            display: grid;
            gap: 10px;
        }
        
        .endpoint-item {
            background: white;
            border: 1px solid #e1e8ff;
            border-radius: 6px;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .endpoint-method {
            background: #4CAF50;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .endpoint-method.POST { background: #FF9800; }
        .endpoint-method.PUT { background: #2196F3; }
        .endpoint-method.DELETE { background: #f44336; }
        
        .rate-limit-info {
            background: #fff3cd;
            border: 1px solid #ffd43b;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .chart-container {
            width: 100%;
            height: 400px;
            margin-top: 20px;
        }
        
        .code-sample {
            background: #1e1e1e;
            color: #fff;
            padding: 20px;
            border-radius: 6px;
            overflow-x: auto;
            margin-top: 15px;
        }
        
        .copy-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            float: right;
            margin-top: -45px;
            margin-right: 10px;
        }
        
        .tier-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .tier-free { background: #e3f2fd; color: #1976d2; }
        .tier-pro { background: #f3e5f5; color: #7b1fa2; }
        .tier-enterprise { background: #fff3e0; color: #f57c00; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Portal de Desarrolladores</h1>
            <p>API de Datos Abiertos de Chile - Gestiona tus claves y monitorea tu uso</p>
        </div>
        
        <div class="content">
            <div class="tabs">
                <button class="tab active" onclick="showTab('overview')">📊 Overview</button>
                <button class="tab" onclick="showTab('keys')">🔑 API Keys</button>
                <button class="tab" onclick="showTab('docs')">📖 Documentación</button>
                <button class="tab" onclick="showTab('examples')">💻 Ejemplos</button>
            </div>
            
            <!-- Overview Tab -->
            <div id="overview" class="tab-content active">
                <div class="rate-limit-info">
                    <h3>📈 Límites de Rate</h3>
                    <p>Los límites dependen de tu tier de API key. Monitorea tu uso para evitar interrupciones.</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value" id="totalRequests">0</div>
                        <div class="stat-label">Requests Hoy</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="avgResponseTime">0ms</div>
                        <div class="stat-label">Tiempo Promedio</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="successRate">0%</div>
                        <div class="stat-label">Tasa de Éxito</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="remainingQuota">0</div>
                        <div class="stat-label">Quota Restante</div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📊 Uso por Endpoint (Últimas 24h)</h3>
                    <div class="chart-container">
                        <canvas id="usageChart"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- API Keys Tab -->
            <div id="keys" class="tab-content">
                <div class="card">
                    <h3>🔑 Generar Nueva API Key</h3>
                    <form class="api-key-form" onsubmit="generateApiKey(event)">
                        <div class="form-group">
                            <label for="keyName">Nombre de la Key</label>
                            <input type="text" id="keyName" required placeholder="Mi aplicación web">
                        </div>
                        <div class="form-group">
                            <label for="userEmail">Email</label>
                            <input type="email" id="userEmail" required placeholder="developer@ejemplo.com">
                        </div>
                        <div class="form-group">
                            <label for="keyTier">Tier</label>
                            <select id="keyTier">
                                <option value="free">Free - 100/hora, 1,000/día</option>
                                <option value="pro">Pro - 1,000/hora, 10,000/día</option>
                                <option value="enterprise">Enterprise - 10,000/hora, 100,000/día</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="keyDescription">Descripción</label>
                            <textarea id="keyDescription" placeholder="Descripción opcional..."></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary">Generar API Key</button>
                    </form>
                    
                    <div id="apiKeyResult" class="api-key-display" style="display: none;">
                        <h4>🎉 API Key Generada Exitosamente</h4>
                        <p><strong>⚠️ Importante:</strong> Guarda esta key de forma segura. No podrás verla nuevamente.</p>
                        <div class="api-key-value" id="newApiKey"></div>
                        <button class="copy-btn" onclick="copyApiKey()">Copiar</button>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📋 Mis API Keys</h3>
                    <div id="apiKeysList">
                        <!-- Lista de API keys se carga dinámicamente -->
                    </div>
                </div>
            </div>
            
            <!-- Documentation Tab -->
            <div id="docs" class="tab-content">
                <div class="card">
                    <h3>📖 Documentación de la API</h3>
                    
                    <h4>🔐 Autenticación</h4>
                    <p>Incluye tu API key en cada request usando uno de estos métodos:</p>
                    
                    <div class="code-sample">
# Método 1: Header Authorization
curl -H "Authorization: Bearer tu_api_key_aqui" \\
     https://api.chiledatos.cl/status

# Método 2: Header X-API-Key  
curl -H "X-API-Key: tu_api_key_aqui" \\
     https://api.chiledatos.cl/status
                    </div>
                    
                    <h4>🛡️ Rate Limiting</h4>
                    <p>Los headers de respuesta incluyen información sobre tus límites:</p>
                    <div class="code-sample">
X-RateLimit-Limit-Hour: 100
X-RateLimit-Remaining-Hour: 85
X-RateLimit-Reset-Hour: 2025-08-29T14:00:00Z
X-RateLimit-Limit-Day: 1000
X-RateLimit-Remaining-Day: 750
X-RateLimit-Reset-Day: 2025-08-30T00:00:00Z
                    </div>
                </div>
                
                <div class="card">
                    <h3>🎯 Endpoints Disponibles</h3>
                    <div class="endpoint-list" id="endpointsList">
                        <!-- Endpoints se cargan dinámicamente -->
                    </div>
                </div>
            </div>
            
            <!-- Examples Tab -->
            <div id="examples" class="tab-content">
                <div class="card">
                    <h3>💻 Ejemplos de Código</h3>
                    
                    <h4>🐍 Python</h4>
                    <div class="code-sample">
import requests

API_KEY = "tu_api_key_aqui"
BASE_URL = "https://api.chiledatos.cl"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Obtener estado de datasets
response = requests.get(f"{BASE_URL}/status", headers=headers)
datasets = response.json()

print(f"Datasets disponibles: {len(datasets['datasets'])}")
for dataset in datasets['datasets']:
    print(f"- {dataset['name']}: {dataset['status']}")
                    </div>
                    
                    <h4>🟨 JavaScript</h4>
                    <div class="code-sample">
const API_KEY = 'tu_api_key_aqui';
const BASE_URL = 'https://api.chiledatos.cl';

const headers = {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
};

// Obtener métricas del sistema
async function getSystemMetrics() {
    try {
        const response = await fetch(`${BASE_URL}/api/analytics/system-metrics`, {
            headers: headers
        });
        
        const data = await response.json();
        console.log('Métricas del sistema:', data);
        
        return data;
    } catch (error) {
        console.error('Error:', error);
    }
}

getSystemMetrics();
                    </div>
                    
                    <h4>📱 cURL</h4>
                    <div class="code-sample">
# Obtener datasets por categoría
curl -H "Authorization: Bearer tu_api_key_aqui" \\
     "https://api.chiledatos.cl/api/analytics/category-analytics"

# Generar reporte personalizado
curl -X POST \\
     -H "Authorization: Bearer tu_api_key_aqui" \\
     -H "Content-Type: application/json" \\
     "https://api.chiledatos.cl/api/reports/generate-custom?hours=168"

# Exportar datos en CSV
curl -H "Authorization: Bearer tu_api_key_aqui" \\
     "https://api.chiledatos.cl/api/analytics/export?format=csv&hours=24" \\
     --output datos_chile.csv
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentApiKey = null;
        
        function showTab(tabName) {
            // Ocultar todas las tabs
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Mostrar tab seleccionada
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            
            // Cargar datos específicos
            if (tabName === 'overview') {
                loadOverviewData();
            } else if (tabName === 'keys') {
                loadApiKeys();
            } else if (tabName === 'docs') {
                loadEndpoints();
            }
        }
        
        async function generateApiKey(event) {
            event.preventDefault();
            
            const formData = {
                name: document.getElementById('keyName').value,
                user_email: document.getElementById('userEmail').value,
                tier: document.getElementById('keyTier').value,
                description: document.getElementById('keyDescription').value
            };
            
            try {
                const response = await fetch('/developer/api/generate-key', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('newApiKey').textContent = result.api_key;
                    document.getElementById('apiKeyResult').style.display = 'block';
                    currentApiKey = result.api_key;
                    
                    // Limpiar formulario
                    document.querySelector('.api-key-form').reset();
                } else {
                    alert('Error generando API key: ' + result.error);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        
        function copyApiKey() {
            if (currentApiKey) {
                navigator.clipboard.writeText(currentApiKey);
                alert('API Key copiada al portapapeles');
            }
        }
        
        async function loadOverviewData() {
            // Simular datos por ahora
            document.getElementById('totalRequests').textContent = '1,247';
            document.getElementById('avgResponseTime').textContent = '245ms';
            document.getElementById('successRate').textContent = '99.2%';
            document.getElementById('remainingQuota').textContent = '8,753';
        }
        
        async function loadApiKeys() {
            // Cargar lista de API keys (simulado)
            const keysList = document.getElementById('apiKeysList');
            keysList.innerHTML = `
                <div class="endpoint-item">
                    <div>
                        <strong>Mi App Web</strong>
                        <span class="tier-badge tier-free">Free</span>
                        <div style="font-size: 0.9rem; color: #666;">ak_1234...abcd</div>
                        <div style="font-size: 0.8rem; color: #666;">Creada: 2025-08-29</div>
                    </div>
                    <div>
                        <button class="btn btn-primary">Ver Stats</button>
                    </div>
                </div>
            `;
        }
        
        async function loadEndpoints() {
            const endpoints = [
                {method: 'GET', path: '/health', description: 'Estado del sistema'},
                {method: 'GET', path: '/status', description: 'Estado de todos los datasets'},
                {method: 'GET', path: '/stats', description: 'Estadísticas generales'},
                {method: 'POST', path: '/check', description: 'Forzar verificación'},
                {method: 'GET', path: '/api/analytics/system-metrics', description: 'Métricas del sistema'},
                {method: 'GET', path: '/api/analytics/top-datasets', description: 'Top datasets por confiabilidad'},
                {method: 'GET', path: '/api/analytics/export', description: 'Exportar datos'},
                {method: 'POST', path: '/api/reports/generate-custom', description: 'Generar reporte personalizado'},
            ];
            
            const endpointsList = document.getElementById('endpointsList');
            endpointsList.innerHTML = endpoints.map(endpoint => `
                <div class="endpoint-item">
                    <div>
                        <span class="endpoint-method ${endpoint.method}">${endpoint.method}</span>
                        <strong>${endpoint.path}</strong>
                        <div style="font-size: 0.9rem; color: #666;">${endpoint.description}</div>
                    </div>
                </div>
            `).join('');
        }
        
        // Cargar datos iniciales
        document.addEventListener('DOMContentLoaded', function() {
            loadOverviewData();
        });
    </script>
</body>
</html>
"""

@developer_bp.route('/')
def dashboard():
    """Dashboard principal para desarrolladores"""
    return render_template_string(DEVELOPER_DASHBOARD_HTML)

@developer_bp.route('/api/generate-key', methods=['POST'])
@safe_api_call
def generate_api_key():
    """Generar nueva API key"""
    data = request.get_json()
    
    required_fields = ['name', 'user_email']
    for field in required_fields:
        if not data.get(field):
            raise APIError(f"Campo requerido: {field}", 400)
    
    tier = data.get('tier', 'free')
    if tier not in ['free', 'pro', 'enterprise']:
        tier = 'free'
    
    try:
        key_id, raw_key = api_key_manager.generate_api_key(
            name=data['name'],
            user_email=data['user_email'],
            tier=tier,
            description=data.get('description', '')
        )
        
        return jsonify({
            'success': True,
            'key_id': key_id,
            'api_key': raw_key,
            'tier': tier,
            'message': 'API key generada exitosamente'
        })
        
    except Exception as e:
        raise APIError(f"Error generando API key: {str(e)}", 500)

@developer_bp.route('/api/keys', methods=['GET'])
@safe_api_call
def list_api_keys():
    """Listar API keys de un usuario"""
    user_email = request.args.get('email')
    if not user_email:
        raise APIError("Email requerido", 400)
    
    # Implementar listado de keys por email
    # Por seguridad, solo mostrar información básica
    return jsonify({
        'success': True,
        'keys': []  # Implementar lógica de listado
    })

@developer_bp.route('/api/key/<key_id>/stats', methods=['GET'])
@require_api_key
def get_key_stats(key_id):
    """Obtener estadísticas de uso de una API key"""
    hours = int(request.args.get('hours', 24))
    
    if g.api_key.key_id != key_id:
        raise APIError("No autorizado para ver estadísticas de esta key", 403)
    
    stats = api_key_manager.get_api_key_stats(key_id, hours)
    
    return jsonify({
        'success': True,
        'key_id': key_id,
        'timeframe_hours': hours,
        'stats': stats
    })

@developer_bp.route('/api/key/<key_id>/deactivate', methods=['POST'])
@require_api_key  
def deactivate_api_key(key_id):
    """Desactivar una API key"""
    if g.api_key.key_id != key_id:
        raise APIError("No autorizado para desactivar esta key", 403)
    
    # Implementar desactivación
    return jsonify({
        'success': True,
        'message': 'API key desactivada'
    })
