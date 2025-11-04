/**
 * YOLO1125 管理者介面
 */

class AdminManager {
    constructor() {
        this.users = [];
        this.currentEditUser = null;
        this.currentDeleteUser = null;
        this.init();
    }

    async init() {
        await this.loadStats();
        await this.loadUsers();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // 重新載入按鈕
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.loadUsers();
            this.loadStats();
        });

        // 搜尋功能
        document.getElementById('search-input').addEventListener('input', (e) => {
            this.filterUsers(e.target.value);
        });

        // 編輯 Modal
        document.getElementById('close-edit-modal').addEventListener('click', () => {
            this.closeEditModal();
        });
        document.getElementById('cancel-edit-btn').addEventListener('click', () => {
            this.closeEditModal();
        });
        document.getElementById('save-edit-btn').addEventListener('click', () => {
            this.saveUser();
        });

        // 刪除 Modal
        document.getElementById('close-delete-modal').addEventListener('click', () => {
            this.closeDeleteModal();
        });
        document.getElementById('cancel-delete-btn').addEventListener('click', () => {
            this.closeDeleteModal();
        });
        document.getElementById('confirm-delete-btn').addEventListener('click', () => {
            this.confirmDelete();
        });
    }

    async loadStats() {
        try {
            const response = await fetch('/api/admin/stats');
            const data = await response.json();

            if (data.success) {
                document.getElementById('total-users').textContent = data.stats.total_users;
                document.getElementById('total-transactions').textContent = data.stats.total_transactions;
                document.getElementById('total-revenue').textContent = `NT$ ${data.stats.total_revenue.toLocaleString()}`;
            }
        } catch (error) {
            console.error('載入統計資料失敗:', error);
            this.showToast('載入統計資料失敗', 'error');
        }
    }

    async loadUsers() {
        try {
            const tbody = document.getElementById('users-table-body');
            tbody.innerHTML = '<tr><td colspan="8" class="loading-row"><div class="spinner"></div><p>載入中...</p></td></tr>';

            const response = await fetch('/api/admin/users');
            const data = await response.json();

            if (data.success) {
                this.users = data.users;
                this.renderUsers(this.users);
            }
        } catch (error) {
            console.error('載入使用者失敗:', error);
            this.showToast('載入使用者失敗', 'error');
            document.getElementById('users-table-body').innerHTML =
                '<tr><td colspan="8" class="error-row">載入失敗，請重試</td></tr>';
        }
    }

    renderUsers(users) {
        const tbody = document.getElementById('users-table-body');

        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="empty-row">尚無使用者</td></tr>';
            return;
        }

        tbody.innerHTML = users.map(user => `
            <tr data-user-id="${user.id}">
                <td>
                    ${user.avatar ?
                        `<img src="${user.avatar}" class="user-avatar-small" alt="${user.name}">` :
                        `<div class="user-avatar-placeholder">${user.name.charAt(0)}</div>`
                    }
                </td>
                <td>${this.escapeHtml(user.name)}</td>
                <td>${this.escapeHtml(user.phone)}</td>
                <td>${user.birthday ? this.formatDate(user.birthday, 'birthday') : '--'}</td>
                <td>${user.created_at ? this.formatDate(user.created_at) : '--'}</td>
                <td>${user.last_visit ? this.formatDate(user.last_visit) : '--'}</td>
                <td class="amount">NT$ ${user.total_spent.toLocaleString()}</td>
                <td class="actions">
                    <button class="btn-edit" onclick="adminManager.editUser('${user.id}')">
                        ✏️ 編輯
                    </button>
                    <button class="btn-delete" onclick="adminManager.deleteUser('${user.id}')">
                        🗑️ 刪除
                    </button>
                </td>
            </tr>
        `).join('');
    }

    filterUsers(searchTerm) {
        const filtered = this.users.filter(user =>
            user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            user.phone.includes(searchTerm)
        );
        this.renderUsers(filtered);
    }

    editUser(userId) {
        const user = this.users.find(u => u.id === userId);
        if (!user) return;

        this.currentEditUser = user;

        // 填充表單
        document.getElementById('edit-name').value = user.name;
        document.getElementById('edit-phone').value = user.phone;

        if (user.birthday) {
            try {
                const date = new Date(user.birthday);
                document.getElementById('edit-birthday').value = date.toISOString().split('T')[0];
            } catch (e) {
                document.getElementById('edit-birthday').value = '';
            }
        } else {
            document.getElementById('edit-birthday').value = '';
        }

        // 顯示 Modal
        document.getElementById('edit-modal').style.display = 'flex';
    }

    closeEditModal() {
        document.getElementById('edit-modal').style.display = 'none';
        this.currentEditUser = null;
    }

    async saveUser() {
        if (!this.currentEditUser) return;

        const name = document.getElementById('edit-name').value.trim();
        const phone = document.getElementById('edit-phone').value.trim();
        const birthday = document.getElementById('edit-birthday').value;

        if (!name || !phone) {
            this.showToast('請填寫完整資料', 'error');
            return;
        }

        try {
            const response = await fetch(`/api/admin/user/${this.currentEditUser.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, phone, birthday })
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('使用者資訊已更新', 'success');
                this.closeEditModal();
                await this.loadUsers();
            } else {
                this.showToast(data.message || '更新失敗', 'error');
            }
        } catch (error) {
            console.error('更新使用者失敗:', error);
            this.showToast('更新失敗，請重試', 'error');
        }
    }

    deleteUser(userId) {
        const user = this.users.find(u => u.id === userId);
        if (!user) return;

        this.currentDeleteUser = user;

        // 填充確認資訊
        document.getElementById('delete-user-name').textContent = user.name;
        document.getElementById('delete-user-phone').textContent = user.phone;

        // 顯示 Modal
        document.getElementById('delete-modal').style.display = 'flex';
    }

    closeDeleteModal() {
        document.getElementById('delete-modal').style.display = 'none';
        this.currentDeleteUser = null;
    }

    async confirmDelete() {
        if (!this.currentDeleteUser) return;

        try {
            const response = await fetch(`/api/admin/user/${this.currentDeleteUser.id}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('使用者已刪除', 'success');
                this.closeDeleteModal();
                await this.loadUsers();
                await this.loadStats();
            } else {
                this.showToast(data.message || '刪除失敗', 'error');
            }
        } catch (error) {
            console.error('刪除使用者失敗:', error);
            this.showToast('刪除失敗，請重試', 'error');
        }
    }

    formatDate(dateString, type = 'datetime') {
        try {
            const date = new Date(dateString);
            if (type === 'birthday') {
                return `${date.getMonth() + 1}/${date.getDate()}`;
            }
            return date.toLocaleString('zh-TW');
        } catch (e) {
            return '--';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;

        const container = document.getElementById('toast-container');
        container.appendChild(toast);

        setTimeout(() => toast.classList.add('show'), 10);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// 初始化
let adminManager;
document.addEventListener('DOMContentLoaded', () => {
    adminManager = new AdminManager();
});
