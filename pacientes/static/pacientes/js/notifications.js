(function() {
    'use strict';
    
    const bellIcon = document.getElementById('bell-icon');
    const notificationBadge = document.getElementById('notification-count');
    const notificationDropdown = document.getElementById('notification-dropdown');
    const notificationList = document.getElementById('notification-list');
    const markAllReadBtn = document.getElementById('mark-all-read');
    
    let isDropdownOpen = false;
    
    // ========== FUNCIONES PRINCIPALES ==========
    
    /**
     * Cargar el contador de notificaciones
     */
    function loadNotificationCount() {
        fetch('/pacientes/notifications/count/')
            .then(response => response.json())
            .then(data => {
                updateBadge(data.count);
            })
            .catch(error => console.error('Error al cargar contador:', error));
    }
    
    /**
     * Actualizar el badge con el número de notificaciones
     */
    function updateBadge(count) {
        if (count > 0) {
            notificationBadge.textContent = count > 99 ? '99+' : count;
            notificationBadge.style.display = 'flex';
        } else {
            notificationBadge.style.display = 'none';
        }
    }
    
    /**
     * Cargar lista completa de notificaciones
     */
    function loadNotifications() {
        notificationList.innerHTML = '<div class="notification-loading"><i class="bx bx-loader-alt bx-spin"></i> Cargando...</div>';
        
        fetch('/pacientes/notifications/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderNotifications(data.notifications);
                    updateBadge(data.count);
                }
            })
            .catch(error => {
                console.error('Error al cargar notificaciones:', error);
                notificationList.innerHTML = '<div class="notification-empty"><i class="bx bx-error-circle"></i><p>Error al cargar notificaciones</p></div>';
            });
    }
    
    /**
     * Renderizar las notificaciones en el dropdown
     */
    function renderNotifications(notifications) {
        if (notifications.length === 0) {
            notificationList.innerHTML = `
                <div class="notification-empty">
                    <i class='bx bx-bell-off'></i>
                    <p>No hay notificaciones nuevas</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        notifications.forEach(notif => {
            const icon = getNotificationIcon(notif.type);
            const timeAgo = formatTimeAgo(notif.created_at);
            
            html += `
                <div class="notification-item unread" data-id="${notif.id}" data-url="${notif.url}">
                    <div class="notification-icon ${icon.class}">
                        <i class='bx ${icon.icon}'></i>
                    </div>
                    <div class="notification-content">
                        <div class="notification-title">${notif.title}</div>
                        <div class="notification-message">${notif.message}</div>
                        <div class="notification-time">${timeAgo}</div>
                    </div>
                </div>
            `;
        });
        
        notificationList.innerHTML = html;
        
        // Agregar eventos de click a cada notificación
        document.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', () => handleNotificationClick(item));
        });
    }
    
    /**
     * Obtener el icono según el tipo de notificación
     */
    function getNotificationIcon(type) {
        const icons = {
            'session_reminder': { icon: 'bx-calendar-check', class: 'session' },
            'session_tomorrow': { icon: 'bx-calendar-event', class: 'session' },
            'payment_overdue': { icon: 'bx-money', class: 'payment' },
            'expense_due': { icon: 'bx-receipt', class: 'expense' },
            'expense_overdue': { icon: 'bx-error-circle', class: 'expense' }
        };
        return icons[type] || { icon: 'bx-bell', class: 'session' };
    }
    
    /**
     * Formatear el tiempo transcurrido
     */
    function formatTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);
        
        if (seconds < 60) return 'Hace un momento';
        if (seconds < 3600) return `Hace ${Math.floor(seconds / 60)} min`;
        if (seconds < 86400) return `Hace ${Math.floor(seconds / 3600)} h`;
        if (seconds < 604800) return `Hace ${Math.floor(seconds / 86400)} días`;
        
        return date.toLocaleDateString('es-PE', { day: '2-digit', month: 'short' });
    }
    
    /**
     * Manejar click en una notificación
     */
    function handleNotificationClick(item) {
        const notificationId = item.dataset.id;
        const url = item.dataset.url;
        
        // Marcar como leída
        fetch(`/pacientes/notifications/${notificationId}/read/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                item.classList.remove('unread');
                loadNotificationCount(); // Actualizar contador
                
                // Redirigir a la URL de la notificación
                if (url && url !== '#') {
                    window.location.href = url;
                }
            }
        })
        .catch(error => console.error('Error al marcar como leída:', error));
        
        closeDropdown();
    }
    
    /**
     * Marcar todas como leídas
     */
    function markAllAsRead() {
        fetch('/pacientes/notifications/read-all/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateBadge(0);
                loadNotifications(); 
            }
        })
        .catch(error => console.error('Error al marcar todas como leídas:', error));
    }
    
    /**
     * Toggle del dropdown
     */
    function toggleDropdown() {
        isDropdownOpen = !isDropdownOpen;
        
        if (isDropdownOpen) {
            notificationDropdown.classList.add('show');
            loadNotifications(); // Cargar notificaciones al abrir
        } else {
            notificationDropdown.classList.remove('show');
        }
    }
    
    function closeDropdown() {
        isDropdownOpen = false;
        notificationDropdown.classList.remove('show');
    }
    
    /**
     * Obtener CSRF token de las cookies
     */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // ========== EVENT ==========
    
    // Click en la campana
    bellIcon.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown();
    });
    
    // Click en marcar todas como leídas
    markAllReadBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        markAllAsRead();
    });
    
    // Cerrar dropdown al hacer click fuera
    document.addEventListener('click', (e) => {
        if (isDropdownOpen && !notificationDropdown.contains(e.target)) {
            closeDropdown();
        }
    });
    
    // Prevenir que clicks dentro del dropdown lo cierren
    notificationDropdown.addEventListener('click', (e) => {
        e.stopPropagation();
    });
    
    // Cargar contador al cargar la página
    loadNotificationCount();
    
    // Actualizar contador cada 30 segundos
    setInterval(loadNotificationCount, 30000);
    
    // Polling: recargar notificaciones cada 2 minutos si el dropdown está abierto
    setInterval(() => {
        if (isDropdownOpen) {
            loadNotifications();
        }
    }, 120000);
    
})();