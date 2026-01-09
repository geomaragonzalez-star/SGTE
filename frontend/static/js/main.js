// Helper para llamadas a la API
const api = {
    async get(url) {
        const response = await fetch(`/api${url}`);
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
            throw new Error(error.detail || 'Error en la petición');
        }
        return await response.json();
    },
    
    async post(url, data) {
        const response = await fetch(`/api${url}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
            throw new Error(error.detail || 'Error en la petición');
        }
        return await response.json();
    },
    
    async put(url, data) {
        const response = await fetch(`/api${url}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
            throw new Error(error.detail || 'Error en la petición');
        }
        return await response.json();
    },
    
    async delete(url) {
        const response = await fetch(`/api${url}`, {
            method: 'DELETE'
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
            throw new Error(error.detail || 'Error en la petición');
        }
        return await response.json();
    }
};

// Sidebar toggle funcional
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const collapseBtn = document.getElementById('sidebar-collapse-btn');
    const mobileToggle = document.getElementById('sidebar-toggle-mobile');
    
    // Estado del sidebar (guardado en localStorage)
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    
    // Aplicar estado inicial
    if (isCollapsed) {
        sidebar.classList.add('sidebar-collapsed');
        sidebar.classList.remove('sidebar-expanded');
        mainContent.classList.add('main-content-collapsed');
        mainContent.classList.remove('main-content-expanded');
    } else {
        sidebar.classList.add('sidebar-expanded');
        sidebar.classList.remove('sidebar-collapsed');
        mainContent.classList.add('main-content-expanded');
        mainContent.classList.remove('main-content-collapsed');
    }
    
    // Toggle desktop
    if (collapseBtn) {
        collapseBtn.addEventListener('click', () => {
            const isCurrentlyCollapsed = sidebar.classList.contains('sidebar-collapsed');
            
            if (isCurrentlyCollapsed) {
                // Expandir
                sidebar.classList.remove('sidebar-collapsed');
                sidebar.classList.add('sidebar-expanded');
                mainContent.classList.remove('main-content-collapsed');
                mainContent.classList.add('main-content-expanded');
                localStorage.setItem('sidebarCollapsed', 'false');
            } else {
                // Colapsar
                sidebar.classList.remove('sidebar-expanded');
                sidebar.classList.add('sidebar-collapsed');
                mainContent.classList.remove('main-content-expanded');
                mainContent.classList.add('main-content-collapsed');
                localStorage.setItem('sidebarCollapsed', 'true');
            }
        });
    }
    
    // Toggle móvil
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
        
        // Cerrar sidebar al hacer clic fuera (móvil)
        document.addEventListener('click', (event) => {
            if (window.innerWidth <= 1024) {
                if (!sidebar.contains(event.target) && !mobileToggle.contains(event.target)) {
                    sidebar.classList.remove('open');
                }
            }
        });
    }
});

// Exportar para uso global
window.api = api;

// Destacar opción activa del sidebar
document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-nav-link');
    
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('data-path');
        
        // Verificar si la ruta actual coincide o comienza con la ruta del enlace
        if (currentPath === linkPath || (linkPath !== '/' && currentPath.startsWith(linkPath))) {
            link.classList.add('active');
        }
    });
});
