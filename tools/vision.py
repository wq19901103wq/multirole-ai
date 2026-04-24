"""
多模态（图片）分析工具
使用 Kimi K2.5 API 分析图片
"""
import base64

from model_router.router import ModelRouter


class VisionAnalyzer:
    """
    图片分析器 - 使用 Kimi K2.5 的多模态能力
    """
    
    def __init__(self, router: ModelRouter):
        self.router = router
    
    def analyze_image(
        self,
        image_path: str,
        prompt: str = "描述这张图片的内容",
        system_prompt: str = "你是一个视觉分析助手，请详细描述图片内容。"
    ) -> str:
        """
        分析本地图片
        
        Args:
            image_path: 图片文件路径
            prompt: 用户问题
            system_prompt: 系统提示
            
        Returns:
            分析结果
        """
        # 读取图片并转为 base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # 构建多模态消息
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]
        }]
        
        # 调用 Kimi API
        # 注意：需要确保 router 使用的是支持 vision 的模型（kimi-k2.5）
        return self.router.chat(
            messages=messages,
            system=system_prompt,
            max_tokens=2000,
            temperature=0.7
        )
    
    def analyze_image_url(
        self,
        image_url: str,
        prompt: str = "描述这张图片的内容",
        system_prompt: str = "你是一个视觉分析助手，请详细描述图片内容。"
    ) -> str:
        """
        分析网络图片
        
        Args:
            image_url: 图片 URL
            prompt: 用户问题
            system_prompt: 系统提示
            
        Returns:
            分析结果
        """
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                }
            ]
        }]
        
        return self.router.chat(
            messages=messages,
            system=system_prompt,
            max_tokens=2000,
            temperature=0.7
        )


# 使用示例
if __name__ == "__main__":
    from model_router.providers.kimi import KimiProvider
    from model_router.router import ModelRouter
    
    # 初始化（需要设置 KIMI_API_KEY）
    router = ModelRouter(KimiProvider(model="kimi-k2.5"))
    analyzer = VisionAnalyzer(router)
    
    # 分析图片
    # result = analyzer.analyze_image("path/to/image.jpg")
    # print(result)
