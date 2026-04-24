"""
使用 Kimi API 的 Function Calling 实现搜索
比文本解析更可靠
"""
import json
from typing import List, Dict, Any, Optional
from tools.search import SearchTool


class KimiFunctionSearch:
    """
    使用 Kimi API 的 function calling 能力实现搜索工具调用
    
    文档：https://platform.moonshot.cn/docs/api/chat#function-calling
    """
    
    def __init__(self, router, search_tool: Optional[SearchTool] = None):
        self.router = router
        self.search_tool = search_tool or SearchTool()
        
    def run(
        self,
        system_prompt: str,
        conversation: List[Dict[str, str]],
        max_iterations: int = 3
    ) -> str:
        """
        运行带搜索的对话
        """
        # 定义工具（OpenAI 格式）
        tools = [{
            "type": "function",
            "function": {
                "name": "search",
                "description": "搜索网络信息，获取实时数据",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索查询内容"
                        }
                    },
                    "required": ["query"]
                }
            }
        }]
        
        messages = conversation.copy()
        
        for i in range(max_iterations):
            # 调用 Kimi API，传入 tools
            response = self.router.chat_with_tools(
                messages=messages,
                system=system_prompt,
                tools=tools,
                max_tokens=2000,
                temperature=0.7,
            )
            
            # 检查是否有工具调用
            tool_calls = response.get("tool_calls", [])
            
            if not tool_calls:
                # 没有工具调用，直接返回内容
                return response.get("content", "")
            
            # 执行工具调用
            for tool_call in tool_calls:
                if tool_call["function"]["name"] == "search":
                    # 解析参数
                    arguments = json.loads(tool_call["function"]["arguments"])
                    query = arguments.get("query", "")
                    
                    # 执行搜索
                    search_results = self._do_search(query)
                    
                    # 添加工具调用结果到对话
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": search_results
                    })
        
        # 达到最大迭代次数，返回最后一次响应
        return response.get("content", "")
    
    def _do_search(self, query: str) -> str:
        """执行搜索并格式化结果"""
        try:
            results = self.search_tool.search(query, max_results=3)
            if not results:
                return "未找到相关信息"
            
            lines = []
            for i, r in enumerate(results, 1):
                lines.append(f"{i}. {r['title']}: {r['snippet'][:200]}")
            return "\n".join(lines)
        except Exception as e:
            return f"搜索失败: {e}"


# 兼容旧接口的包装器
class SearchToolWrapper:
    """
    给不支持 function calling 的模型用的简化版
    直接在 prompt 里告诉模型可以搜索
    """
    
    def __init__(self, router, search_tool: Optional[SearchTool] = None):
        self.router = router
        self.search_tool = search_tool or SearchTool()
    
    def run(
        self,
        system_prompt: str,
        conversation: List[Dict[str, str]],
        max_iterations: int = 2
    ) -> str:
        """
        使用 prompt engineering 实现类似效果
        """
        enhanced_system = f"""{system_prompt}

当你需要搜索信息时，请在回复中包含以下格式：
SEARCH: <搜索查询内容>

系统会自动搜索并将结果返回给你，然后你可以基于搜索结果继续回答。
"""
        
        messages = conversation.copy()
        
        for i in range(max_iterations):
            response = self.router.chat(
                messages=messages,
                system=enhanced_system,
                max_tokens=2000,
                temperature=0.7,
            )
            
            # 检查是否需要搜索
            if "SEARCH:" in response:
                # 提取搜索查询
                import re
                search_match = re.search(r'SEARCH:\s*(.+?)(?:\n|$)', response)
                if search_match:
                    query = search_match.group(1).strip()
                    results = self._do_search(query)
                    
                    # 添加搜索结果到对话
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user", 
                        "content": f"搜索结果：\n{results}\n\n请基于以上搜索结果回答。"
                    })
                    continue
            
            # 不需要搜索，直接返回
            return response
        
        return response
    
    def _do_search(self, query: str) -> str:
        """执行搜索"""
        try:
            results = self.search_tool.search(query, max_results=3)
            if not results:
                return "未找到相关信息"
            
            lines = []
            for i, r in enumerate(results, 1):
                lines.append(f"{i}. {r['title']}\n   {r['snippet'][:200]}")
            return "\n".join(lines)
        except Exception as e:
            return f"搜索失败: {e}"
