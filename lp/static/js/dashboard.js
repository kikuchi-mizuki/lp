// 管理ダッシュボード JavaScript
class DashboardManager {
    constructor() {
        this.baseUrl = window.location.origin;
        this.authToken = localStorage.getItem('auth_token');
        this.charts = {};
        this.refreshInterval = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboard();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // ナビゲーション
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const target = e.target.getAttribute('data-target');
                this.showSection(target);
            });
        });

        // リフレッシュボタン
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadDashboard();
            });
        }

        // ログアウトボタン
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                this.logout();
            });
        }

        // 検索機能
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterData(e.target.value);
            });
        }

        // 日付フィルター
        const dateFilter = document.getElementById('date-filter');
        if (dateFilter) {
            dateFilter.addEventListener('change', (e) => {
                this.filterByDate(e.target.value);
            });
        }
    }

    async loadDashboard() {
        try {
            this.showLoading();
            
            // 概要統計を取得
            const overview = await this.fetchData('/api/v1/dashboard/overview');
            this.updateOverviewCards(overview);

            // 企業一覧を取得
            const companies = await this.fetchData('/api/v1/companies');
            this.updateCompaniesTable(companies);

            // チャートを更新
            await this.updateCharts();

            // 最新のアクティビティを取得
            const activities = await this.fetchRecentActivities();
            this.updateActivityFeed(activities);

            this.hideLoading();
        } catch (error) {
            console.error('ダッシュボード読み込みエラー:', error);
            this.showError('ダッシュボードの読み込みに失敗しました');
        }
    }

    async fetchData(endpoint, options = {}) {
        const url = this.baseUrl + endpoint;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...(this.authToken && { 'Authorization': `Bearer ${this.authToken}` })
            },
            ...options
        };

        const response = await fetch(url, config);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    updateOverviewCards(data) {
        if (!data.success) return;

        const stats = data.statistics;
        
        // 統計カードを更新
        this.updateCard('total-companies', stats.total_companies);
        this.updateCard('active-subscriptions', stats.active_subscriptions);
        this.updateCard('total-revenue', `¥${stats.total_revenue.toLocaleString()}`);
        this.updateCard('pending-cancellations', stats.pending_cancellations);
        this.updateCard('trial-users', stats.trial_users);
        this.updateCard('monthly-growth', `${stats.monthly_growth}%`);
    }

    updateCard(cardId, value) {
        const card = document.getElementById(cardId);
        if (card) {
            const valueElement = card.querySelector('.card-value');
            if (valueElement) {
                valueElement.textContent = value;
            }
        }
    }

    updateCompaniesTable(data) {
        if (!data.success) return;

        const tableBody = document.getElementById('companies-table-body');
        if (!tableBody) return;

        tableBody.innerHTML = '';

        data.companies.forEach(company => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${company.name}</td>
                <td>${company.industry || '未設定'}</td>
                <td>${company.employee_count || '未設定'}</td>
                <td>
                    <span class="badge ${this.getStatusBadgeClass(company.status)}">
                        ${this.getStatusText(company.status)}
                    </span>
                </td>
                <td>${company.created_at ? new Date(company.created_at).toLocaleDateString('ja-JP') : '未設定'}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="dashboard.viewCompany(${company.id})">
                        詳細
                    </button>
                    <button class="btn btn-sm btn-warning" onclick="dashboard.editCompany(${company.id})">
                        編集
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        });
    }

    getStatusBadgeClass(status) {
        const statusClasses = {
            'active': 'bg-success',
            'trial': 'bg-warning',
            'cancelled': 'bg-danger',
            'pending': 'bg-info'
        };
        return statusClasses[status] || 'bg-secondary';
    }

    getStatusText(status) {
        const statusTexts = {
            'active': 'アクティブ',
            'trial': 'トライアル',
            'cancelled': '解約済み',
            'pending': '保留中'
        };
        return statusTexts[status] || '不明';
    }

    async updateCharts() {
        try {
            // 収益チャート
            const revenueData = await this.fetchData('/api/v1/dashboard/revenue');
            this.updateRevenueChart(revenueData);

            // 解約率チャート
            const cancellationData = await this.fetchData('/api/v1/dashboard/cancellation');
            this.updateCancellationChart(cancellationData);

            // 通知統計チャート
            const notificationData = await this.fetchData('/api/v1/dashboard/notification');
            this.updateNotificationChart(notificationData);

        } catch (error) {
            console.error('チャート更新エラー:', error);
        }
    }

    updateRevenueChart(data) {
        if (!data.success) return;

        const ctx = document.getElementById('revenue-chart');
        if (!ctx) return;

        if (this.charts.revenue) {
            this.charts.revenue.destroy();
        }

        const chartData = {
            labels: data.monthly_revenue.map(item => item.month),
            datasets: [{
                label: '月次収益',
                data: data.monthly_revenue.map(item => item.revenue),
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1
            }]
        };

        this.charts.revenue = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: '月次収益推移'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '¥' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    updateCancellationChart(data) {
        if (!data.success) return;

        const ctx = document.getElementById('cancellation-chart');
        if (!ctx) return;

        if (this.charts.cancellation) {
            this.charts.cancellation.destroy();
        }

        const chartData = {
            labels: data.monthly_cancellations.map(item => item.month),
            datasets: [{
                label: '解約率',
                data: data.monthly_cancellations.map(item => item.cancellation_rate),
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                tension: 0.1
            }]
        };

        this.charts.cancellation = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: '月次解約率推移'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    updateNotificationChart(data) {
        if (!data.success) return;

        const ctx = document.getElementById('notification-chart');
        if (!ctx) return;

        if (this.charts.notification) {
            this.charts.notification.destroy();
        }

        const chartData = {
            labels: data.daily_notifications.map(item => item.date),
            datasets: [{
                label: '通知送信数',
                data: data.daily_notifications.map(item => item.count),
                borderColor: 'rgb(54, 162, 235)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                tension: 0.1
            }]
        };

        this.charts.notification = new Chart(ctx, {
            type: 'bar',
            data: chartData,
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: '日次通知送信数'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    async fetchRecentActivities() {
        try {
            const activities = await this.fetchData('/api/v1/dashboard/activities');
            return activities.success ? activities.activities : [];
        } catch (error) {
            console.error('アクティビティ取得エラー:', error);
            return [];
        }
    }

    updateActivityFeed(activities) {
        const feedContainer = document.getElementById('activity-feed');
        if (!feedContainer) return;

        feedContainer.innerHTML = '';

        activities.forEach(activity => {
            const activityItem = document.createElement('div');
            activityItem.className = 'activity-item';
            activityItem.innerHTML = `
                <div class="activity-icon ${this.getActivityIconClass(activity.type)}">
                    <i class="${this.getActivityIcon(activity.type)}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">${activity.title}</div>
                    <div class="activity-description">${activity.description}</div>
                    <div class="activity-time">${new Date(activity.timestamp).toLocaleString('ja-JP')}</div>
                </div>
            `;
            feedContainer.appendChild(activityItem);
        });
    }

    getActivityIconClass(type) {
        const iconClasses = {
            'company_created': 'bg-success',
            'company_updated': 'bg-info',
            'company_cancelled': 'bg-warning',
            'payment_success': 'bg-success',
            'payment_failed': 'bg-danger',
            'notification_sent': 'bg-primary'
        };
        return iconClasses[type] || 'bg-secondary';
    }

    getActivityIcon(type) {
        const icons = {
            'company_created': 'fas fa-building',
            'company_updated': 'fas fa-edit',
            'company_cancelled': 'fas fa-times',
            'payment_success': 'fas fa-check',
            'payment_failed': 'fas fa-exclamation-triangle',
            'notification_sent': 'fas fa-bell'
        };
        return icons[type] || 'fas fa-info';
    }

    showSection(sectionId) {
        // すべてのセクションを非表示
        document.querySelectorAll('.dashboard-section').forEach(section => {
            section.style.display = 'none';
        });

        // 選択されたセクションを表示
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.style.display = 'block';
        }

        // ナビゲーションのアクティブ状態を更新
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        const activeLink = document.querySelector(`[data-target="${sectionId}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }
    }

    filterData(searchTerm) {
        const rows = document.querySelectorAll('#companies-table-body tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const matches = text.includes(searchTerm.toLowerCase());
            row.style.display = matches ? '' : 'none';
        });
    }

    filterByDate(dateRange) {
        // 日付フィルターの実装
        console.log('日付フィルター:', dateRange);
    }

    viewCompany(companyId) {
        // 企業詳細モーダルを表示
        this.showCompanyModal(companyId);
    }

    editCompany(companyId) {
        // 企業編集モーダルを表示
        this.showEditCompanyModal(companyId);
    }

    async showCompanyModal(companyId) {
        try {
            const company = await this.fetchData(`/api/v1/companies/${companyId}`);
            
            if (company.success) {
                this.displayCompanyDetails(company.company);
            }
        } catch (error) {
            console.error('企業詳細取得エラー:', error);
            this.showError('企業詳細の取得に失敗しました');
        }
    }

    displayCompanyDetails(company) {
        const modal = document.getElementById('company-modal');
        if (!modal) return;

        // モーダル内容を更新
        modal.querySelector('.modal-title').textContent = company.name;
        modal.querySelector('#company-id').textContent = company.id;
        modal.querySelector('#company-name').textContent = company.name;
        modal.querySelector('#company-industry').textContent = company.industry || '未設定';
        modal.querySelector('#company-employees').textContent = company.employee_count || '未設定';
        modal.querySelector('#company-status').textContent = this.getStatusText(company.status);
        modal.querySelector('#company-created').textContent = company.created_at ? 
            new Date(company.created_at).toLocaleDateString('ja-JP') : '未設定';

        // モーダルを表示
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }

    showEditCompanyModal(companyId) {
        // 企業編集モーダルの実装
        console.log('企業編集:', companyId);
    }

    startAutoRefresh() {
        // 5分ごとに自動更新
        this.refreshInterval = setInterval(() => {
            this.loadDashboard();
        }, 5 * 60 * 1000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    showLoading() {
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.style.display = 'block';
        }
    }

    hideLoading() {
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }

    showError(message) {
        const alertContainer = document.getElementById('alert-container');
        if (alertContainer) {
            const alert = document.createElement('div');
            alert.className = 'alert alert-danger alert-dismissible fade show';
            alert.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            alertContainer.appendChild(alert);

            // 5秒後に自動削除
            setTimeout(() => {
                alert.remove();
            }, 5000);
        }
    }

    showSuccess(message) {
        const alertContainer = document.getElementById('alert-container');
        if (alertContainer) {
            const alert = document.createElement('div');
            alert.className = 'alert alert-success alert-dismissible fade show';
            alert.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            alertContainer.appendChild(alert);

            // 5秒後に自動削除
            setTimeout(() => {
                alert.remove();
            }, 5000);
        }
    }

    async logout() {
        try {
            await this.fetchData('/api/v1/security/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            // ローカルストレージをクリア
            localStorage.removeItem('auth_token');
            
            // ログインページにリダイレクト
            window.location.href = '/login';
        } catch (error) {
            console.error('ログアウトエラー:', error);
            // エラーが発生してもローカルストレージをクリア
            localStorage.removeItem('auth_token');
            window.location.href = '/login';
        }
    }

    // ユーティリティ関数
    formatCurrency(amount) {
        return new Intl.NumberFormat('ja-JP', {
            style: 'currency',
            currency: 'JPY'
        }).format(amount);
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('ja-JP');
    }

    formatDateTime(dateString) {
        return new Date(dateString).toLocaleString('ja-JP');
    }
}

// ダッシュボードの初期化
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DashboardManager();
});

// ページ離脱時の処理
window.addEventListener('beforeunload', () => {
    if (window.dashboard) {
        window.dashboard.stopAutoRefresh();
    }
}); 