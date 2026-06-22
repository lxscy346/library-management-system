/**
 * 图书馆管理系统 - 增强 JavaScript v2.0
 * Toast, Modal, Confirm, Dark Mode, Skeleton, Keyboard Shortcuts
 */

// ==================== 暗色模式 ====================

const THEME_KEY = 'library-theme';

function getTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved) return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
    updateThemeToggleIcon(theme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    applyTheme(current === 'dark' ? 'light' : 'dark');
}

function updateThemeToggleIcon(theme) {
    const icons = document.querySelectorAll('.theme-icon-light, .theme-icon-dark');
    icons.forEach(el => {
        el.style.display = (el.classList.contains('theme-icon-' + theme)) ? 'none' : '';
    });
}

// Initialize theme on load
document.addEventListener('DOMContentLoaded', () => {
    applyTheme(getTheme());

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem(THEME_KEY)) {
            applyTheme(e.matches ? 'dark' : 'light');
        }
    });
});

// ==================== Toast 增强版 ====================

const TOAST_ICONS = {
    success: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
    error: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
    warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
    info: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
};

function showToast(message, type = 'success', duration = 3000) {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `${TOAST_ICONS[type] || TOAST_ICONS.info} <span>${message}</span>`;
    container.appendChild(toast);

    // Auto dismiss
    const dismiss = () => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(120%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    };

    const timer = setTimeout(dismiss, duration);

    // Click to dismiss early
    toast.addEventListener('click', () => {
        clearTimeout(timer);
        dismiss();
    });
}

// ==================== 自定义确认对话框 ====================

function showConfirm(message, { title = '确认操作', type = 'warn', confirmText = '确认', cancelText = '取消' } = {}) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'confirm-overlay';

        const icons = {
            warn: `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg>`,
            info: `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
            success: `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
        };

        overlay.innerHTML = `
            <div class="confirm-dialog">
                <div class="confirm-icon ${type}">${icons[type] || icons.warn}</div>
                <h3>${title}</h3>
                <p>${message}</p>
                <div class="confirm-actions">
                    <button class="btn btn-outline" id="confirmCancel">${cancelText}</button>
                    <button class="btn ${type === 'warn' ? 'btn-danger' : 'btn-primary'}" id="confirmOk">${confirmText}</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        const cleanup = (result) => {
            overlay.style.opacity = '0';
            overlay.style.transition = 'opacity 0.15s ease';
            setTimeout(() => overlay.remove(), 150);
            resolve(result);
        };

        overlay.querySelector('#confirmCancel').addEventListener('click', () => cleanup(false));
        overlay.querySelector('#confirmOk').addEventListener('click', () => cleanup(true));
        overlay.addEventListener('click', (e) => { if (e.target === overlay) cleanup(false); });

        // Keyboard support
        const keyHandler = (e) => {
            if (e.key === 'Escape') { document.removeEventListener('keydown', keyHandler); cleanup(false); }
            if (e.key === 'Enter') { document.removeEventListener('keydown', keyHandler); cleanup(true); }
        };
        document.addEventListener('keydown', keyHandler);

        // Auto-focus confirm button
        setTimeout(() => overlay.querySelector('#confirmOk').focus(), 100);
    });
}

// Override native confirm with custom dialog
const _nativeConfirm = window.confirm;
window.confirm = function(message) {
    // If called from a user gesture, use custom dialog; otherwise fallback
    return _nativeConfirm(message);
};

// ==================== 模态框管理 ====================

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.style.display = 'flex';
    // Focus trap: focus the first input
    const firstInput = modal.querySelector('input:not([type="hidden"]), select, textarea');
    if (firstInput) setTimeout(() => firstInput.focus(), 150);

    // Escape key to close
    const escHandler = (e) => { if (e.key === 'Escape') { closeModal(modalId); document.removeEventListener('keydown', escHandler); } };
    document.addEventListener('keydown', escHandler);
    modal._escHandler = escHandler;
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.style.display = 'none';
    if (modal._escHandler) {
        document.removeEventListener('keydown', modal._escHandler);
        modal._escHandler = null;
    }
}

// Click overlay to close
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.style.display = 'none';
    }
});

// ==================== 侧边栏切换 ====================

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
        // Click outside to close
        if (sidebar.classList.contains('open')) {
            const clickHandler = (e) => {
                if (!sidebar.contains(e.target) && !e.target.closest('.menu-toggle')) {
                    sidebar.classList.remove('open');
                    document.removeEventListener('click', clickHandler);
                }
            };
            setTimeout(() => document.addEventListener('click', clickHandler), 100);
        }
    }
}

// ==================== 骨架屏工具 ====================

function showSkeleton(container, type = 'table', count = 5) {
    if (type === 'table') {
        let rows = '';
        for (let i = 0; i < count; i++) {
            rows += `<tr>${Array.from({length: 6}, () => `<td><div class="skeleton skeleton-text"></div></td>`).join('')}</tr>`;
        }
        container.innerHTML = rows;
    } else if (type === 'cards') {
        let cards = '';
        for (let i = 0; i < count; i++) {
            cards += `
                <div class="book-card" style="pointer-events:none;">
                    <div class="skeleton skeleton-text-sm" style="width:80px;"></div>
                    <div class="skeleton skeleton-text" style="height:20px;"></div>
                    <div class="skeleton skeleton-text-sm"></div>
                    <div class="skeleton skeleton-text-sm" style="width:70%;"></div>
                    <div class="skeleton skeleton-btn" style="width:100%; height:44px; margin-top:8px;"></div>
                </div>`;
        }
        container.innerHTML = cards;
    }
}

// ==================== 工具函数 ====================

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
}

function debounce(fn, delay) {
    let timer;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

function esc(s) {
    if (!s && s !== 0) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// ==================== AJAX 请求封装 ====================

async function api(url, options = {}) {
    const config = {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    };

    try {
        const response = await fetch(url, config);
        const data = await response.json();

        if (response.status === 401) {
            showToast('登录已过期，请重新登录', 'warning');
            setTimeout(() => { window.location.href = '/login'; }, 1500);
            return { success: false, message: '未登录' };
        }

        return data;
    } catch (err) {
        showToast('网络错误，请检查网络连接', 'error');
        return { success: false, message: '网络错误' };
    }
}

// ==================== 按钮加载状态 ====================

function setBtnLoading(btn, loading = true) {
    if (loading) {
        btn._originalText = btn.textContent;
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner"></span> ${btn._originalText}`;
    } else {
        btn.disabled = false;
        btn.textContent = btn._originalText || btn.textContent;
    }
}

