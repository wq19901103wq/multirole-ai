"""
ReAct 引擎 - 支持工具调用的推理循环
Agent 可以自主决定何时调用搜索工具
"""
import re
from typing import List, Dict, Optional
from tools.search import SearchTool, get_free_search_tool


class ToolCallingEngine:
    """
    使用 OpenAI 风格的 function calling 实现工具调用
    更现代的方式
    """
    
    def __init__(self, router, search_tool: Optional[SearchTool] = None):
        self.router = router
        
        # 优先使用免费搜索（DuckDuckGo）
        if search_tool is None:
            free_search = get_free_search_tool()
            if free_search:
                self.search_tool = free_search
                print("[ReAct] 使用免费搜索（DuckDuckGo）")
            else:
                self.search_tool = SearchTool()
        else:
            self.search_tool = search_tool
            
        self.available_tools = {
            "search": self._search_wrapper,
        }
    
    def run(
        self,
        system_prompt: str,
        conversation: List[Dict[str, str]],
        max_iterations: int = 3
    ) -> str:
        """
        运行工具调用循环
        """
        messages = conversation.copy()
        
        # 添加工具说明到系统提示
        tools_description = """
你可以调用以下工具：

[TOOL] search
参数: query (string) - 搜索查询
用途: 搜索网络获取实时信息

当你需要搜索时，请回复：
TOOL_CALL: search
query: <搜索内容>

如果不需要工具，直接给出回答。"""
        
        enhanced_system = system_prompt + tools_description
        
        for i in range(max_iterations):
            response = self.router.chat(
                messages=messages,
                system=enhanced_system,
                max_tokens=2000,
                temperature=0.7,
            )
            
            # 检查是否有工具调用（支持多种格式）
            # 格式1: TOOL_CALL: tool_name\nparam: value
            # 格式2: TOOL_CALL: tool_name\nquery: <多行查询>
            tool_call_match = re.search(
                r'TOOL_CALL:\s*(\w+)\s*\n((?:[^:]+:[^\n]*\n?)*)',
                response, re.DOTALL
            )
            
            # 备选：更宽松的匹配
            if not tool_call_match:
                tool_call_match = re.search(
                    r'TOOL_CALL:\s*(\w+)\s*\n(.+?)(?:\n\n|\Z)',
                    response, re.DOTALL
                )
            
            if tool_call_match:
                tool_name = tool_call_match.group(1).strip().lower()
                params_text = tool_call_match.group(2)
                
                # 解析参数（支持多行值）
                params = {}
                current_key = None
                for line in params_text.strip().split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    if ':' in line and not line.startswith('"') and not line.startswith("'"):
                        # 可能是新的key:value对
                        parts = line.split(':', 1)
                        key = parts[0].strip()
                        value = parts[1].strip() if len(parts) > 1 else ""
                        # 如果key看起来像参数名（不含空格或特殊字符）
                        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                            current_key = key
                            params[current_key] = value
                        elif current_key:
                            # 可能是当前参数值的续行
                            params[current_key] += " " + line
                    elif current_key:
                        # 当前参数值的续行
                        params[current_key] += " " + line
                
                # 执行工具
                if tool_name in self.available_tools:
                    result = self.available_tools[tool_name](params)
                    
                    # 添加工具调用和结果到对话
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user", 
                        "content": f"[TOOL_RESULT] {tool_name}\n{result}\n\n基于以上结果继续回答。"
                    })
                else:
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": f"[TOOL_RESULT] 错误: 未知工具 '{tool_name}'，可用工具: {list(self.available_tools.keys())}"
                    })
            else:
                # 没有工具调用，返回最终答案
                return response
        
        return response
    
    def _search_wrapper(self, params: Dict[str, str]) -> str:
        """搜索工具包装器"""
        query = params.get("query", "")
        if not query:
            return "错误: 缺少 query 参数"
        
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


def run_with_tool_fallback(
    router,
    system_prompt: str,
    conversation: List[Dict[str, str]],
    max_iterations: int = 2,
    max_tokens: int = 4000,
    temperature: float = 0.5,
) -> str:
    """统一的 ReAct 调用 + 降级逻辑

    优先使用免费搜索，失败回退到付费搜索，
    再失败则降级为直接 LLM 调用。
    """
    from tools.search_free import get_free_search_tool
    from tools.search import get_search_tool

    # 尝试免费搜索
    search_tool = get_free_search_tool()
    if not search_tool:
        search_tool = get_search_tool()

    if search_tool:
        try:
            engine = ToolCallingEngine(router, search_tool)
            return engine.run(
                system_prompt=system_prompt,
                conversation=conversation,
                max_iterations=max_iterations,
            )
        except Exception:
            pass  # 降级到直接 LLM 调用

    # 降级：直接调用 LLM
    return router.chat(
        messages=conversation,
        system=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )
