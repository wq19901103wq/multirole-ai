"""
免费搜索方案 - 无需 API Key
支持 DuckDuckGo（推荐）和 Bing（有限免费）
"""
import time
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseSearchProvider(ABC):
    """搜索工具抽象基类"""
    
    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """执行搜索，返回结果列表
        
        每个结果格式: {"title": str, "url": str, "snippet": str}
        """
        ...
    
    def format_results(self, results: List[Dict]) -> str:
        """格式化搜索结果为文本（可复用的默认实现）"""
        if not results:
            return "未找到相关结果。"
        lines = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "无标题")
            snippet = r.get("snippet", r.get("body", ""))
            lines.append(f"{i}. {title}\n   {snippet}")
        return "\n\n".join(lines)


class DuckDuckGoSearch(BaseSearchProvider):
    """
    DuckDuckGo 搜索 - 完全免费，无需 API Key
    
    安装: pip install duckduckgo-search
    文档: https://github.com/deedy5/duckduckgo-search
    """
    
    def __init__(self):
        self._client = None
        
    def _get_client(self):
        """懒加载客户端"""
        if self._client is None:
            try:
                # 优先使用新的 ddgs 包
                try:
                    from ddgs import DDGS
                except ImportError:
                    # 兼容旧包名
                    from duckduckgo_search import DDGS
                self._client = DDGS()
            except ImportError:
                raise ImportError(
                    "DuckDuckGo 搜索需要安装: pip install ddgs"
                )
        return self._client
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        搜索 DuckDuckGo
        
        Args:
            query: 搜索查询
            max_results: 最大结果数（建议 3-5，太多容易被限流）
            
        Returns:
            搜索结果列表
        """
        try:
            client = self._get_client()
            
            # 添加随机延迟，避免被限流
            time.sleep(random.uniform(0.5, 1.5))
            
            results = client.text(
                query,
                max_results=max_results,
                region='wt-wt',  # 全球结果
                safesearch='moderate'
            )
            
            # 格式化结果
            formatted = []
            for r in results:
                formatted.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                    "source": "duckduckgo"
                })
            
            return formatted
            
        except Exception as e:
            print(f"DuckDuckGo 搜索失败: {e}")
            return []


class BingSearchFree(BaseSearchProvider):
    """
    Bing 搜索 - 有限免费额度
    
    每月 1000 次免费搜索（需要 Microsoft Azure 账号）
    注册: https://portal.azure.com -> Cognitive Services -> Bing Search
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.endpoint = "https://api.bing.microsoft.com/v7.0/search"
        
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Bing 搜索"""
        if not self.api_key:
            print("Bing 搜索需要 API Key，但每月有 1000 次免费额度")
            return []
        
        try:
            import requests
            
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            params = {
                "q": query,
                "count": max_results,
                "textDecorations": False,
                "textFormat": "HTML"
            }
            
            response = requests.get(
                self.endpoint,
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("webPages", {}).get("value", []):
                results.append({
                    "title": item.get("name", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "bing"
                })
            
            return results
            
        except Exception as e:
            print(f"Bing 搜索失败: {e}")
            return []


# 兼容旧接口的包装
class FreeSearchTool(BaseSearchProvider):
    """
    免费搜索工具主类
    优先使用 DuckDuckGo，失败时回退到其他免费方案
    """
    
    def __init__(self):
        self.providers = []
        
        # 优先尝试 DuckDuckGo（完全免费）
        try:
            from ddgs import DDGS  # 新的包名
            self.providers.append(DuckDuckGoSearch())
            print("✓ DuckDuckGo 搜索已启用（免费）")
        except ImportError:
            try:
                # 兼容旧包名
                from duckduckgo_search import DDGS
                self.providers.append(DuckDuckGoSearch())
                print("✓ DuckDuckGo 搜索已启用（免费）")
            except ImportError:
                print("⚠ DuckDuckGo 未安装: pip install ddgs")
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        搜索，自动尝试多个免费源
        """
        for provider in self.providers:
            results = provider.search(query, max_results)
            if results:
                return results
        
        return []


# 全局实例
_free_search_tool = None


def get_free_search_tool():
    """获取免费搜索工具实例"""
    global _free_search_tool
    if _free_search_tool is None:
        _free_search_tool = FreeSearchTool()
    return _free_search_tool


def search_web(query: str, max_results: int = 3) -> str:
    """
    搜索网络获取实时信息。

    适用于需要最新数据、具体人名、日期、事件验证等场景。
    当讨论涉及你不确定的事实、最新新闻、或需要验证其他参与者观点时使用。

    Args:
        query: 搜索查询词（建议用英文以获得更好结果）
        max_results: 返回结果数量（默认3条）

    Returns:
        格式化的搜索结果文本，每条包含标题和摘要
    """
    tool = get_free_search_tool()
    if not tool or not tool.providers:
        return "搜索服务暂不可用。"

    results = tool.search(query, max_results=max_results)
    if not results:
        return "未找到相关结果。"

    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "无标题")
        snippet = r.get("snippet", r.get("body", ""))
        lines.append(f"{i}. {title}\n   {snippet}")
    return "\n\n".join(lines)
