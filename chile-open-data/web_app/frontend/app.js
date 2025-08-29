// app.js - Fase 2
// /web_app/frontend/app.js
/**
 * Frontend JavaScript para la Biblioteca de Datos Abiertos de Chile - Fase 2
 * Interfaz completa con filtros, búsqueda, histórico y monitoreo en tiempo real
 */

class ChileDataApp {
  constructor() {
    this.API_BASE = this.detectApiUrl();
    this.cache = new Map();
    this.filters = {
      category: '',
      status: ''
    };
    this.autoRefreshTimer = null;
    this.isLoading = false;
    
    // WebSocket y notificaciones
    this.socket = null;
    this.notifications = [];
    this.unreadCount = 0;
    this.isConnected = false;
    
    // Referencias a elementos DOM
    this.elements = {
      // Stats
      totalDatasets: document.getElementById('totalDatasets'),
      availableDatasets: document.getElementById('availableDatasets'),
      avgLatency: document.getElementById('avgLatency'),
      
      // Controls
      refreshBtn: document.getElementById('refreshBtn'),
      forceCheckBtn: document.getElementById('forceCheckBtn'),
      categoryFilter: document.getElementById('categoryFilter'),
      statusFilter: document.getElementById('statusFilter'),
      autoRefresh: document.getElementById('autoRefresh'),
      clearFiltersBtn: document.getElementById('clearFiltersBtn'),
      
      // Content
      loadingIndicator: document.getElementById('loadingIndicator'),
      tbody: document.getElementById('tbody'),
      error: document.getElementById('error'),
      noData: document.getElementById('noData'),
      
      // Footer
      apiStatus: document.getElementById('apiStatus'),
      statusIndicator: document.getElementById('statusIndicator'),
      statusText: document.getElementById('statusText'),
      lastUpdated: document.getElementById('lastUpdated'),
      
      // Notificaciones
      notificationBtn: document.getElementById('notificationBtn'),
      notificationBadge: document.getElementById('notificationBadge'),
      connectionStatus: document.getElementById('connectionStatus'),
      notificationsModal: document.getElementById('notificationsModal'),
      closeNotificationsModal: document.getElementById('closeNotificationsModal'),
      clearNotificationsBtn: document.getElementById('clearNotificationsBtn'),
      notificationsContent: document.getElementById('notificationsContent'),
      
      // Modal histórico
      historyModal: document.getElementById('historyModal'),
      modalOverlay: document.getElementById('modalOverlay'),
      modalTitle: document.getElementById('modalTitle'),
      closeModal: document.getElementById('closeModal'),
      historyPeriod: document.getElementById('historyPeriod'),
      historyContent: document.getElementById('historyContent')
    };
    
    this.init();
  }
  
  detectApiUrl() {
    const isLocal = location.hostname === "localhost" || location.hostname === "127.0.0.1";
    return isLocal ? "http://localhost:5001" : window.location.origin;
  }
  
  init() {
    this.setupEventListeners();
    this.initWebSocket();
    this.loadInitialData();
    this.checkApiHealth();
    this.setupAutoRefresh();
  }
  
