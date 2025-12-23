/**
 * Main Application Entry Point
 * 整合所有前端模組並處理應用邏輯
 */

class App {
    constructor() {
        this.camera = null;
        this.ws = null;
        this.cart = null;
        this.currentUser = null;
        this.frameInterval = null;
        this.FRAME_SEND_INTERVAL = 1000; // 每秒發送一幀
    }

    /**
     * 初始化應用程式
     */
    async init() {
        try {
            console.log('初始化應用程式...');

            // 檢查是否從登入頁面跳轉過來
            const urlParams = new URLSearchParams(window.location.search);
            const sessionId = urlParams.get('session_id');

            // 初始化購物車
            this.cart = new Cart();

            // 初始化相機
            this.camera = new CameraManager('camera-video', 'camera-canvas');
            await this.camera.start();
            console.log('相機啟動成功');

            // 使用全域 WebSocket 實例
            this.ws = wsClient;

            // 如果從登入頁跳轉過來，使用該 session_id
            if (sessionId) {
                this.ws.sessionId = sessionId;
            }

            this.setupWebSocketHandlers();
            this.ws.connect();

            // WebSocket 連線後啟動幀發送
            setTimeout(() => {
                if (this.ws && this.ws.connected) {
                    this.updateStatus('已連線', 'success');
                    this.startFrameSending();
                }
            }, 1000);

            // 設置 UI 事件
            this.setupUIEvents();

            // 顯示成功訊息
            this.showToast('系統初始化成功', 'success');

        } catch (error) {
            console.error('應用程式初始化失敗:', error);
            this.showToast(`初始化失敗: ${error.message}`, 'error');
            this.updateStatus('初始化失敗', 'error');
        }
    }

    /**
     * 設置 WebSocket 訊息處理器
     */
    setupWebSocketHandlers() {
        // 註冊訊息處理器（使用 .on() 方法）
        this.ws.on('user_info', this.handleUserInfo.bind(this));
        this.ws.on('user_login', this.handleUserLogin.bind(this));
        this.ws.on('face_detected', this.handleFaceDetected.bind(this));
        this.ws.on('face_status', this.handleFaceStatus.bind(this));
        this.ws.on('cart_update', this.handleCartUpdate.bind(this));
        this.ws.on('cart_updated', this.handleCartUpdated.bind(this));
        this.ws.on('product_added', this.handleProductAdded.bind(this));
        this.ws.on('product_detected', this.handleProductDetected.bind(this));
        this.ws.on('detection_result', this.handleDetectionResult.bind(this));
        this.ws.on('products_added', this.handleProductsAdded.bind(this));
        this.ws.on('error', this.handleError.bind(this));
    }

    /**
     * 開始定期發送影像幀
     */
    startFrameSending() {
        if (this.frameInterval) {
            clearInterval(this.frameInterval);
        }

        this.frameInterval = setInterval(() => {
            if (this.camera && this.ws && this.ws.connected) {
                const frame = this.camera.captureFrame();
                if (frame) {
                    this.ws.sendFrame(frame);
                }
            }
        }, this.FRAME_SEND_INTERVAL);

        console.log('開始發送影像幀');
    }

    /**
     * 停止發送影像幀
     */
    stopFrameSending() {
        if (this.frameInterval) {
            clearInterval(this.frameInterval);
            this.frameInterval = null;
            console.log('停止發送影像幀');
        }
    }

    /**
     * 處理使用者資訊更新
     */
    handleUserInfo(data) {
        console.log('收到使用者資訊:', data);
        this.currentUser = data.user;
        this.updateUserDisplay(data.user);

        if (data.is_new_user) {
            this.showToast(`歡迎新用戶: ${data.user.name}`, 'success');
        } else {
            this.showToast(`歡迎回來: ${data.user.name}`, 'success');
        }
    }

    /**
     * 處理購物車更新
     */
    handleCartUpdate(data) {
        console.log('購物車更新:', data);
        this.cart.update(data.cart);

        if (data.added_product) {
            this.showToast(`已加入: ${data.added_product}`, 'info');
        }
    }

    /**
     * 處理購物車更新
     */
    handleCartUpdated(data) {
        console.log('🛒 購物車更新:', data.cart);
        this.cart.update(data.cart);
    }

