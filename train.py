import os
from ultralytics import YOLO
from pathlib import Path
import argparse

class SupermarketModelTrainer:
    def __init__(self):
        """
        初始化模型訓練器
        """
        # 使用YOLOv8預訓練模型作為基底
        self.model = YOLO('yolov8n.pt')
        print("載入YOLOv8預訓練模型")

        # 定義商品類別
        self.product_classes = {
            0: "可樂",
            1: "洋芋片",
            2: "餅乾",
            3: "礦泉水",
            4: "牛奶",
            5: "麵包",
            6: "蘋果",
            7: "香蕉",
            8: "優格",
            9: "泡麵"
        }

    def create_dataset_yaml(self, data_path, output_path=None):
        """
        建立訓練用的資料集YAML配置檔案

        Args:
            data_path: 資料集根目錄路徑
            output_path: YAML檔案輸出路徑，預設為data_path下的dataset.yaml

        Returns:
            str: YAML檔案路徑
        """
        if output_path is None:
            output_path = os.path.join(data_path, 'dataset.yaml')

        # 確保路徑存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        yaml_content = f"""# 超市商品辨識資料集配置
path: {os.path.abspath(data_path)}
train: images/train
val: images/val
test: images/test

# 類別數量
nc: {len(self.product_classes)}

# 類別名稱
names: {list(self.product_classes.values())}
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)

        print(f"資料集配置檔案已建立: {output_path}")
        return output_path

    def validate_dataset_structure(self, data_path):
        """
        驗證資料集結構是否正確

        Args:
            data_path: 資料集根目錄路徑

        Returns:
            bool: 結構是否正確
        """
        required_dirs = [
            'images/train',
            'images/val',
            'labels/train',
            'labels/val'
        ]

        print("檢查資料集結構...")
        missing_dirs = []

        for dir_name in required_dirs:
            full_path = os.path.join(data_path, dir_name)
            if not os.path.exists(full_path):
                missing_dirs.append(dir_name)
            else:
                # 檢查資料夾是否有檔案
                files = os.listdir(full_path)
                print(f"✓ {dir_name}: {len(files)} 個檔案")

        if missing_dirs:
            print("❌ 缺少以下必要資料夾:")
            for missing in missing_dirs:
                print(f"   - {missing}")
            return False

        print("✓ 資料集結構檢查通過")
        return True

    def train_model(self, data_yaml_path, **training_params):
        """
        訓練YOLO模型

        Args:
            data_yaml_path: 資料集YAML檔案路徑
            **training_params: 訓練參數

        Returns:
            訓練結果
        """
        # 預設訓練參數
        default_params = {
            'epochs': 100,
            'imgsz': 640,
            'batch': 16,
            'lr0': 0.01,
            'weight_decay': 0.0005,
            'patience': 50,
            'save': True,
            'plots': True,
            'verbose': True,
            'name': 'supermarket_product_detector'
        }

        # 更新參數
        default_params.update(training_params)

        print("開始訓練模型...")
        print(f"訓練參數: {default_params}")

        try:
            # 訓練模型
            results = self.model.train(
                data=data_yaml_path,
                **default_params
            )

            print("\n🎉 訓練完成!")
            print(f"模型已儲存至: runs/detect/{default_params['name']}/weights/best.pt")

            return results

        except Exception as e:
            print(f"❌ 訓練過程發生錯誤: {e}")
            raise

    def resume_training(self, model_path, **training_params):
        """
        從檢查點恢復訓練

        Args:
            model_path: 模型檔案路徑
            **training_params: 訓練參數
        """
        print(f"從檢查點恢復訓練: {model_path}")

        # 載入模型
        self.model = YOLO(model_path)

        # 設定參數
        default_params = {
            'resume': True,
            'epochs': 100,
            'save': True,
            'plots': True,
            'verbose': True
        }
        default_params.update(training_params)

        # 恢復訓練
        results = self.model.train(**default_params)

        print("恢復訓練完成!")
        return results

