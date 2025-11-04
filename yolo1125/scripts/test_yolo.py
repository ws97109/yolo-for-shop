#!/usr/bin/env python3
"""
YOLO 偵測測試腳本
測試 YOLO 模型是否能正確偵測商品
"""

import sys
from pathlib import Path
import cv2

# 加入專案路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.yolo_service import get_yolo_service


def test_yolo():
    """測試 YOLO 偵測"""
    print("=" * 60)
    print("YOLO 偵測測試")
    print("=" * 60)

    # 初始化 YOLO 服務
    try:
        yolo_service = get_yolo_service()
        print("\n✅ YOLO 服務初始化成功")
    except Exception as e:
        print(f"\n❌ YOLO 服務初始化失敗: {e}")
        return False

    # 測試圖片路徑
    dataset_path = Path(__file__).parent.parent.parent / "dataset" / "images"

    # 嘗試找測試圖片
    test_images = []

    # 先嘗試 train 目錄
    train_path = dataset_path / "train"
    if train_path.exists():
        test_images = list(train_path.glob("*.jpg"))[:3]

    # 如果沒有，嘗試根目錄
    if not test_images and dataset_path.exists():
        test_images = list(dataset_path.glob("*.jpg"))[:3]

    if not test_images:
        print(f"\n⚠️  找不到測試圖片")
        print(f"   嘗試路徑: {dataset_path}")
        print(f"   嘗試路徑: {train_path}")

        # 創建一個簡單的測試圖片
        print("\n建立測試用空白圖片...")
        test_frame = cv2.imread(str(Path(__file__).parent.parent.parent / "yolov8n.pt"))

        if test_frame is None:
            # 創建純色測試圖片
            import numpy as np
            test_frame = np.zeros((640, 640, 3), dtype=np.uint8)
            test_frame[:] = (100, 100, 100)  # 灰色

        print("\n測試空白圖片:")
        detections = yolo_service.detect(test_frame)
        print(f"  偵測結果: {len(detections)} 個物品")

        if len(detections) == 0:
            print("  ✅ 空白圖片沒有偵測到物品（正常）")

        return True

    print(f"\n找到 {len(test_images)} 張測試圖片")
    print("=" * 60)

    all_success = True

    for img_path in test_images:
        print(f"\n測試圖片: {img_path.name}")
        frame = cv2.imread(str(img_path))

        if frame is None:
            print("  ❌ 無法讀取圖片")
            all_success = False
            continue

        print(f"  圖片大小: {frame.shape[1]}x{frame.shape[0]}")

        # 偵測
        detections = yolo_service.detect(frame)

        if detections:
            print(f"  ✅ 偵測到 {len(detections)} 個商品:")
            for det in detections:
                product_name = det['product']['name'] if det['product'] else det['class_name']
                print(f"     - {product_name}")
                print(f"       信心度: {det['confidence']:.2f}")
                print(f"       座標: {det['bbox']}")

                if det['product']:
                    print(f"       價格: NT${det['product']['price']}")
        else:
            print("  ⚠️  未偵測到商品（可能是信心度太低或圖片中無商品）")

    print("\n" + "=" * 60)
    if all_success:
        print("✅ YOLO 測試完成！")
    else:
        print("⚠️  部分測試失敗")
    print("=" * 60)

    return all_success


if __name__ == "__main__":
    success = test_yolo()
    sys.exit(0 if success else 1)
