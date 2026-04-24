"""
搜索工具 - 为讨论提供实时信息检索能力
支持 Tavily、Serper 等搜索 API
"""
import os
import requests
from typing import List, Dict, Optional


class SearchTool:
    """网页搜索工具"""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "tavily"):
        """
        初始化搜索工具
        
        Args:
            api_key: API 密钥，默认从环境变量读取
            provider: 搜索提供商 (tavily/serper/bing)
        """
        self.provider = provider
        self.api_key = api_key or self._get_api_key_from_env()
        
    def _get_api_key_from_env(self) -> Optional[str]:
        """从环境变量获取 API 密钥"""
        if self.provider == "tavily":
            return os.environ.get("TAVILY_API_KEY")
        elif self.provider == "serper":
            return os.environ.get("SERPER_API_KEY")
        elif self.provider == "bing":
            return os.environ.get("BING_API_KEY")
        return None
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        执行搜索
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            搜索结果列表，每个结果包含 title, url, snippet
        """
        if not self.api_key:
            return []
            
        try:
            if self.provider == "tavily":
                return self._search_tavily(query, max_results)
            elif self.provider == "serper":
                return self._search_serper(query, max_results)
            else:
                return []
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
    
    def _search_tavily(self, query: str, max_results: int) -> List[Dict]:
        """Tavily 搜索 API"""
        url = "https://api.tavily.com/search"
        headers = {"Content-Type": "application/json"}
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "include_answer": False,
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for result in data.get("results", []):
            results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("content", ""),
            })
        return results
    
    def _search_serper(self, query: str, max_results: int) -> List[Dict]:
        """Serper (Google) 搜索 API"""
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {"q": query, "num": max_results}
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for result in data.get("organic", []):
            results.append({
                "title": result.get("title", ""),
                "url": result.get("link", ""),
                "snippet": result.get("snippet", ""),
            })
        return results
    
    def format_results(self, results: List[Dict]) -> str:
        """格式化搜索结果为文本"""
        if not results:
            return ""
        
        lines = ["【搜索结果】"]
        for i, r in enumerate(results[:3], 1):
            lines.append(f"{i}. {r['title']}")
            lines.append(f"   {r['snippet'][:150]}...")
        return "\n".join(lines)


# 全局搜索工具实例（懒加载）
_search_tool: Optional[SearchTool] = None
_free_search: Optional["FreeSearchTool"] = None


def get_search_tool() -> Optional[SearchTool]:
    """获取全局搜索工具实例"""
    global _search_tool
    if _search_tool is None:
        # 尝试从环境变量自动配置（付费方案）
        if os.environ.get("TAVILY_API_KEY"):
            _search_tool = SearchTool(provider="tavily")
        elif os.environ.get("SERPER_API_KEY"):
            _search_tool = SearchTool(provider="serper")
    return _search_tool


def get_free_search_tool():
    """获取免费搜索工具实例（无需 API Key）"""
    global _free_search
    if _free_search is None:
        try:
            from tools.search_free import FreeSearchTool
            _free_search = FreeSearchTool()
        except ImportError:
            return None
    return _free_search
