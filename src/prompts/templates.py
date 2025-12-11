"""
Prompt模板库
包含所有用于生成PPT的提示词模板
提示词 by claude code
"""


class PromptTemplates:
    """Prompt模板类，包含各种生成PPT所需的提示词模板"""
    # 大纲设计提示词
    SYSTEM_OUTLINE_DESIGNER = """你是一位资深的演示文稿设计师,擅长设计清晰、逻辑性强的PPT大纲。
        你的职责是:
        1. 理解用户的主题和需求
        2. 设计结构合理、层次分明的PPT大纲
        3. 确保每页都有明确的目标和内容重点
        4. 始终返回标准的JSON格式
        
        设计原则:
        - 第一页必须是封面(cover)
        - 最后一页必须是结束页(conclusion)
        - 中间是内容页(content)
        - 确保逻辑连贯,循序渐进
        - 标题简洁有力,一目了然
        """

    # 内容撰写提示词
    SYSTEM_CONTENT_WRITER = """你是一位专业的PPT内容撰写专家,擅长将复杂概念简化为清晰易懂的要点。
        你的职责是:
        1. 为每一页PPT创作高质量内容
        2. 使用简洁、专业的语言
        3. 确保每个要点都有价值
        4. 始终返回标准的JSON格式
        
        写作原则:
        - 每个要点控制在15-25字
        - 使用主动语态,避免冗余
        - 突出关键信息和数据
        - 适合口头演讲表达
        """

    @staticmethod
    def get_outline_prompt(topic: str, num_slides: int, style: str = "professional") -> str:
        """
        获取大纲生成提示词

        Args:
            topic: PPT主题
            num_slides: 页数
            style: 风格 (professional/creative/academic)

        Returns:
            完整的提示词
        """
        style_guide = {
            "professional": "商务专业风格,注重数据和逻辑",
            "creative": "创意风格,注重视觉冲击和故事性",
            "academic": "学术风格,注重理论深度和引用"
        }

        prompt = f"""
    			请为以下主题设计一个{num_slides}页的PPT大纲:

    			【主题】
    			{topic}

    			【风格要求】
    			{style_guide.get(style, style_guide["professional"])}

    			【结构要求】
    			- 总页数: {num_slides}页
    			- 第1页: 封面页(type: cover)
    			- 第{num_slides}页: 结束页(type: conclusion)  
    			- 中间页: 内容页(type: content)

    			【输出格式】
    			请严格按照以下JSON格式返回,不要添加任何markdown标记:

    			{{
    			  "title": "PPT的总标题(吸引人,概括主题)",
    			  "subtitle": "副标题(可选,补充说明)",
    			  "slides": [
    			    {{
    			      "page": 1,
    			      "title": "封面标题",
    			      "type": "cover",
    			      "description": "这页的作用和要传达的信息"
    			    }},
    			    {{
    			      "page": 2,
    			      "title": "内容页标题",
    			      "type": "content",
    			      "description": "这页的核心内容概要"
    			    }},
    			    ...
    			    {{
    			      "page": {num_slides},
    			      "title": "结束页标题",
    			      "type": "conclusion",
    			      "description": "总结和行动号召"
    			    }}
    			  ]
    			}}

    			【注意事项】
    			1. 确保逻辑流畅,从引入→展开→深入→总结
    			2. 每页标题要简洁有力,最多10个字
    			3. 避免重复和冗余内容
    			4. 只返回JSON,不要有其他文字
    		"""

        return prompt.strip()

    @staticmethod
    def get_content_prompt(
            slide_title: str,
            slide_description: str,
            overall_topic: str,
            page_number: int,
            total_pages: int,
            style: str = "professional"
    ) -> str:
        """
        获取单页内容生成提示词

        Args:
            slide_title: 页面标题
            slide_description: 页面描述
            overall_topic: 整体主题
            page_number: 当前页码
            total_pages: 总页数
            style: 风格

        Returns:
            完整的提示词
        """
        prompt = f"""
                请为PPT的第{page_number}/{total_pages}页创作详细内容:
    
                【整体主题】
                {overall_topic}
    
                【本页标题】
                {slide_title}
    
                【本页目标】
                {slide_description}
    
                【内容要求】
                1. 生成3-5个核心要点
                2. 每个要点15-25字,简洁有力
                3. 要点之间有逻辑关联
                4. 适合{style}风格
    
                【输出格式】
                请严格按照以下JSON格式返回:
    
                {{
                  "title": "{slide_title}",
                  "page_number": {page_number},
                  "content": [
                    "要点1:清晰表述核心观点",
                    "要点2:用数据或案例支撑",
                    "要点3:说明影响或意义",
                    "要点4:补充细节(可选)",
                    "要点5:总结或引申(可选)"
                  ],
                  "notes": "演讲者备注(可选,30-50字)"
                }}
    
                【写作技巧】
                - 使用主动语态
                - 包含具体数据或案例(如果相关)
                - 避免过于抽象的表述
                - 确保内容准确、专业
                - 只返回JSON,不要有其他文字
                """
        return prompt.strip()

    @staticmethod
    def get_cover_prompt(topic: str, subtitle: str = None) -> str:
        """获取封面页提示词"""
        prompt = f"""
                为PPT封面页设计内容:
    
                【主题】
                {topic}
    
                【要求】
                设计一个专业、吸引人的封面
    
                【输出格式】
                {{
                  "title": "主标题(简洁有力,8-15字)",
                  "subtitle": "副标题(补充说明,15-30字)",
                  "author": "演讲者/作者(可以留空)",
                  "date": "日期(可以是'2024年'或留空)"
                }}
    
                只返回JSON,不要其他内容。
                """
        return prompt.strip()

    @staticmethod
    def get_conclusion_prompt(topic: str, key_points: list) -> str:
        """获取结束页提示词"""
        points_text = "\n".join([f"- {p}" for p in key_points[:3]])

        prompt = f"""
                为PPT结束页设计内容:
    
                【主题】
                {topic}
    
                【关键要点回顾】
                {points_text}
    
                【要求】
                设计一个有力的结束,包含:
                1. 总结性标题
                2. 2-3个核心结论
                3. 行动号召(Call to Action)
    
                【输出格式】
                {{
                  "title": "结束页标题(如:'总结与展望')",
                  "page_number": -1,
                  "content": [
                    "核心结论1",
                    "核心结论2",
                    "行动号召或致谢"
                  ]
                }}
    
                只返回JSON。
                """
        return prompt.strip()


    @staticmethod
    def get_modification_prompt(
            original_content: dict,
            modification_request: str
    ) -> str:
        """
        获取内容修改提示词

        Args:
            original_content: 原始内容
            modification_request: 修改要求

        Returns:
            提示词
        """
        prompt = f"""
            请根据用户要求修改以下PPT内容:
    
            【原始内容】
            {original_content}
    
            【修改要求】
            {modification_request}
    
            【输出格式】
            返回修改后的完整JSON格式内容,保持原有结构:
            {{
              "title": "标题",
              "content": ["要点1", "要点2", ...]
            }}
    
            只返回JSON。
            """
        return prompt.strip()


    @staticmethod
    def get_style_guidelines(style: str) -> dict:
        """
        获取不同风格的详细指南

        Args:
            style: 风格类型

        Returns:
            风格指南字典
        """
        guidelines = {
            "professional": {
                "tone": "专业、严谨、客观",
                "language": "使用行业术语,强调数据和事实",
                "structure": "逻辑清晰,层次分明",
                "visuals": "简洁商务风格,蓝色或深色调"
            },
            "creative": {
                "tone": "生动、有趣、富有感染力",
                "language": "使用比喻和故事,语言活泼",
                "structure": "突破常规,注重视觉冲击",
                "visuals": "色彩丰富,图形化表达"
            },
            "academic": {
                "tone": "严谨、深入、理论性强",
                "language": "学术用语,引用文献",
                "structure": "遵循学术规范,论证充分",
                "visuals": "简洁专业,注重图表"
            },
            "startup": {
                "tone": "激情、创新、面向未来",
                "language": "强调愿景和影响力",
                "structure": "问题-方案-市场-团队",
                "visuals": "现代科技感,渐变色"
            },
            "teaching": {
                "tone": "清晰、循序渐进、互动性强",
                "language": "通俗易懂,多举例",
                "structure": "知识点→案例→练习→总结",
                "visuals": "直观图示,色彩明快"
            }
        }

        return guidelines.get(style, guidelines["professional"])


    @staticmethod
    # 快捷函数
    def create_outline_prompt(topic: str, num_slides: int = 10, style: str = "professional") -> tuple:
        """
        创建大纲生成的完整提示(系统+用户)

        Returns:
            (system_prompt, user_prompt)
        """
        return (
            PromptTemplates.SYSTEM_OUTLINE_DESIGNER,
            PromptTemplates.get_outline_prompt(topic, num_slides, style)
        )


    @staticmethod
    def create_content_prompt(
            slide_info: dict,
            overall_topic: str,
            total_pages: int,
            style: str = "professional"
    ) -> tuple:
        """
        创建内容生成的完整提示

        Returns:
            (system_prompt, user_prompt)
        """
        return (
            PromptTemplates.SYSTEM_CONTENT_WRITER,
            PromptTemplates.get_content_prompt(
                slide_info.get("title", ""),
                slide_info.get("description", ""),
                overall_topic,
                slide_info.get("page", 1),
                total_pages,
                style
            )
        )

