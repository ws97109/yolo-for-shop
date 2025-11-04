#!/usr/bin/env python3
"""
前端功能測試腳本
測試靜態檔案是否能正確載入
"""

import requests
import sys

BASE_URL = "http://localhost:8000"

def test_static_file(path, description):
    """測試靜態檔案是否可訪問"""
    url = f"{BASE_URL}{path}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✓ {description}: {len(response.content)} bytes")
            return True
        else:
            print(f"✗ {description}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ {description}: {str(e)}")
        return False

def main():
    """執行所有測試"""
    print("=" * 60)
    print("前端功能測試")
    print("=" * 60)

    tests = [
        ("/", "主頁面 (index.html)"),
        ("/static/css/style.css", "CSS 樣式表"),
        ("/static/js/camera.js", "相機模組"),
        ("/static/js/websocket.js", "WebSocket 模組"),
        ("/static/js/cart.js", "購物車模組"),
        ("/static/js/main.js", "主程式"),
        ("/api/health", "API 健康檢查"),
        ("/api/products", "產品列表 API"),
    ]

    results = []
    for path, description in tests:
        result = test_static_file(path, description)
        results.append(result)

    print("\n" + "=" * 60)
    print(f"測試結果: {sum(results)}/{len(results)} 通過")
    print("=" * 60)

    # 檢查 HTML 是否包含所有必要的 script 標籤
    print("\n檢查 HTML 結構...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        html = response.text

        required_scripts = [
            "/static/js/camera.js",
            "/static/js/websocket.js",
            "/static/js/cart.js",
            "/static/js/main.js"
        ]

        for script in required_scripts:
            if script in html:
                print(f"✓ 找到 script: {script}")
            else:
                print(f"✗ 缺少 script: {script}")

        # 檢查必要的 HTML 元素
        required_elements = [
            'id="system-status"',
            'id="face-status"',
            'id="user-info"',
            'id="camera-video"',
            'id="camera-canvas"',
            'id="cart-items"',
            'id="checkout-btn"'
        ]

        print("\n檢查必要的 HTML 元素...")
        for element in required_elements:
            if element in html:
                print(f"✓ 找到元素: {element}")
            else:
                print(f"✗ 缺少元素: {element}")

    except Exception as e:
        print(f"✗ HTML 檢查失敗: {str(e)}")

    print("\n" + "=" * 60)
    print("測試完成！")
    print("請在瀏覽器中開啟 http://localhost:8000 進行手動測試")
    print("=" * 60)

    return 0 if all(results) else 1

if __name__ == "__main__":
    sys.exit(main())
