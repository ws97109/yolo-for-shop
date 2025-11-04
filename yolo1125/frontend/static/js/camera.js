/**
 * 鏡頭管理類別
 * 負責存取鏡頭、顯示影像、繪製偵測框
 */
class CameraManager {
    constructor(videoId, canvasId) {
        this.video = document.getElementById(videoId);
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.stream = null;
        this.isRunning = false;
        this.loadingEl = document.getElementById('camera-loading');
    }

    /**
     * 啟動鏡頭
     */
    async start() {
        try {
            console.log('🎥 正在啟動鏡頭...');

            // 請求鏡頭權限
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                },
                audio: false
            });

            this.video.srcObject = this.stream;
            this.isRunning = true;

            // 等待視訊載入
            await new Promise((resolve) => {
                this.video.onloadedmetadata = () => {
                    // 設定 Canvas 尺寸
                    this.canvas.width = this.video.videoWidth;
                    this.canvas.height = this.video.videoHeight;
                    resolve();
                };
            });

            console.log(`✅ 鏡頭啟動成功 (${this.canvas.width}x${this.canvas.height})`);
            this.hideLoading();
            this.hideError();
            this.startDrawing();

        } catch (error) {
            console.error('❌ 鏡頭存取失敗:', error);

            let errorMessage = '無法存取鏡頭';

            if (error.name === 'NotAllowedError') {
                errorMessage = '請允許鏡頭權限';
            } else if (error.name === 'NotFoundError') {
                errorMessage = '找不到鏡頭設備';
            } else if (error.name === 'NotReadableError') {
                errorMessage = '鏡頭正被其他程式使用';
            } else if (error.name === 'OverconstrainedError') {
                errorMessage = '無法滿足鏡頭需求';
            }

            this.showError(errorMessage);
            this.hideLoading();
        }
    }

    /**
     * 開始繪製影像到 Canvas
     */
    startDrawing() {
        const draw = () => {
            if (!this.isRunning) return;

            // 繪製當前影格到 Canvas
            if (this.video.readyState === this.video.HAVE_ENOUGH_DATA) {
                this.ctx.drawImage(
                    this.video,
                    0, 0,
                    this.canvas.width,
                    this.canvas.height
                );
            }

            requestAnimationFrame(draw);
        };
        draw();
    }

    /**
     * 擷取當前影格為 Base64
     * @returns {string} Base64 編碼的影像
     */
    captureFrame() {
        if (!this.isRunning) return null;

        try {
            // 擷取當前 Canvas 內容為 Base64 (JPEG 格式, 80% 品質)
            return this.canvas.toDataURL('image/jpeg', 0.8);
        } catch (error) {
            console.error('❌ 擷取影格失敗:', error);
            return null;
        }
    }

    /**
     * 清除 Canvas（用於重新繪製偵測框）
     */
    clearCanvas() {
        if (this.isRunning && this.video.readyState === this.video.HAVE_ENOUGH_DATA) {
            this.ctx.drawImage(
                this.video,
                0, 0,
                this.canvas.width,
                this.canvas.height
            );
        }
    }

    /**
     * 繪製偵測框
     * @param {number} x - X 座標
     * @param {number} y - Y 座標
     * @param {number} width - 寬度
     * @param {number} height - 高度
     * @param {string} label - 標籤文字
     * @param {string} color - 顏色（預設綠色）
     */
    drawBox(x, y, width, height, label, color = '#00ff00') {
        // 繪製矩形框
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 3;
        this.ctx.strokeRect(x, y, width, height);

        // 繪製標籤背景
        this.ctx.font = 'bold 16px Arial';
        const textWidth = this.ctx.measureText(label).width;
        this.ctx.fillStyle = color;
        this.ctx.fillRect(x, y - 25, textWidth + 10, 25);

        // 繪製標籤文字
        this.ctx.fillStyle = '#000';
        this.ctx.fillText(label, x + 5, y - 7);
    }

    /**
     * 繪製多個偵測框
     * @param {Array} detections - 偵測結果陣列
     */
    drawDetections(detections) {
        // 先清除舊的偵測框
        this.clearCanvas();

        // 繪製每個偵測框
        detections.forEach(detection => {
            const [x1, y1, x2, y2] = detection.bbox;
            const width = x2 - x1;
            const height = y2 - y1;

            let label = detection.class_name || '未知';
            if (detection.product) {
                const confidence = (detection.confidence * 100).toFixed(0);
                label = `${detection.product.name} (${confidence}%)`;
            }

            this.drawBox(x1, y1, width, height, label, '#00ff00');
        });
    }

    /**
     * 顯示錯誤訊息
     * @param {string} message - 錯誤訊息
     */
    showError(message) {
        const errorEl = document.getElementById('camera-error');
        errorEl.textContent = '❌ ' + message;
        errorEl.style.display = 'block';
    }

    /**
     * 隱藏錯誤訊息
     */
    hideError() {
        const errorEl = document.getElementById('camera-error');
        errorEl.style.display = 'none';
    }

    /**
     * 隱藏載入訊息
     */
    hideLoading() {
        if (this.loadingEl) {
            this.loadingEl.style.display = 'none';
        }
    }

    /**
     * 停止鏡頭
     */
    stop() {
        this.isRunning = false;
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            console.log('🛑 鏡頭已停止');
        }
    }
}

// 全域實例
const cameraManager = new CameraManager('video', 'canvas');
