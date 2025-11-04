#!/bin/bash

# YOLO1125 智慧無人商店系統啟動腳本

echo "🚀 正在啟動 YOLO1125 系統..."

# 檢查是否在正確的目錄
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 檢查 MongoDB 是否運行
if ! pgrep -x "mongod" > /dev/null; then
    echo "⚠️  MongoDB 未運行，正在啟動..."
    brew services start mongodb-community@6.0
    sleep 2
fi

# 檢查 port 8000 是否被佔用
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "⚠️  Port 8000 已被佔用"
    echo "正在關閉舊的伺服器..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

# 啟動伺服器
echo "✅ 啟動後端伺服器..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

echo ""
echo "🎉 系統啟動完成！"
echo "📱 開啟瀏覽器訪問: http://localhost:8000"