    /**
     * 處理商品加入事件
     */
    handleProductAdded(data) {
        console.log('📦 商品已加入:', data.product.name);
        this.showToast(`已加入：${data.product.name}`, 'info');
    }

    /**
     * 處理商品偵測事件（舊版，保留相容性）
     */
    handleProductDetected(data) {
        console.log('📦 偵測到商品:', data.product);
    }

    /**
     * 處理使用者登入
     */
    handleUserLogin(data) {
        console.log('使用者登入:', data.user);
        this.currentUser = data.user;

        // 更新使用者顯示區域
        this.updateUserDisplay(data.user);

        // 啟用辨識按鈕
        const detectBtn = document.getElementById('detect-btn');
        if (detectBtn) {
            detectBtn.disabled = false;
        }

        // 啟用結帳按鈕
        const checkoutBtn = document.getElementById('checkout-btn');
        if (checkoutBtn) {
            checkoutBtn.disabled = false;
        }

        // 顯示歡迎訊息
        if (data.is_new) {
            this.showToast(`歡迎，${data.user.name}！註冊成功`, 'success');
        } else {
            this.showToast(`歡迎回來，${data.user.name}！`, 'success');
        }

        // 更新人臉狀態
        const faceStatus = document.getElementById('face-status');
        if (faceStatus) {
            faceStatus.textContent = '已識別身份';
            faceStatus.className = 'status-success';
        }
    }

    /**
     * 處理人臉偵測
     */
    handleFaceDetected(data) {
        if (data.action === 'register_prompt') {
            console.log('👤 偵測到新人臉，顯示註冊表單');
            this.showRegisterForm();
        }

        // 更新人臉狀態
        const faceStatus = document.getElementById('face-status');
        if (faceStatus) {
            faceStatus.textContent = '已偵測到人臉';
            faceStatus.className = 'status-success';
        }
    }

    /**
     * 處理人臉狀態更新
     */
    handleFaceStatus(data) {
        const faceStatus = document.getElementById('face-status');
        if (faceStatus) {
            if (data.detected) {
                faceStatus.textContent = '已偵測到人臉';
                faceStatus.className = 'status-success';
            } else {
                faceStatus.textContent = '未偵測到人臉';
                faceStatus.className = 'status-idle';
            }
        }
    }