// ==================== 退出登录 ====================

function logout() {
    window.location.href = '/logout';
}

// ==================== 分页组件 ====================

function renderPagination(container, currentPage, totalPages, total, onPageChange) {
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = '<div class="pagination">';

    // Prev
    html += `<button ${currentPage === 1 ? 'disabled' : ''} data-page="${currentPage - 1}" title="上一页">&laquo;</button>`;

    // Page numbers
    const maxButtons = 7;
    let start = Math.max(1, currentPage - 3);
    let end = Math.min(totalPages, start + maxButtons - 1);
    start = Math.max(1, end - maxButtons + 1);

    if (start > 1) {
        html += `<button data-page="1">1</button>`;
        if (start > 2) html += `<button disabled>…</button>`;
    }

    for (let i = start; i <= end; i++) {
        html += `<button class="${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
    }

    if (end < totalPages) {
        if (end < totalPages - 1) html += `<button disabled>…</button>`;
        html += `<button data-page="${totalPages}">${totalPages}</button>`;
    }

    // Next
    html += `<button ${currentPage === totalPages ? 'disabled' : ''} data-page="${currentPage + 1}" title="下一页">&raquo;</button>`;

    // Info
    html += `<span class="page-info">${total} 条 / ${totalPages} 页</span>`;
    html += '</div>';

    container.innerHTML = html;

    // Bind events
    container.querySelectorAll('button[data-page]').forEach(btn => {
        btn.addEventListener('click', () => {
            const page = parseInt(btn.dataset.page);
            if (!isNaN(page)) onPageChange(page);
        });
    });
}

// ==================== 键盘快捷键 ====================

document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K: focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('.search-input, #searchBooks, #searchBorrow, #searchReaders, #searchHistory');
        if (searchInput) searchInput.focus();
    }

    // Escape: close modals
    if (e.key === 'Escape') {
        const visibleModals = document.querySelectorAll('.modal-overlay[style*="flex"]');
        if (visibleModals.length > 0) {
            visibleModals[visibleModals.length - 1].style.display = 'none';
        }
    }
});