def main():
    """
    主要執行函數
    """
    parser = argparse.ArgumentParser(description='超市商品辨識模型訓練程式')

    parser.add_argument('--data', type=str, required=True,
                       help='資料集根目錄路徑')
    parser.add_argument('--epochs', type=int, default=100,
                       help='訓練輪數 (預設: 100)')
    parser.add_argument('--batch', type=int, default=16,
                       help='批次大小 (預設: 16)')
    parser.add_argument('--imgsz', type=int, default=640,
                       help='輸入圖片尺寸 (預設: 640)')
    parser.add_argument('--lr0', type=float, default=0.01,
                       help='初始學習率 (預設: 0.01)')
    parser.add_argument('--resume', type=str, default=None,
                       help='從檢查點恢復訓練的模型路徑')
    parser.add_argument('--name', type=str, default='supermarket_product_detector',
                       help='實驗名稱')
    parser.add_argument('--patience', type=int, default=50,
                       help='早停耐心值 (預設: 50)')

    args = parser.parse_args()

    print("=== 超市商品辨識模型訓練 ===")

    # 建立訓練器
    trainer = SupermarketModelTrainer()

    try:
        if args.resume:
            # 從檢查點恢復訓練
            print(f"從檢查點恢復訓練: {args.resume}")
            results = trainer.resume_training(
                args.resume,
                epochs=args.epochs,
                batch=args.batch,
                imgsz=args.imgsz,
                lr0=args.lr0,
                patience=args.patience,
                name=args.name
            )
        else:
            # 新訓練
            # 驗證資料集結構
            if not trainer.validate_dataset_structure(args.data):
                print("❌ 資料集結構不正確，請確認資料夾結構:")
                print("""
所需結構:
dataset/
├── images/
│   ├── train/     # 訓練圖片
│   ├── val/       # 驗證圖片
│   └── test/      # 測試圖片 (可選)
└── labels/
    ├── train/     # 訓練標籤 (.txt檔案)
    ├── val/       # 驗證標籤 (.txt檔案)
    └── test/      # 測試標籤 (可選)
                """)
                return

            # 建立資料集配置檔案
            yaml_path = trainer.create_dataset_yaml(args.data)

            # 開始訓練
            results = trainer.train_model(
                yaml_path,
                epochs=args.epochs,
                batch=args.batch,
                imgsz=args.imgsz,
                lr0=args.lr0,
                patience=args.patience,
                name=args.name
            )

        print(f"\n✅ 訓練成功完成!")
        print(f"最佳模型路徑: runs/detect/{args.name}/weights/best.pt")
        print(f"最後模型路徑: runs/detect/{args.name}/weights/last.pt")

    except KeyboardInterrupt:
        print("\n⚠️ 訓練被使用者中斷")
    except Exception as e:
        print(f"\n❌ 訓練失敗: {e}")

if __name__ == "__main__":
    # 如果沒有提供命令列參數，則進入互動模式
    import sys
    if len(sys.argv) == 1:
        print("=== 超市商品辨識模型訓練 (互動模式) ===")

        trainer = SupermarketModelTrainer()

        # 取得資料集路徑
        data_path = input("請輸入資料集根目錄路徑: ").strip()
        if not os.path.exists(data_path):
            print(f"❌ 路徑不存在: {data_path}")
            exit(1)

        # 檢查是否要恢復訓練
        resume_choice = input("是否從檢查點恢復訓練? (y/n): ").strip().lower()

        if resume_choice == 'y':
            model_path = input("請輸入模型檔案路徑: ").strip()
            epochs = int(input("請輸入訓練輪數 (預設100): ") or 100)

            try:
                results = trainer.resume_training(model_path, epochs=epochs)
                print("✅ 恢復訓練完成!")
            except Exception as e:
                print(f"❌ 恢復訓練失敗: {e}")
        else:
            # 驗證資料集
            if not trainer.validate_dataset_structure(data_path):
                print("❌ 請修正資料集結構後再執行")
                exit(1)

            # 取得訓練參數
            epochs = int(input("請輸入訓練輪數 (預設100): ") or 100)
            batch_size = int(input("請輸入批次大小 (預設16): ") or 16)
            img_size = int(input("請輸入圖片尺寸 (預設640): ") or 640)

            # 建立配置檔案和開始訓練
            try:
                yaml_path = trainer.create_dataset_yaml(data_path)
                results = trainer.train_model(
                    yaml_path,
                    epochs=epochs,
                    batch=batch_size,
                    imgsz=img_size
                )
                print("✅ 訓練完成!")
            except Exception as e:
                print(f"❌ 訓練失敗: {e}")
    else:
        main()