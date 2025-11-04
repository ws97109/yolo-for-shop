/**
 * 購物車類別
 * 負責管理購物車 UI 和邏輯
 */
class Cart {
    constructor() {
        this.items = [];
        this.totalQuantity = 0;
        this.totalAmount = 0;
    }

    /**
     * 更新購物車資料並重新渲染
     * @param {Object} cartData - 購物車資料 {items, total_quantity, total_amount}
     */
    update(cartData) {
        this.items = cartData.items || [];
        this.totalQuantity = cartData.total_quantity || 0;
        this.totalAmount = cartData.total_amount || 0;

        this.render();
    }

    /**
     * 渲染購物車 UI
     */
    render() {
        const cartItemsEl = document.getElementById('cart-items');
        const totalQuantityEl = document.getElementById('total-quantity');
        const totalAmountEl = document.getElementById('total-amount');
        const checkoutBtn = document.getElementById('checkout-btn');

        // 更新商品清單
        if (this.items.length === 0) {
            cartItemsEl.innerHTML = `
                <div class="empty-cart">
                    🛒 購物車是空的
                </div>
            `;
            checkoutBtn.disabled = true;
        } else {
            cartItemsEl.innerHTML = this.items.map((item, index) => `
                <div class="cart-item">
                    <div class="cart-item-info">
                        <div class="cart-item-name">${this.escapeHtml(item.name)}</div>
                        <div class="cart-item-details">
                            NT$ ${item.unit_price} × ${item.quantity} = NT$ ${item.subtotal}
                        </div>
                    </div>
                    <button class="cart-item-remove" onclick="cart.removeItem(${index})">
                        移除
                    </button>
                </div>
            `).join('');

            checkoutBtn.disabled = false;
        }

        // 更新總計
        totalQuantityEl.textContent = this.totalQuantity;
        totalAmountEl.textContent = `NT$ ${this.totalAmount}`;

        // 更新用戶卡片中的本次消費
        const currentTotalEl = document.getElementById('current-total');
        if (currentTotalEl) {
            currentTotalEl.textContent = `NT$ ${this.totalAmount}`;
        }
    }

    /**
     * 移除購物車商品
     * @param {number} index - 商品索引
     */
    removeItem(index) {
        console.log(`🗑️ 移除商品索引: ${index}`);

        // 發送移除請求到後端
        wsClient.sendCartRemove(index);
    }

    /**
     * 清空購物車
     */
    clear() {
        this.items = [];
        this.totalQuantity = 0;
        this.totalAmount = 0;
        this.render();
    }

    /**
     * 結帳
     */
    async checkout() {
        if (this.items.length === 0) {
            showToast('購物車是空的，無法結帳');
            return;
        }

        // 確認結帳
        const confirmed = confirm(
            `確認結帳？\n\n` +
            `商品數量：${this.totalQuantity}\n` +
            `總金額：NT$ ${this.totalAmount}`
        );

        if (!confirmed) return;

        try {
            // 發送結帳請求
            const response = await fetch('/api/checkout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: wsClient.sessionId
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // 結帳成功
                const message = `✅ 結帳成功！\n\n` +
                    `交易編號：${data.transaction_id.substring(0, 12)}...\n` +
                    `總金額：NT$ ${data.total_amount}\n\n` +
                    `感謝您的購買！`;
                alert(message);
                console.log('✅ 結帳成功:', data);
                // 購物車會透過 WebSocket cart_updated 訊息自動清空
            } else {
                // 結帳失敗
                alert('❌ 結帳失敗：' + (data.detail || data.message || '未知錯誤'));
            }

        } catch (err) {
            console.error('❌ 結帳錯誤:', err);
            showToast('❌ 結帳失敗，請檢查網路連線');
        }
    }

    /**
     * 跳脫 HTML 特殊字元
     * @param {string} text - 原始文字
     * @returns {string} 跳脫後的文字
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 全域實例
const cart = new Cart();