    /**
     * 顯示註冊表單
     */
    async showRegisterForm() {
        // 使用簡單的 prompt（可改為更美觀的 modal）
        const name = prompt('請輸入您的姓名：');
        if (!name) {
            this.showToast('已取消註冊', 'info');
            return;
        }

        const phone = prompt('請輸入您的電話：');
        if (!phone) {
            this.showToast('已取消註冊', 'info');
            return;
        }

        try {
            // 發送註冊請求
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.ws.sessionId,
                    name: name,
                    phone: phone
                })
            });

            const data = await response.json();

            if (data.success) {
                console.log('✅ 註冊成功:', data.user);
                // 登入訊息會透過 WebSocket 接收
            } else {
                throw new Error(data.error || '註冊失敗');
            }
        } catch (error) {
            console.error('❌ 註冊失敗:', error);
            this.showToast('註冊失敗，請稍後再試', 'error');
        }
    }

    /**
     * 處理錯誤訊息
     */
    handleError(data) {
        console.error('收到錯誤:', data);
        this.showToast(data.message || '發生錯誤', 'error');

        // 重置辨識狀態
        this.resetDetectionUI();
    }

    /**
     * 處理手動辨識按鈕點擊
     */
    async handleManualDetection() {
        if (!this.currentUser) {
            this.showToast('請先進行人臉辨識登入', 'error');
            return;
        }

        if (!this.camera || !this.ws || !this.ws.connected) {
            this.showToast('系統未就緒，請稍後再試', 'error');
            return;
        }

        try {
            console.log('🔍 開始手動辨識...');

            // 更新 UI 狀態
            this.setDetectionUI('detecting', '辨識中...');

            // 擷取當前幀
            const frame = this.camera.captureFrame();
            if (!frame) {
                throw new Error('無法擷取影像');
            }

            // 發送辨識請求
            this.ws.send({
                type: 'detect_products',
                frame: frame,
                timestamp: new Date().toISOString()
            });

        } catch (error) {
            console.error('❌ 辨識失敗:', error);
            this.showToast('辨識失敗，請重試', 'error');
            this.resetDetectionUI();
        }
    }

    /**
     * 處理辨識結果
     */
    handleDetectionResult(data) {
        console.log('📦 收到辨識結果:', data);

        const detections = data.detections || [];

        if (detections.length === 0) {
            this.setDetectionUI('error', data.message || '未辨識到商品');
            setTimeout(() => this.resetDetectionUI(), 2000);
            return;
        }

        // 顯示成功狀態
        this.setDetectionUI('success', `偵測到 ${detections.length} 項商品`);

        // 在畫面上繪製辨識框
        if (this.camera) {
            this.camera.drawDetections(detections);
        }

        // 顯示確認對話框
        setTimeout(() => {
            this.showDetectionConfirmation(detections);
        }, 500);
    }

    /**
     * 顯示辨識確認對話框
     */
    showDetectionConfirmation(detections) {
        const products = detections.map(d => d.product).filter(p => p);

        if (products.length === 0) {
            this.showToast('沒有可加入的商品', 'error');
            this.resetDetectionUI();
            return;
        }

        const productList = products.map(p => `• ${p.name} - NT$ ${p.price}`).join('\n');
        const confirmed = confirm(`偵測到以下商品，是否加入購物車？\n\n${productList}`);

        if (confirmed) {
            // 發送加入購物車請求
            this.ws.send({
                type: 'add_detected_products',
                products: products
            });
        } else {
            this.showToast('已取消加入', 'info');
            this.resetDetectionUI();
        }
    }

    /**
     * 處理商品加入成功
     */
    handleProductsAdded(data) {
        console.log('✅ 商品已加入:', data);
        this.showToast(data.message || '商品已加入購物車', 'success');
        this.resetDetectionUI();
    }

    /**
     * 設置辨識 UI 狀態
     */
    setDetectionUI(state, message) {
        const detectionBox = document.getElementById('detection-box');
        const detectionStatus = document.getElementById('detection-status');
        const detectBtn = document.getElementById('detect-btn');

        if (detectionBox) {
            detectionBox.className = 'guide-box ' + state;
        }

        if (detectionStatus) {
            detectionStatus.textContent = message;
            detectionStatus.className = 'detection-status ' + state;
        }

        if (detectBtn) {
            detectBtn.disabled = (state === 'detecting');
        }
    }

    /**
     * 重置辨識 UI 狀態
     */
    resetDetectionUI() {
        const detectionBox = document.getElementById('detection-box');
        const detectionStatus = document.getElementById('detection-status');
        const detectBtn = document.getElementById('detect-btn');

        if (detectionBox) {
            detectionBox.className = 'guide-box';
        }

        if (detectionStatus) {
            detectionStatus.textContent = '';
            detectionStatus.className = 'detection-status';
        }

        if (detectBtn && this.currentUser) {
            detectBtn.disabled = false;
        }

        // 清除繪製的辨識框
        if (this.camera) {
            this.camera.clearCanvas();
        }
    }

    /**
     * 設置 UI 事件監聽
     */
    setupUIEvents() {
        // 辨識按鈕
        const detectBtn = document.getElementById('detect-btn');
        if (detectBtn) {
            detectBtn.addEventListener('click', () => this.handleManualDetection());
        }

        // 結帳按鈕
        const checkoutBtn = document.getElementById('checkout-btn');
        if (checkoutBtn) {
            checkoutBtn.addEventListener('click', () => this.handleCheckout());
        }

        // 登出按鈕
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }

        // 查看歷史按鈕
        const viewHistoryBtn = document.getElementById('view-history-btn');
        if (viewHistoryBtn) {
            viewHistoryBtn.addEventListener('click', () => this.showHistory());
        }

        // 關閉歷史 modal
        const closeHistoryBtn = document.getElementById('close-history-modal');
        if (closeHistoryBtn) {
            closeHistoryBtn.addEventListener('click', () => {
                document.getElementById('history-modal').style.display = 'none';
            });
        }

        // 點擊 modal 外部關閉
        const historyModal = document.getElementById('history-modal');
        if (historyModal) {
            historyModal.addEventListener('click', (e) => {
                if (e.target === historyModal) {
                    historyModal.style.display = 'none';
                }
            });
        }

        // 移除購物車項目事件委派
        this.cart.onRemoveItem = (index) => {
            this.ws.sendCartRemove(index);
        };

        // 結帳事件委派
        this.cart.onCheckout = async () => {
            await this.handleCheckout();
        };
    }

    /**
     * 處理結帳
     */
    async handleCheckout() {
        if (!this.currentUser) {
            this.showToast('請先進行人臉辨識登入', 'error');
            return;
        }

        if (!this.cart.items || this.cart.items.length === 0) {
            this.showToast('購物車是空的', 'error');
            return;
        }

        try {
            const result = await this.cart.checkout();
            if (result.success) {
                this.showToast(`結帳成功！總金額: NT$${result.total}`, 'success');
                // 清空購物車 UI
                this.cart.update({ items: [], total: 0 });
            }
        } catch (error) {
            console.error('結帳失敗:', error);
            this.showToast('結帳失敗，請稍後再試', 'error');
        }
    }

    /**
     * 更新系統狀態顯示
     */
    updateStatus(message, type = 'idle') {
        const statusEl = document.getElementById('system-status');
        if (statusEl) {
            statusEl.textContent = message;
            statusEl.className = `status-${type}`;
        }
    }

    /**
     * 顯示提示訊息
     */
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        // 顯示動畫
        setTimeout(() => toast.classList.add('show'), 10);

        // 3秒後移除
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * HTML 跳脫處理
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 處理登出
     */
    handleLogout() {
        console.log('🚪 使用者登出');

        // 清除當前使用者資訊
        this.currentUser = null;

        // 清空購物車
        this.cart.clear();

        // 顯示提示
        this.showToast('已登出，返回登入頁面', 'info');

        // 延遲後跳轉
        setTimeout(() => {
            window.location.href = '/login.html';
        }, 1000);
    }

    /**
     * 顯示歷史消費記錄
     */
    async showHistory() {
        if (!this.currentUser || !this.currentUser.id) {
            this.showToast('請先登入', 'error');
            return;
        }

        console.log('📊 載入歷史消費記錄...');

        try {
            // 顯示 modal
            const modal = document.getElementById('history-modal');
            const historyList = document.getElementById('history-list');
            historyList.innerHTML = '<p class="loading">載入中...</p>';
            modal.style.display = 'block';

            // 獲取交易歷史
            const response = await fetch(`/api/user/${this.currentUser.id}/transactions`);
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.message || '無法載入歷史記錄');
            }

            // 更新統計摘要
            document.getElementById('total-transactions').textContent = data.total_transactions;
            document.getElementById('total-spent').textContent = `NT$ ${data.total_spent}`;

            // 顯示交易列表
            if (data.transactions.length === 0) {
                historyList.innerHTML = '<p class="no-data">尚無消費記錄</p>';
            } else {
                historyList.innerHTML = data.transactions.map(t => `
                    <div class="transaction-item">
                        <div class="transaction-header">
                            <span class="transaction-date">${new Date(t.date).toLocaleString('zh-TW')}</span>
                            <span class="transaction-amount">NT$ ${t.total_amount}</span>
                        </div>
                        <div class="transaction-details">
                            <span>商品數量：${t.total_quantity} 件</span>
                        </div>
                        <div class="transaction-items">
                            ${t.items.map(item => `
                                <div class="item-row">
                                    <span>${item.name}</span>
                                    <span>x${item.quantity}</span>
                                    <span>NT$ ${item.subtotal}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `).join('');
            }

        } catch (error) {
            console.error('❌ 載入歷史記錄失敗:', error);
            this.showToast('載入歷史記錄失敗', 'error');
            document.getElementById('history-list').innerHTML =
                '<p class="error">載入失敗，請稍後再試</p>';
        }
    }

    /**
     * 更新使用者資訊顯示
     */
    async updateUserDisplay(user) {
        const placeholder = document.getElementById('user-placeholder');
        const details = document.getElementById('user-details');
        const userName = document.getElementById('user-name');
        const userPhone = document.getElementById('user-phone');
        const userBirthday = document.getElementById('user-birthday');
        const userAvatar = document.getElementById('user-avatar');
        const totalSpentAmount = document.getElementById('total-spent-amount');
        const accountAge = document.getElementById('account-age');

        if (user) {
            // 顯示使用者資訊
            userName.textContent = user.name;
            userPhone.textContent = user.phone;

            // 設置頭像
            if (user.avatar) {
                userAvatar.src = user.avatar;
                userAvatar.style.display = 'block';
            } else {
                userAvatar.style.display = 'none';
            }

            // 獲取並顯示詳細資訊
            try {
                console.log('🔍 正在載入使用者詳細資訊...', user.id);

                const [userInfoRes, transactionsRes] = await Promise.all([
                    fetch(`/api/user/${user.id}/info`),
                    fetch(`/api/user/${user.id}/transactions`)
                ]);

                console.log('📡 API 回應狀態:', {
                    userInfo: userInfoRes.status,
                    transactions: transactionsRes.status
                });

                const userInfo = await userInfoRes.json();
                const transactions = await transactionsRes.json();

                console.log('📦 API 資料:', {
                    userInfo: userInfo,
                    transactions: transactions
                });

                // 顯示生日
                if (userInfo.success && userInfo.user.birthday) {
                    const birthday = new Date(userInfo.user.birthday);
                    userBirthday.textContent = `${birthday.getMonth() + 1}/${birthday.getDate()}`;
                } else {
                    userBirthday.textContent = '--/--';
                }

                // 顯示累積消費
                if (transactions.success) {
                    const totalSpent = transactions.total_spent || 0;
                    totalSpentAmount.textContent = `NT$ ${totalSpent.toLocaleString()}`;
                    console.log('💰 累積消費:', totalSpent, '元');
                    console.log('📊 交易記錄數量:', transactions.transactions ? transactions.transactions.length : 0);

                    // 顯示最近購買
                    if (transactions.transactions && transactions.transactions.length > 0) {
                        this.displayRecentPurchase(transactions.transactions);
                    } else {
                        console.log('⚠️ 沒有交易記錄');
                    }
                } else {
                    totalSpentAmount.textContent = 'NT$ 0';
                    console.log('⚠️ 累積消費 API 失敗:', transactions);
                }

                // 計算帳號年齡
                if (userInfo.success && userInfo.user.created_at) {
                    const createdAt = new Date(userInfo.user.created_at);
                    const now = new Date();
                    const diffDays = Math.floor((now - createdAt) / (1000 * 60 * 60 * 24));
                    accountAge.textContent = `${diffDays} 天`;
                    console.log('📅 會員天數:', diffDays, '天 (註冊日期:', createdAt.toLocaleDateString(), ')');
                } else {
                    accountAge.textContent = '0 天';
                    console.log('⚠️ 無法取得註冊日期');
                }
            } catch (error) {
                console.error('❌ 載入使用者詳細資訊失敗:', error);
                // 設置預設值
                totalSpentAmount.textContent = 'NT$ 0';
                accountAge.textContent = '0 天';
            }

            placeholder.style.display = 'none';
            details.style.display = 'flex';
        } else {
            // 顯示佔位符
            placeholder.style.display = 'block';
            details.style.display = 'none';
        }
    }

    /**
     * 顯示最近購買的商品
     */
    displayRecentPurchase(transactions) {
        const recentPurchaseDiv = document.getElementById('recent-purchase');
        const recentPurchaseItems = document.getElementById('recent-purchase-items');

        if (!transactions || transactions.length === 0) {
            recentPurchaseDiv.style.display = 'none';
            return;
        }

        // 取得最近一筆交易
        const latestTransaction = transactions[0];

        if (!latestTransaction || !latestTransaction.items || latestTransaction.items.length === 0) {
            recentPurchaseDiv.style.display = 'none';
            return;
        }

        // 顯示最近購買的商品
        const itemsHtml = latestTransaction.items.map(item =>
            `<div class="recent-item">
                <span class="recent-item-name">${item.product_name}</span>
                <span class="recent-item-quantity">x${item.quantity}</span>
            </div>`
        ).join('');

        recentPurchaseItems.innerHTML = itemsHtml;
        recentPurchaseDiv.style.display = 'block';

        console.log('🛍️ 最近購買:', latestTransaction.items);
    }

    /**
     * 清理資源
     */
    destroy() {
        this.stopFrameSending();
        if (this.ws) {
            this.ws.disconnect();
        }
        if (this.camera) {
            this.camera.stop();
        }
    }
}

// 當 DOM 載入完成後初始化應用程式
let app = null;

document.addEventListener('DOMContentLoaded', async () => {
    console.log('DOM 載入完成，啟動應用程式...');
    app = new App();
    await app.init();
});

// 頁面卸載時清理資源
window.addEventListener('beforeunload', () => {
    if (app) {
        app.destroy();
    }
});
