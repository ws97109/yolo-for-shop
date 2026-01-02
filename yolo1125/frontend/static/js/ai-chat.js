/**
 * AI 商品助理聊天模組
 */

class AIChat {
    constructor() {
        this.isExpanded = false;
        this.isOnline = false;
        this.conversationHistory = [];
        this.isLoading = false;

        // DOM 元素
        this.chatToggle = document.getElementById('ai-chat-toggle');
        this.chatBody = document.getElementById('ai-chat-body');
        this.toggleBtn = document.getElementById('ai-toggle-btn');
        this.messagesContainer = document.getElementById('ai-messages');
        this.inputField = document.getElementById('ai-input');
        this.sendBtn = document.getElementById('ai-send-btn');
        this.statusElement = document.getElementById('ai-status');
        this.quickButtons = document.querySelectorAll('.quick-btn');

        this.init();
    }

    init() {
        // 綁定事件
        this.bindEvents();
        // 檢查 AI 服務狀態
        this.checkAIHealth();
        // 預設展開聊天區塊
        this.toggleChat();
    }

    bindEvents() {
        // 切換聊天視窗
        this.toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleChat();
        });

        this.chatToggle.addEventListener('click', () => {
            this.toggleChat();
        });

        // 發送訊息
        this.sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });

        // 按 Enter 發送
        this.inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // 快速問題按鈕
        this.quickButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const question = btn.dataset.question;
                this.inputField.value = question;
                this.sendMessage();
            });
        });
    }

    toggleChat() {
        this.isExpanded = !this.isExpanded;
        this.chatBody.style.display = this.isExpanded ? 'flex' : 'none';
        this.toggleBtn.querySelector('.toggle-icon').textContent = this.isExpanded ? '▲' : '▼';
    }

    async checkAIHealth() {
        try {
            const response = await fetch('/api/ai/health');
            const data = await response.json();

            if (data.success && data.status === 'healthy') {
                this.setOnlineStatus(true, data.model);
            } else {
                this.setOnlineStatus(false);
            }
        } catch (error) {
            console.error('AI 健康檢查失敗:', error);
            this.setOnlineStatus(false);
        }
    }

    setOnlineStatus(isOnline, model = '') {
        this.isOnline = isOnline;
        const statusDot = this.statusElement.querySelector('.ai-status-dot');
        const statusText = this.statusElement.querySelector('.ai-status-text');

        if (isOnline) {
            statusDot.classList.add('online');
            statusDot.classList.remove('offline');
            statusText.textContent = model ? `${model}` : '在線';
            this.inputField.disabled = false;
            this.sendBtn.disabled = false;
        } else {
            statusDot.classList.add('offline');
            statusDot.classList.remove('online');
            statusText.textContent = '離線';
            this.inputField.disabled = true;
            this.sendBtn.disabled = true;
        }
    }

    async sendMessage() {
        const message = this.inputField.value.trim();

        if (!message || this.isLoading || !this.isOnline) {
            return;
        }

        // 清空輸入框
        this.inputField.value = '';

        // 顯示使用者訊息
        this.addMessage(message, 'user');

        // 加入對話歷史
        this.conversationHistory.push({
            role: 'user',
            content: message
        });

        // 顯示載入中
        this.setLoading(true);
        const loadingId = this.addLoadingMessage();

        try {
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    history: this.conversationHistory.slice(-10) // 只保留最近 10 條對話
                })
            });

            const data = await response.json();

            // 移除載入訊息
            this.removeLoadingMessage(loadingId);

            if (data.success) {
                // 顯示 AI 回應
                this.addMessage(data.response, 'bot');

                // 加入對話歷史
                this.conversationHistory.push({
                    role: 'assistant',
                    content: data.response
                });
            } else {
                this.addMessage('抱歉，發生錯誤：' + (data.detail || '未知錯誤'), 'bot', true);
            }

        } catch (error) {
            console.error('AI 對話錯誤:', error);
            this.removeLoadingMessage(loadingId);
            this.addMessage('抱歉，無法連接 AI 服務，請稍後再試。', 'bot', true);
        } finally {
            this.setLoading(false);
        }
    }

    addMessage(content, type, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-message ai-message-${type}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = type === 'user' ? '你' : '✦';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        if (isError) {
            contentDiv.classList.add('error');
        }

        // 處理 Markdown 格式（簡易版）
        const formattedContent = this.formatMessage(content);
        contentDiv.innerHTML = `<p>${formattedContent}</p>`;

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);

        this.messagesContainer.appendChild(messageDiv);

        // 捲動到底部
        this.scrollToBottom();
    }

    addLoadingMessage() {
        const loadingId = 'loading-' + Date.now();
        const messageDiv = document.createElement('div');
        messageDiv.className = 'ai-message ai-message-bot loading-message';
        messageDiv.id = loadingId;

        messageDiv.innerHTML = `
            <div class="message-avatar">✦</div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();

        return loadingId;
    }

    removeLoadingMessage(loadingId) {
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) {
            loadingElement.remove();
        }
    }

    setLoading(isLoading) {
        this.isLoading = isLoading;
        this.inputField.disabled = isLoading;
        this.sendBtn.disabled = isLoading;

        if (isLoading) {
            this.sendBtn.innerHTML = '<span class="loading-spinner-small"></span>';
        } else {
            this.sendBtn.innerHTML = '<span>↑</span>';
        }
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    formatMessage(content) {
        // 簡易 Markdown 轉換
        return content
            // 粗體
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // 斜體
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // 程式碼
            .replace(/`(.*?)`/g, '<code>$1</code>')
            // 換行
            .replace(/\n/g, '<br>')
            // NT$ 格式化
            .replace(/NT\$\s*(\d+)/g, '<span class="price">NT$ $1</span>');
    }

    clearHistory() {
        this.conversationHistory = [];
        this.messagesContainer.innerHTML = `
            <div class="ai-message ai-message-bot">
                <div class="message-avatar">✦</div>
                <div class="message-content">
                    <p>嗨！我是您的 AI 商品助理，有任何商品問題都可以問我。</p>
                </div>
            </div>
        `;
    }
}

// 全域變數
let aiChat = null;

// 初始化 AI 聊天
function initAIChat() {
    aiChat = new AIChat();
}

// DOM 載入完成後初始化
document.addEventListener('DOMContentLoaded', () => {
    // 延遲初始化，確保其他模組已載入
    setTimeout(() => {
        initAIChat();
    }, 500);
});
