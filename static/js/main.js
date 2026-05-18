/**
 * 图书馆管理系统 - 通用 JavaScript
 */

// Toast 提示
function showToast(message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 2500);
}

// 模态框管理
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'flex';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// 点击遮罩关闭模态框
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.style.display = 'none';
    }
});

// 侧边栏切换（移动端）
function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('open');
}

// 格式化日期
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 退出登录
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
    html += `<button ${currentPage === 1 ? 'disabled' : ''} onclick="event.preventDefault(); arguments[0](${currentPage - 1})" data-page="${currentPage - 1}">&laquo; 上一页</button>`;

    const maxButtons = 5;
    let start = Math.max(1, currentPage - 2);
    let end = Math.min(totalPages, start + maxButtons - 1);
    start = Math.max(1, end - maxButtons + 1);

    for (let i = start; i <= end; i++) {
        html += `<button class="${i === currentPage ? 'active' : ''}" onclick="event.preventDefault(); arguments[0](${i})" data-page="${i}">${i}</button>`;
    }

    html += `<button ${currentPage === totalPages ? 'disabled' : ''} onclick="event.preventDefault(); arguments[0](${currentPage + 1})" data-page="${currentPage + 1}">下一页 &raquo;</button>`;
    html += `<span class="page-info">共 ${total} 条 / ${totalPages} 页</span>`;
    html += '</div>';

    container.innerHTML = html;

    // 绑定事件
    container.querySelectorAll('button[data-page]').forEach(btn => {
        btn.onclick = () => {
            const page = parseInt(btn.dataset.page);
            onPageChange(page);
        };
    });
}

// ==================== 工具函数 ====================

// 防抖
function debounce(fn, delay) {
    let timer;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

// HTML 转义
function esc(s) {
    if (!s) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// AJAX 请求封装
async function api(url, options = {}) {
    const config = {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    };

    const response = await fetch(url, config);
    const data = await response.json();

    if (response.status === 401) {
        window.location.href = '/login';
        return;
    }

    return data;
}