  setupEventListeners() {
    // Botones principales
    this.elements.refreshBtn.addEventListener('click', () => this.loadStatus());
    this.elements.forceCheckBtn.addEventListener('click', () => this.forceCheck());
    
    // Filtros
    this.elements.categoryFilter.addEventListener('change', (e) => {
      this.filters.category = e.target.value;
      this.applyFilters();
    });
    
    this.elements.statusFilter.addEventListener('change', (e) => {
      this.filters.status = e.target.value;
      this.applyFilters();
    });
    
    this.elements.clearFiltersBtn.addEventListener('click', () => this.clearFilters());
    
    // Auto-refresh
    this.elements.autoRefresh.addEventListener('change', (e) => {
      this.setupAutoRefresh();
    });
    
    // Modal
    this.elements.closeModal.addEventListener('click', () => this.closeModal());
    this.elements.modalOverlay.addEventListener('click', () => this.closeModal());
    this.elements.historyPeriod.addEventListener('change', () => this.loadCurrentHistory());
    
    // Escape key para cerrar modal
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closeModal();
        this.closeNotificationsModal();
      }
    });
    
    // Event listeners para notificaciones
    this.elements.notificationBtn.addEventListener('click', () => this.showNotifications());
    this.elements.closeNotificationsModal.addEventListener('click', () => this.closeNotificationsModal());
    this.elements.clearNotificationsBtn.addEventListener('click', () => this.clearNotifications());
  }
  
  async loadInitialData() {
    try {
      // Cargar categorías para el filtro
      await this.loadCategories();
      
      // Cargar estado inicial
      await this.loadStatus();
      
      // Cargar estadísticas
      await this.loadStats();
      
    } catch (error) {
      console.error('Error loading initial data:', error);
      this.showError('Error cargando datos iniciales');
    }
  }
  
  async loadCategories() {
    try {
      const response = await this.apiCall('/categories');
      const data = await response.json();
      
      if (response.ok) {
        this.populateCategoryFilter(data.categories);
      }
    } catch (error) {
      console.warn('Error loading categories:', error);
    }
  }
  
  populateCategoryFilter(categories) {
    const select = this.elements.categoryFilter;
    
    // Limpiar opciones existentes (excepto "Todas")
    while (select.children.length > 1) {
      select.removeChild(select.lastChild);
    }
    
    // Agregar categorías
    categories.forEach(category => {
      const option = document.createElement('option');
      option.value = category.name;
      option.textContent = `${category.name} (${category.count})`;
      select.appendChild(option);
    });
  }
  
  async loadStatus() {
    if (this.isLoading) return;
    
    try {
      this.setLoading(true);
      this.hideError();
      
      const response = await this.apiCall('/status');
      const data = await response.json();
      
      if (response.ok) {
        this.displayDatasets(data.results);
        this.updateLastUpdated(data.last_updated);
        this.updateApiStatus('connected');
      } else {
        throw new Error(data.error || 'Error loading status');
      }
      
    } catch (error) {
      console.error('Error loading status:', error);
      this.showError(`Error cargando estado: ${error.message}`);
      this.updateApiStatus('error');
    } finally {
      this.setLoading(false);
    }
  }
  
  async loadStats() {
    try {
      const response = await this.apiCall('/stats');
      const data = await response.json();
      
      if (response.ok) {
        this.updateStatsDisplay(data.stats);
      }
    } catch (error) {
      console.warn('Error loading stats:', error);
    }
  }
  
  async forceCheck() {
    try {
      this.elements.forceCheckBtn.disabled = true;
      this.elements.forceCheckBtn.innerHTML = '<span class="btn-icon">⏳</span> Verificando...';
      
      const response = await this.apiCall('/check', { method: 'POST' });
      const data = await response.json();
      
      if (response.ok) {
        // Esperar un momento y recargar
        setTimeout(() => this.loadStatus(), 2000);
        this.showSuccess('Verificación forzada iniciada');
      } else {
        throw new Error(data.error || 'Error forcing check');
      }
      
    } catch (error) {
      console.error('Error forcing check:', error);
      this.showError(`Error forzando verificación: ${error.message}`);
    } finally {
      setTimeout(() => {
        this.elements.forceCheckBtn.disabled = false;
        this.elements.forceCheckBtn.innerHTML = '<span class="btn-icon">⚡</span> Verificar Ahora';
      }, 3000);
    }
  }
  
  displayDatasets(datasets) {
    if (!datasets || datasets.length === 0) {
      this.showNoData();
      return;
    }
    
    this.elements.noData.classList.add('hidden');
    
    const tbody = this.elements.tbody;
    tbody.innerHTML = '';
    
    datasets.forEach(dataset => {
      const row = this.createDatasetRow(dataset);
      tbody.appendChild(row);
    });
    
    this.applyFilters();
  }
  
  createDatasetRow(dataset) {
    const row = document.createElement('tr');
    row.dataset.category = dataset.category;
    row.dataset.status = dataset.status;
    
    const statusBadge = this.createStatusBadge(dataset.status);
    const latency = dataset.latency_ms ? `${dataset.latency_ms}ms` : '—';
    const httpCode = dataset.http_code || dataset.error || '—';
    const lastCheck = dataset.checked_at ? this.formatDate(dataset.checked_at) : '—';
    
    row.innerHTML = `
      <td>
        <a href="${dataset.url}" target="_blank" rel="noreferrer" title="Abrir fuente original">
          ${this.escapeHtml(dataset.name)}
        </a>
      </td>
      <td>
        <span class="category-tag">${this.escapeHtml(dataset.category)}</span>
      </td>
      <td>${statusBadge}</td>
      <td>${latency}</td>
      <td>${httpCode}</td>
      <td class="text-muted">${lastCheck}</td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="app.showHistory('${dataset.id}', '${this.escapeHtml(dataset.name)}')">
          📊 Histórico
        </button>
      </td>
    `;
    
    return row;
  }
  
  createStatusBadge(status) {
    const statusMap = {
      'up': { text: 'Disponible', class: 'up', icon: '✅' },
      'down': { text: 'No disponible', class: 'down', icon: '❌' },
      'unknown': { text: 'Desconocido', class: 'unknown', icon: '❓' }
    };
    
    const info = statusMap[status] || statusMap.unknown;
    return `<span class="badge ${info.class}">${info.icon} ${info.text}</span>`;
  }
  
  applyFilters() {
    const rows = this.elements.tbody.querySelectorAll('tr');
    let visibleCount = 0;
    
    rows.forEach(row => {
      const matchesCategory = !this.filters.category || 
        row.dataset.category === this.filters.category;
      const matchesStatus = !this.filters.status || 
        row.dataset.status === this.filters.status;
      
      if (matchesCategory && matchesStatus) {
        row.style.display = '';
        visibleCount++;
      } else {
        row.style.display = 'none';
      }
    });
    
    if (visibleCount === 0 && rows.length > 0) {
      this.showNoData();
    } else {
      this.elements.noData.classList.add('hidden');
    }
  }
  
  clearFilters() {
    this.filters.category = '';
    this.filters.status = '';
    this.elements.categoryFilter.value = '';
    this.elements.statusFilter.value = '';
    this.applyFilters();
  }
  
  async showHistory(datasetId, datasetName) {
    this.elements.modalTitle.textContent = `Histórico: ${datasetName}`;
    this.elements.historyModal.dataset.datasetId = datasetId;
    this.showModal();
    await this.loadCurrentHistory();
  }
  
  async loadCurrentHistory() {
    const datasetId = this.elements.historyModal.dataset.datasetId;
    const hours = this.elements.historyPeriod.value;
    
    if (!datasetId) return;
    
    try {
      this.elements.historyContent.innerHTML = `
        <div class="loading-indicator">
          <div class="spinner"></div>
          <span>Cargando histórico...</span>
        </div>
      `;
      
      const response = await this.apiCall(`/datasets/${datasetId}/history?hours=${hours}`);
      const data = await response.json();
      
      if (response.ok) {
        this.displayHistory(data.history);
      } else {
        throw new Error(data.error || 'Error loading history');
      }
      
    } catch (error) {
      console.error('Error loading history:', error);
      this.elements.historyContent.innerHTML = `
        <div class="error">Error cargando histórico: ${error.message}</div>
      `;
    }
  }
  
  displayHistory(history) {
    if (!history || history.length === 0) {
      this.elements.historyContent.innerHTML = `
        <div class="no-data">
          <p>No hay datos históricos disponibles para el período seleccionado.</p>
        </div>
      `;
      return;
    }
    
    const table = document.createElement('table');
    table.className = 'table';
    table.innerHTML = `
      <thead>
        <tr>
          <th>Fecha/Hora</th>
          <th>Estado</th>
          <th>Latencia</th>
          <th>Código HTTP</th>
        </tr>
      </thead>
      <tbody>
        ${history.map(entry => `
          <tr>
            <td>${this.formatDate(entry.checked_at)}</td>
            <td>${this.createStatusBadge(entry.status)}</td>
            <td>${entry.latency_ms ? `${entry.latency_ms}ms` : '—'}</td>
            <td>${entry.http_code || entry.error || '—'}</td>
          </tr>
        `).join('')}
      </tbody>
    `;
    
    this.elements.historyContent.innerHTML = '';
    this.elements.historyContent.appendChild(table);
  }
  
  showModal() {
    this.elements.historyModal.classList.remove('hidden');
    this.elements.modalOverlay.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  }
  
  closeModal() {
    this.elements.historyModal.classList.add('hidden');
    this.elements.modalOverlay.classList.add('hidden');
    document.body.style.overflow = '';
  }
  
  updateStatsDisplay(stats) {
    this.elements.totalDatasets.textContent = stats.total_datasets || '—';
    this.elements.availableDatasets.textContent = stats.successful_checks || '—';
    this.elements.avgLatency.textContent = stats.avg_latency ? 
      `${Math.round(stats.avg_latency)}ms` : '—';
  }
  
  setupAutoRefresh() {
    if (this.autoRefreshTimer) {
      clearInterval(this.autoRefreshTimer);
      this.autoRefreshTimer = null;
    }
    
    const seconds = parseInt(this.elements.autoRefresh.value, 10);
    if (seconds > 0) {
      this.autoRefreshTimer = setInterval(() => {
        this.loadStatus();
        this.loadStats();
      }, seconds * 1000);
    }
  }
  
  async checkApiHealth() {
    try {
      const response = await this.apiCall('/health');
      if (response.ok) {
        this.updateApiStatus('connected');
      } else {
        this.updateApiStatus('error');
      }
    } catch (error) {
      this.updateApiStatus('error');
    }
  }
  
  updateApiStatus(status) {
    const statusMap = {
      'connected': { text: 'API Conectada', class: '' },
      'error': { text: 'API Desconectada', class: 'error' },
      'warning': { text: 'API Lenta', class: 'warning' }
    };
    
    const info = statusMap[status] || statusMap.error;
    this.elements.statusText.textContent = info.text;
    this.elements.statusIndicator.className = `status-indicator ${info.class}`;
  }
  
  updateLastUpdated(timestamp) {
    if (timestamp) {
      const date = new Date(timestamp);
      this.elements.lastUpdated.textContent = `Actualizado: ${this.formatDate(date)}`;
    }
  }
  
  async apiCall(endpoint, options = {}) {
    const url = `${this.API_BASE}${endpoint}`;
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
      }
    };
    
    return fetch(url, { ...defaultOptions, ...options });
  }
  
  setLoading(loading) {
    this.isLoading = loading;
    if (loading) {
      this.elements.loadingIndicator.classList.remove('hidden');
      this.elements.refreshBtn.disabled = true;
    } else {
      this.elements.loadingIndicator.classList.add('hidden');
      this.elements.refreshBtn.disabled = false;
    }
  }
  
  showError(message) {
    this.elements.error.textContent = message;
    this.elements.error.classList.remove('hidden');
    setTimeout(() => this.hideError(), 5000);
  }
  
  hideError() {
    this.elements.error.classList.add('hidden');
  }
  
  showSuccess(message) {
    // Crear notificación temporal de éxito
    const notification = document.createElement('div');
    notification.className = 'success-notification';
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: var(--success-bg);
      border: 1px solid var(--success-border);
      color: var(--success);
      padding: var(--spacing-md);
      border-radius: var(--radius-md);
      z-index: 1002;
      animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    setTimeout(() => {
      notification.remove();
    }, 3000);
  }
  
  showNoData() {
    this.elements.noData.classList.remove('hidden');
    this.elements.tbody.innerHTML = '';
  }
  
  formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('es-CL', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
  
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  // === MÉTODOS DE WEBSOCKETS Y NOTIFICACIONES ===
  
  initWebSocket() {
    try {
      // Inicializar socket.io
      this.socket = io(this.API_BASE);
      
      // Event listeners del socket
      this.socket.on('connect', () => {
        console.log('WebSocket conectado');
        this.isConnected = true;
        this.updateConnectionStatus(true);
      });
      
      this.socket.on('disconnect', () => {
        console.log('WebSocket desconectado');
        this.isConnected = false;
        this.updateConnectionStatus(false);
      });
      
      this.socket.on('connect_error', (error) => {
        console.error('Error de conexión WebSocket:', error);
        this.updateConnectionStatus(false);
      });
      
      // Eventos de notificaciones
      this.socket.on('new_notification', (data) => {
        this.handleNewNotification(data);
      });
      
      this.socket.on('recent_notifications', (data) => {
        this.handleRecentNotifications(data);
      });
      
      this.socket.on('notification_marked_read', (data) => {
        this.updateNotificationBadge(data.unread_count);
      });
      
      this.socket.on('notifications_cleared', () => {
        this.notifications = [];
        this.unreadCount = 0;
        this.updateNotificationBadge(0);
        if (this.isNotificationsModalOpen()) {
          this.renderNotifications();
        }
      });
      
      // Eventos de datos
      this.socket.on('dataset_update', (data) => {
        console.log('Dataset actualizado:', data);
        // Actualizar datos en tiempo real
        this.loadStatus();
        this.loadStats();
      });
      
      this.socket.on('stats_update', (data) => {
        this.updateStatsDisplay(data);
      });
      
    } catch (error) {
      console.error('Error inicializando WebSocket:', error);
      this.updateConnectionStatus(false);
    }
  }
  
  updateConnectionStatus(isConnected) {
    const indicator = this.elements.connectionStatus.querySelector('#statusIndicator');
    const text = this.elements.connectionStatus.querySelector('#statusText');
    
    if (isConnected) {
      indicator.className = 'status-indicator online';
      text.textContent = 'Conectado';
    } else {
      indicator.className = 'status-indicator offline';
      text.textContent = 'Desconectado';
    }
  }
  
  handleNewNotification(data) {
    const notification = data.notification;
    
    // Añadir a la lista local
    this.notifications.unshift(notification);
    
    // Actualizar badge
    this.updateNotificationBadge(data.unread_count);
    
    // Animación del botón
    this.elements.notificationBtn.classList.add('new-notification');
    setTimeout(() => {
      this.elements.notificationBtn.classList.remove('new-notification');
    }, 500);
    
    // Actualizar modal si está abierto
    if (this.isNotificationsModalOpen()) {
      this.renderNotifications();
    }
    
    console.log('Nueva notificación:', notification.title);
  }
  
  handleRecentNotifications(data) {
    this.notifications = data.notifications || [];
    this.updateNotificationBadge(data.unread_count || 0);
  }
  
  updateNotificationBadge(count) {
    this.unreadCount = count;
    this.elements.notificationBadge.textContent = count;
    
    if (count === 0) {
      this.elements.notificationBadge.classList.add('zero');
    } else {
      this.elements.notificationBadge.classList.remove('zero');
    }
  }
  
  showNotifications() {
    this.loadNotifications();
    this.elements.notificationsModal.classList.remove('hidden');
    this.elements.modalOverlay.classList.remove('hidden');
  }
  
  closeNotificationsModal() {
    this.elements.notificationsModal.classList.add('hidden');
    this.elements.modalOverlay.classList.add('hidden');
  }
  
  isNotificationsModalOpen() {
    return !this.elements.notificationsModal.classList.contains('hidden');
  }
  
  async loadNotifications() {
    try {
      const response = await this.apiCall('/api/notifications?limit=50');
      const data = await response.json();
      
      this.notifications = data.notifications || [];
      this.updateNotificationBadge(data.unread_count || 0);
      this.renderNotifications();
      
    } catch (error) {
      console.error('Error loading notifications:', error);
      this.elements.notificationsContent.innerHTML = `
        <div class="error">Error cargando notificaciones</div>
      `;
    }
  }
  
  renderNotifications() {
    const container = this.elements.notificationsContent;
    
    if (this.notifications.length === 0) {
      container.innerHTML = `
        <div class="no-notifications">
          <div class="no-notifications-icon">🔔</div>
          <p>No hay notificaciones</p>
        </div>
      `;
      return;
    }
    
    const notificationsHtml = this.notifications.map(notification => {
      const timeAgo = this.timeAgo(notification.timestamp);
      const isUnread = !notification.read;
      
      return `
        <div class="notification-item ${isUnread ? 'unread' : ''}" 
             onclick="app.markNotificationAsRead('${notification.id}')">
          <div class="notification-header">
            <h4 class="notification-title">${this.escapeHtml(notification.title)}</h4>
            <span class="notification-type ${notification.type}">${notification.type}</span>
          </div>
          <p class="notification-message">${this.escapeHtml(notification.message)}</p>
          <div class="notification-time">${timeAgo}</div>
        </div>
      `;
    }).join('');
    
    container.innerHTML = notificationsHtml;
  }
  
  async markNotificationAsRead(notificationId) {
    try {
      const response = await this.apiCall(`/api/notifications/${notificationId}/read`, {
        method: 'POST'
      });
      
      if (response.ok) {
        // Actualizar localmente
        const notification = this.notifications.find(n => n.id === notificationId);
        if (notification) {
          notification.read = true;
        }
        
        // Re-renderizar
        this.renderNotifications();
      }
      
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  }
  
  async clearNotifications() {
    try {
      const response = await this.apiCall('/api/notifications/clear', {
        method: 'POST'
      });
      
      if (response.ok) {
        this.notifications = [];
        this.updateNotificationBadge(0);
        this.renderNotifications();
      }
      
    } catch (error) {
      console.error('Error clearing notifications:', error);
    }
  }
  
  timeAgo(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now - time;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffMins < 1) return 'Ahora';
    if (diffMins < 60) return `Hace ${diffMins} min`;
    if (diffHours < 24) return `Hace ${diffHours}h`;
    if (diffDays < 7) return `Hace ${diffDays}d`;
    
    return time.toLocaleDateString('es-CL');
  }
}

// Agregar estilos para animaciones
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
  
  .btn-sm {
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
  }
  
  .category-tag {
    display: inline-block;
    padding: 0.125rem 0.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    color: var(--text-secondary);
    text-transform: capitalize;
  }
`;
document.head.appendChild(style);

// Inicializar aplicación
const app = new ChileDataApp();

// Primera carga
app.loadStatus();

// Auto-refresh inicial si está configurado
const initialRefresh = parseInt(app.elements.autoRefresh.value, 10);
if (initialRefresh > 0) {
  app.autoRefreshTimer = setInterval(() => {
    app.loadStatus();
    app.loadStats();
  }, initialRefresh * 1000);
}