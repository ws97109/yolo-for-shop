"""
Ollama AI 商品諮詢服務
"""
import json
import httpx
from typing import List, Dict, Optional, AsyncGenerator
from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from backend.database import Database


class OllamaService:
    """Ollama AI 服務類別"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.products_context = ""
        self.system_prompt = ""
        self._load_products_context()
        print(f"✅ OllamaService 初始化完成 (模型: {self.model})")

    def _load_products_context(self):
        """載入商品資訊作為 AI 上下文"""
        try:
            db = Database.get_db()
            products = list(db.products.find({}))

            if not products:
                self.products_context = "目前沒有商品資訊。"
                return

            # 建立商品 JSON 資料
            products_data = []
            for p in products:
                products_data.append({
                    "name": p.get('name', ''),
                    "price": p.get('price', 0),
                    "description": p.get('description', ''),
                    "category": p.get('category', ''),
                    "stock": p.get('stock', 0),
                    "is_active": p.get('is_active', True)
                })

            self.products_context = json.dumps(products_data, ensure_ascii=False, indent=2)

            # 建立系統提示
            self.system_prompt = f"""你是一個智慧無人商店的 AI 助理，專門協助顧客了解商品資訊。

以下是商店目前的商品資料（JSON 格式）：
```json
{self.products_context}
```

請根據以上商品資料回答顧客的問題。

回答規則：
1. 只回答與商店商品相關的問題
2. 使用繁體中文回答
3. 回答要簡潔明瞭，不要太長
4. 如果顧客詢問的商品不存在，請禮貌地告知
5. 可以推薦相關商品
6. 提供價格時請使用 NT$ 或「元」
7. 如果問題與商品無關，請禮貌地引導顧客詢問商品相關問題"""

            print(f"✅ 載入 {len(products_data)} 個商品資訊作為 AI 上下文")

        except Exception as e:
            print(f"❌ 載入商品資訊失敗: {e}")
            self.products_context = "商品資訊載入失敗。"
            self.system_prompt = "你是一個智慧無人商店的 AI 助理。目前無法取得商品資訊，請稍後再試。"

    def refresh_products_context(self):
        """重新整理商品上下文"""
        print("🔄 重新整理 AI 商品上下文...")
        self._load_products_context()

    async def check_health(self) -> bool:
        """檢查 Ollama 服務是否可用"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            print(f"❌ Ollama 服務檢查失敗: {e}")
            return False

    async def chat(self, message: str, conversation_history: List[Dict] = None) -> str:
        """
        與 AI 對話（非串流模式）

        Args:
            message: 使用者訊息
            conversation_history: 對話歷史

        Returns:
            AI 回應
        """
        try:
            # 建立訊息列表
            messages = [{"role": "system", "content": self.system_prompt}]

            # 加入對話歷史
            if conversation_history:
                messages.extend(conversation_history)

            # 加入當前訊息
            messages.append({"role": "user", "content": message})

            # 呼叫 Ollama API
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False
                    }
                )

                if response.status_code != 200:
                    error_text = response.text
                    print(f"❌ Ollama API 錯誤: {response.status_code} - {error_text}")
                    return f"抱歉，AI 服務暫時無法使用。錯誤: {response.status_code}"

                result = response.json()
                return result.get("message", {}).get("content", "抱歉，無法取得回應。")

        except httpx.TimeoutException:
            print("❌ Ollama API 逾時")
            return "抱歉，AI 回應逾時，請稍後再試。"
        except Exception as e:
            print(f"❌ Ollama 對話錯誤: {e}")
            return f"抱歉，發生錯誤: {str(e)}"

    async def chat_stream(self, message: str, conversation_history: List[Dict] = None) -> AsyncGenerator[str, None]:
        """
        與 AI 對話（串流模式）

        Args:
            message: 使用者訊息
            conversation_history: 對話歷史

        Yields:
            AI 回應片段
        """
        try:
            # 建立訊息列表
            messages = [{"role": "system", "content": self.system_prompt}]

            # 加入對話歷史
            if conversation_history:
                messages.extend(conversation_history)

            # 加入當前訊息
            messages.append({"role": "user", "content": message})

            # 呼叫 Ollama API（串流模式）
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": True
                    }
                ) as response:
                    if response.status_code != 200:
                        yield "抱歉，AI 服務暫時無法使用。"
                        return

                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                content = data.get("message", {}).get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue

        except httpx.TimeoutException:
            yield "抱歉，AI 回應逾時，請稍後再試。"
        except Exception as e:
            print(f"❌ Ollama 串流對話錯誤: {e}")
            yield f"抱歉，發生錯誤: {str(e)}"

    def get_products_json(self) -> str:
        """取得商品 JSON 資料"""
        return self.products_context


# 單例模式
_ollama_service = None


def get_ollama_service() -> OllamaService:
    """取得 OllamaService 單例"""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service
