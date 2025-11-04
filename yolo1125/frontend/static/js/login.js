/**
 * YOLO1125 登入/註冊頁面
 * 使用 face_recognition 進行人臉識別
 */

class LoginManager {
    constructor() {
        this.currentTab = 'login';
        this.loginStream = null;
        this.registerStream = null;
        this.capturedFaceImage = null;
        this.ws = null;
        this.sessionId = this.generateSessionId();

        this.init();
    }

    generateSessionId() {
        return 'login_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }

    init() {
        this.setupTabs();
        this.setupLoginCamera();
        this.setupRegisterCamera();
        this.setupButtons();
    }

    // 設置選項卡切換
    setupTabs() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.dataset.tab;

                // 更新按鈕狀態
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                // 更新內容顯示
                tabContents.forEach(content => {
                    if (content.id === `${targetTab}-tab`) {
                        content.classList.add('active');
                    } else {
                        content.classList.remove('active');
                    }
                });

                this.currentTab = targetTab;

                // 如果切換到管理者頁面，停止相機
                if (targetTab === 'admin') {
                    this.stopAllCameras();
                }
            });
        });
    }

    // 停止所有相機
    stopAllCameras() {
        if (this.loginStream) {
            this.loginStream.getTracks().forEach(track => track.stop());
        }
        if (this.registerStream) {
            this.registerStream.getTracks().forEach(track => track.stop());
        }
    }

    // 設置登入鏡頭
    async setupLoginCamera() {
        const video = document.getElementById('login-video');
        const status = document.getElementById('login-status');
        const loginBtn = document.getElementById('login-btn');

        try {
            this.loginStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                }
            });

            video.srcObject = this.loginStream;
            status.textContent = '鏡頭已就緒，請點擊按鈕開始登入';
            loginBtn.disabled = false;
        } catch (err) {
            console.error('登入鏡頭啟動失敗:', err);
            status.textContent = '❌ 無法啟動鏡頭，請檢查權限設定';
        }
    }

    // 設置註冊鏡頭
    async setupRegisterCamera() {
        const video = document.getElementById('register-video');
        const status = document.getElementById('register-status');
        const captureBtn = document.getElementById('capture-face-btn');

        try {
            this.registerStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                }
            });

            video.srcObject = this.registerStream;
            status.textContent = '鏡頭已就緒，請拍攝人臉照片';
            captureBtn.disabled = false;
        } catch (err) {
            console.error('註冊鏡頭啟動失敗:', err);
            status.textContent = '❌ 無法啟動鏡頭，請檢查權限設定';
        }
    }

    // 設置按鈕事件
    setupButtons() {
        // 客戶登入按鈕
        document.getElementById('login-btn').addEventListener('click', () => {
            this.startFaceLogin();
        });

        // 管理者登入按鈕
        document.getElementById('admin-login-btn').addEventListener('click', () => {
            this.startAdminLogin();
        });

        // 拍攝人臉按鈕
        document.getElementById('capture-face-btn').addEventListener('click', () => {
            this.captureFaceImage();
        });

        // 註冊按鈕
        document.getElementById('register-btn').addEventListener('click', () => {
            this.completeRegistration();
        });
    }

    // 管理者登入
    async startAdminLogin() {
        const username = document.getElementById('admin-username').value.trim();
        const password = document.getElementById('admin-password').value.trim();
        const adminLoginBtn = document.getElementById('admin-login-btn');

        console.log('管理者登入 - 帳號:', username);

        // 驗證輸入
        if (!username || !password) {
            alert('請輸入帳號和密碼');
            return;
        }

        adminLoginBtn.disabled = true;
        this.showLoading('正在驗證管理者身份...');

        try {
            console.log('發送管理者登入請求...');
            // 發送登入請求
            const response = await fetch('/api/admin-login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });

            console.log('收到回應, status:', response.status);
            const result = await response.json();
            console.log('回應內容:', result);

            this.hideLoading();

            if (response.ok && result.success) {
                // 登入成功，跳轉到管理介面
                console.log('管理者登入成功，跳轉到管理後台');
                alert('✅ 管理者登入成功！');
                setTimeout(() => {
                    window.location.href = '/admin.html';
                }, 500);
            } else {
                // 登入失敗
                console.error('登入失敗:', result);
                alert('❌ ' + (result.detail || result.message || '帳號或密碼錯誤'));
                adminLoginBtn.disabled = false;
            }
        } catch (err) {
            console.error('管理者登入錯誤:', err);
            this.hideLoading();
            alert('❌ 登入失敗：' + err.message);
            adminLoginBtn.disabled = false;
        }
    }

    // 開始人臉登入
    async startFaceLogin() {
        const video = document.getElementById('login-video');
        const canvas = document.getElementById('login-canvas');
        const status = document.getElementById('login-status');
        const loginBtn = document.getElementById('login-btn');

        loginBtn.disabled = true;
        status.textContent = '正在識別人臉...';
        this.showLoading('正在進行人臉識別...');

        try {
            // 拍攝當前影格
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0);

            // 轉換為 base64
            const imageData = canvas.toDataURL('image/jpeg', 0.8);

            // 發送到後端進行人臉識別
            const response = await fetch('/api/face-login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image: imageData,
                    session_id: this.sessionId
                })
            });

            const result = await response.json();

            this.hideLoading();

            if (response.ok && result.success) {
                // 登入成功
                status.textContent = `✅ 歡迎回來，${result.user.name}！`;

                setTimeout(() => {
                    // 跳轉到購物頁面，帶上 session_id
                    window.location.href = `/index.html?session_id=${this.sessionId}`;
                }, 1500);
            } else {
                // 登入失敗
                status.textContent = '❌ ' + (result.message || '未識別到註冊使用者');
                loginBtn.disabled = false;

                setTimeout(() => {
                    status.textContent = '鏡頭已就緒，請點擊按鈕開始登入';
                }, 3000);
            }
        } catch (err) {
            console.error('人臉登入錯誤:', err);
            this.hideLoading();
            status.textContent = '❌ 登入失敗，請稍後再試';
            loginBtn.disabled = false;
        }
    }

    // 更新步驟指示器
    updateStepIndicator(step) {
        console.log('更新步驟指示器到步驟:', step);
        const steps = document.querySelectorAll('.steps-indicator .step');
        console.log('找到步驟元素數量:', steps.length);

        steps.forEach(stepEl => {
            const stepNumber = parseInt(stepEl.dataset.step);
            console.log(`處理步驟 ${stepNumber}, 目標步驟: ${step}`);

            if (stepNumber < step) {
                // 已完成的步驟
                stepEl.classList.remove('active');
                stepEl.classList.add('completed');
                console.log(`步驟 ${stepNumber} 標記為已完成`);
            } else if (stepNumber === step) {
                // 當前步驟
                stepEl.classList.add('active');
                stepEl.classList.remove('completed');
                console.log(`步驟 ${stepNumber} 標記為當前`);
            } else {
                // 未開始的步驟
                stepEl.classList.remove('active', 'completed');
                console.log(`步驟 ${stepNumber} 標記為未開始`);
            }
        });
    }

    // 拍攝人臉照片（註冊）
    captureFaceImage() {
        const video = document.getElementById('register-video');
        const canvas = document.getElementById('register-canvas');
        const status = document.getElementById('register-status');
        const captureBtn = document.getElementById('capture-face-btn');
        const registerForm = document.getElementById('register-form');
        const registerBtn = document.getElementById('register-btn');

        status.textContent = '正在拍攝...';

        try {
            // 拍攝當前影格
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0);

            // 保存圖片數據
            this.capturedFaceImage = canvas.toDataURL('image/jpeg', 0.8);

            // 更新步驟指示器到步驟 2
            this.updateStepIndicator(2);

            // 顯示註冊表單
            status.textContent = '✅ 人臉照片已拍攝，請填寫資料';
            captureBtn.style.display = 'none';
            registerForm.style.display = 'block';
            registerBtn.style.display = 'block';

            // 在 video 上顯示拍攝的照片（預覽）
            const img = new Image();
            img.onload = () => {
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                canvas.style.display = 'block';
                video.style.display = 'none';
            };
            img.src = this.capturedFaceImage;

        } catch (err) {
            console.error('拍攝人臉失敗:', err);
            status.textContent = '❌ 拍攝失敗，請重試';
        }
    }

    // 完成註冊
    async completeRegistration() {
        const name = document.getElementById('name').value.trim();
        const phone = document.getElementById('phone').value.trim();
        const birthday = document.getElementById('birthday').value;
        const status = document.getElementById('register-status');
        const registerBtn = document.getElementById('register-btn');

        // 驗證輸入
        if (!name || !phone || !birthday) {
            alert('請填寫完整資料');
            return;
        }

        if (!this.capturedFaceImage) {
            alert('請先拍攝人臉照片');
            return;
        }

        registerBtn.disabled = true;
        this.showLoading('正在建立帳戶...');

        try {
            // 發送到後端進行註冊
            const response = await fetch('/api/face-register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    phone: phone,
                    birthday: birthday,
                    image: this.capturedFaceImage,
                    session_id: this.sessionId
                })
            });

            const result = await response.json();

            this.hideLoading();

            if (response.ok && result.success) {
                // 更新步驟指示器到步驟 3（完成）
                this.updateStepIndicator(3);

                // 註冊成功
                status.textContent = `✅ 註冊成功，歡迎 ${name}！`;

                setTimeout(() => {
                    // 跳轉到購物頁面
                    window.location.href = `/index.html?session_id=${this.sessionId}`;
                }, 1500);
            } else {
                // 註冊失敗
                alert('❌ ' + (result.message || '註冊失敗'));
                registerBtn.disabled = false;
            }
        } catch (err) {
            console.error('註冊錯誤:', err);
            this.hideLoading();
            alert('❌ 註冊失敗，請稍後再試');
            registerBtn.disabled = false;
        }
    }

    // 顯示載入中
    showLoading(message) {
        const overlay = document.getElementById('loading-overlay');
        const messageEl = document.getElementById('loading-message');
        messageEl.textContent = message;
        overlay.style.display = 'flex';
    }

    // 隱藏載入中
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        overlay.style.display = 'none';
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    new LoginManager();
});
