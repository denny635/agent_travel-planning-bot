import httpx
from typing import Optional

class AsyncHttpx:
    """异步 HTTP 客户端（单例 + 惰性初始化）"""
    
    _instance: Optional['AsyncHttpx'] = None
    _client: Optional[httpx.AsyncClient] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    # @property 修饰的函数可以直接当字段使用, 参考后面函数中使用
    @property
    def client(self) -> httpx.AsyncClient:
        """惰性加载 client"""
        # ✅ 全局 Client，整个应用生命周期复用, httpx.AsyncClient 实例是线程安全且可复用的，所有 HTTP 方法（GET、POST、PUT、DELETE 等）都可以通过同一个 httpx_client 实例来发起请求。
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=10.0,
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100
                ),
                headers={"User-Agent": "MyAgent/1.0"}
            )
        return self._client
    
    # 直接代理 httpx 的常用方法
    async def get(self, url, **kwargs):
        return await self.client.get(url, **kwargs)
    
    async def post(self, url, **kwargs):
        return await self.client.post(url, **kwargs)
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

