#!/usr/bin/env python3
"""
WebSocket 連接測試腳本
測試 WebSocket 是否能正常連接和通訊
"""

import asyncio
import json
import websockets
import sys

async def test_websocket():
    """測試 WebSocket 連接"""
    uri = "ws://localhost:8000/ws/test-session-123"

    print("=" * 60)
    print("WebSocket 連接測試")
    print("=" * 60)

    try:
        print(f"正在連接到: {uri}")
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket 連接成功！")

            # 測試 1: 發送 ping
            print("\n測試 1: 發送 ping 訊息")
            ping_message = {
                "type": "ping"
            }
            await websocket.send(json.dumps(ping_message))
            print(f"  發送: {ping_message}")

            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"  接收: {response_data}")

            if response_data.get("type") == "pong":
                print("  ✓ ping/pong 測試通過")
            else:
                print("  ✗ ping/pong 測試失敗")

            # 測試 2: 發送簡單的 frame（不包含真實圖像數據）
            print("\n測試 2: 發送測試 frame")
            frame_message = {
                "type": "frame",
                "frame": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAA8A/9k="
            }
            await websocket.send(json.dumps(frame_message))
            print(f"  發送: frame 訊息 (測試用 base64 數據)")

            # 等待回應（如果有的話）
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                response_data = json.loads(response)
                print(f"  接收: {response_data}")
                print("  ✓ frame 處理測試通過")
            except asyncio.TimeoutError:
                print("  ℹ️  未收到 frame 回應（這是正常的，因為 YOLO 尚未整合）")

            print("\n" + "=" * 60)
            print("WebSocket 測試完成！")
            print("=" * 60)
            return True

    except ConnectionRefusedError:
        print("✗ 連接被拒絕 - 請確認伺服器是否正在運行")
        return False
    except Exception as e:
        print(f"✗ WebSocket 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """執行測試"""
    result = asyncio.run(test_websocket())
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())
