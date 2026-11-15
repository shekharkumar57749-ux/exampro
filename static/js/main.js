/**
 * ExamPro - Advanced Examination Management System
 * Core UI Logic, Theme System, Toasts, and Notifications
 */

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initSidebar();
    initNotifications();
    initUserDropdown();
    initAnimatedCounters();
});

/* ========================================================
   Theme Toggle System (Light / Dark)
   ======================================================== */
function initTheme() {
    const savedTheme = localStorage.getItem('exampro_theme') || 'light';
    setTheme(savedTheme);

    const toggleBtns = document.querySelectorAll('.theme-toggle-btn');
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            setTheme(newTheme);
        });
    });
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('exampro_theme', theme);
    
    // Update icons
    const icons = document.querySelectorAll('.theme-toggle-btn i');
    icons.forEach(icon => {
        if (theme === 'dark') {
            icon.className = 'fas fa-sun';
        } else {
            icon.className = 'fas fa-moon';
        }
    });
}

/* ========================================================
   Sidebar Collapse & Mobile Drawer
   ======================================================== */
function initSidebar() {
    const sidebar = document.querySelector('.app-sidebar');
    const collapseBtn = document.querySelector('.sidebar-collapse-btn');
    const mobileBtn = document.querySelector('.mobile-menu-btn');

    if (collapseBtn && sidebar) {
        collapseBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('exampro_sidebar_collapsed', sidebar.classList.contains('collapsed'));
        });

        // Restore collapse state on desktop
        if (localStorage.getItem('exampro_sidebar_collapsed') === 'true' && window.innerWidth > 1024) {
            sidebar.classList.add('collapsed');
        }
    }

    if (mobileBtn && sidebar) {
        mobileBtn.addEventListener('click', () => {
            sidebar.classList.toggle('mobile-open');
        });

        // Close on clicking outside
        document.addEventListener('click', (e) => {
            if (sidebar.classList.contains('mobile-open') && !sidebar.contains(e.target) && !mobileBtn.contains(e.target)) {
                sidebar.classList.remove('mobile-open');
            }
        });
    }
}

/* ========================================================
   Notifications Dropdown & Mark as Read
   ======================================================== */
function initNotifications() {
    const notifBtn = document.querySelector('.notification-bell-btn');
    const notifDropdown = document.querySelector('.notification-dropdown');

    if (notifBtn && notifDropdown) {
        notifBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            notifDropdown.classList.toggle('active');
            if (notifDropdown.classList.contains('active')) {
                loadNotifications();
            }
        });

        document.addEventListener('click', (e) => {
            if (!notifDropdown.contains(e.target) && !notifBtn.contains(e.target)) {
                notifDropdown.classList.remove('active');
            }
        });
    }
}

async function loadNotifications() {
    try {
        const res = await fetch('/api/notifications');
        const data = await res.json();
        if (data.success) {
            const listContainer = document.querySelector('.notif-list');
            const badge = document.querySelector('.notification-badge');
            
            if (badge) {
                badge.textContent = data.unread_count;
                badge.style.display = data.unread_count > 0 ? 'flex' : 'none';
            }

            if (listContainer) {
                if (!data.notifications || data.notifications.length === 0) {
                    listContainer.innerHTML = '<li style="padding:1.5rem; text-align:center; color:var(--text-muted);">No new notifications</li>';
                    return;
                }

                listContainer.innerHTML = data.notifications.map(n => `
                    <li class="notif-item ${n.is_read ? '' : 'unread'}" onclick="markNotificationRead(${n.id}, '${n.link || '#'}')">
                        <i class="fas ${getNotifIcon(n.type)}" style="color:var(--primary); margin-top:2px;"></i>
                        <div>
                            <div style="font-weight:600; color:var(--text-main);">${escapeHtml(n.title)}</div>
                            <div style="font-size:0.8rem; color:var(--text-muted);">${escapeHtml(n.message)}</div>
                        </div>
                    </li>
                `).join('');
            }
        }
    } catch (e) {
        console.error('Failed to load notifications:', e);
    }
}

function getNotifIcon(type) {
    switch (type) {
        case 'success': return 'fa-check-circle';
        case 'warning': return 'fa-exclamation-triangle';
        case 'exam': return 'fa-file-alt';
        default: return 'fa-info-circle';
    }
}

async function markNotificationRead(id, link) {
    try {
        await fetch(`/api/notifications/${id}/read`, { method: 'POST' });
        if (link && link !== '#') {
            window.location.href = link;
        } else {
            loadNotifications();
        }
    } catch (e) {
        console.error(e);
    }
}

/* ========================================================
   User Dropdown Menu
   ======================================================== */
function initUserDropdown() {
    const userMenuBtn = document.querySelector('.user-menu-btn');
    const userDropdown = document.querySelector('.user-dropdown');

    if (userMenuBtn && userDropdown) {
        userMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdown.classList.toggle('active');
        });

        document.addEventListener('click', (e) => {
            if (!userDropdown.contains(e.target) && !userMenuBtn.contains(e.target)) {
                userDropdown.classList.remove('active');
            }
        });
    }
}

/* ========================================================
   Toast Notification System
   ======================================================== */
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let icon = 'fa-info-circle';
    if (type === 'success') icon = 'fa-check-circle';
    if (type === 'danger') icon = 'fa-times-circle';
    if (type === 'warning') icon = 'fa-exclamation-triangle';

    toast.innerHTML = `
        <i class="fas ${icon}" style="font-size:1.2rem; color:var(--${type === 'danger' ? 'danger' : (type === 'success' ? 'success' : 'primary')});"></i>
        <div style="flex:1;">${escapeHtml(message)}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

/* ========================================================
   Modal Dialog Controls
   ======================================================== */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

/* ========================================================
   Animated Counters
   ======================================================== */
function initAnimatedCounters() {
    const counters = document.querySelectorAll('.counter-val');
    counters.forEach(counter => {
        const target = +counter.getAttribute('data-target') || 0;
        let count = 0;
        const speed = target / 40;

        const updateCount = () => {
            count += speed;
            if (count < target) {
                counter.innerText = Math.ceil(count).toLocaleString();
                requestAnimationFrame(updateCount);
            } else {
                counter.innerText = target.toLocaleString();
            }
        };
        updateCount();
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.innerText = text;
    return div.innerHTML;
}

