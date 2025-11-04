/**
 * WebSocket 客戶端類別
 * 負責與後端即時通訊
 */
class WebSocketClient {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.sessionId = this.generateSessionId();
        this.connected = false;
        this.messageHandlers = {};
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // 初始重連延遲 1 秒
    }

    /**
     * 產生唯一的 Session ID
     * @returns {string} Session ID
     */
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * 連接 WebSocket
     */
    connect() {
        const wsUrl = `${this.url}/${this.sessionId}`;
        console.log(`🔌 正在連接 WebSocket: ${wsUrl}`);

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('✅ WebSocket 連線成功');
                this.connected = true;
                this.reconnectAttempts = 0;
                this.reconnectDelay = 1000;
                this.updateStatus(true);
            };

            this.ws.onclose = () => {
                console.log('❌ WebSocket 斷線');
                this.connected = false;
                this.updateStatus(false);
                this.handleReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('❌ WebSocket 錯誤:', error);
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('❌ 解析訊息失敗:', error);
                }
            };

        } catch (error) {
            console.error('❌ WebSocket 連線失敗:', error);
            this.handleReconnect();
        }
    }

    /**
     * 處理重新連線
     */
    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * this.reconnectAttempts;

            console.log(`⏳ ${delay/1000} 秒後重新連線... (嘗試 ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

            setTimeout(() => {
                this.connect();
            }, delay);
        } else {
            console.error('❌ 已達最大重連次數');
            showToast('連線中斷，請重新整理頁面');
        }
    }

    /**
     * 發送訊息
     * @param {Object} data - 要發送的資料
     */
    send(data) {
        if (this.connected && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify(data));
            } catch (error) {
                console.error('❌ 發送訊息失敗:', error);
            }
        } else {
            console.warn('⚠️ WebSocket 未連線，無法發送訊息');
        }
    }

    /**
     * 發送影像影格
     * @param {string} frameData - Base64 編碼的影像
     */
    sendFrame(frameData) {
        this.send({
            type: 'frame',
            frame: frameData,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * 發送心跳
     */
    sendPing() {
        this.send({
            type: 'ping',
            timestamp: new Date().toISOString()
        });
    }

    /**
     * 發送移除購物車商品請求
     * @param {number} index - 商品索引
     */
    sendCartRemove(index) {
        this.send({
            type: 'cart_remove',
            index: index
        });
    }

    /**
     * 註冊訊息處理器
     * @param {string} messageType - 訊息類型
     * @param {Function} handler - 處理函式
     */
    on(messageType, handler) {
        this.messageHandlers[messageType] = handler;
    }

    /**
     * 處理收到的訊息
     * @param {Object} data - 訊息資料
     */
    handleMessage(data) {
        const messageType = data.type;

        // 呼叫對應的處理器
        const handler = this.messageHandlers[messageType];
        if (handler) {
            try {
                handler(data);
            } catch (error) {
                console.error(`❌ 處理訊息失敗 (${messageType}):`, error);
            }
        } else {
            console.log(`📨 收到訊息 (${messageType}):`, data);
        }
    }

    /**
     * 更新連線狀態顯示
     * @param {boolean} connected - 是否已連線
     */
    updateStatus(connected) {
        const statusEl = document.getElementById('connection-status');
        if (statusEl) {
            if (connected) {
                statusEl.textContent = '● 已連線';
                statusEl.className = 'status-connected';
            } else {
                statusEl.textContent = '● 未連線';
                statusEl.className = 'status-disconnected';
            }
        }
    }

    /**
     * 關閉連線
     */
    close() {
        if (this.ws) {
            this.connected = false;
            this.ws.close();
            console.log('🔌 WebSocket 連線已關閉');
        }
    }
}

// 全域實例（使用 ws:// 因為是本地開發）
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsHost = window.location.host;
const wsClient = new WebSocketClient(`${wsProtocol}//${wsHost}/ws`);
