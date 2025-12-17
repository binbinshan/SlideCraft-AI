"""
基于 LangChain 的内容生成 Agent
提供更好的提示词管理和链式调用能力
"""
from typing import Dict, List, Optional, Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory

from prompts.templates import PromptTemplates


class LangChainContentAgent:
    """基于 LangChain 的内容生成 Agent"""

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com",
        temperature: float = 0.7,
        max_retries: int = 3
    ):
        """
        初始化 LangChain Content Agent

        Args:
            api_key: API密钥
            model: 模型名称
            base_url: API基础URL
            temperature: 温度参数
            max_retries: 最大重试次数
        """
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries

        # 初始化 LLM
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_retries=max_retries
        )

        # 保存最后生成的内容
        self.last_outline = None
        self.last_contents = None

        # 初始化对话记忆
        self.memory = ChatMessageHistory()

        # 创建提示词模板
        self._create_prompts()

    def _create_prompts(self):
        """创建各种提示词模板"""

        # 大纲生成提示词
        self.outline_prompt = ChatPromptTemplate.from_messages([
            ("system", PromptTemplates.SYSTEM_OUTLINE_DESIGNER),
            ("human", "{user_prompt}")
        ])

        # 内容生成提示词
        self.content_prompt = ChatPromptTemplate.from_messages([
            ("system", PromptTemplates.SYSTEM_CONTENT_WRITER),
            ("human", "{user_prompt}")
        ])

        # 内容修改提示词
        self.modification_prompt = ChatPromptTemplate.from_messages([
            ("system", PromptTemplates.SYSTEM_CONTENT_WRITER),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{modification_request}")
        ])

        # 结束页提示词
        self.conclusion_prompt = ChatPromptTemplate.from_messages([
            ("system", PromptTemplates.SYSTEM_CONTENT_WRITER),
            ("human", "{user_prompt}")
        ])

        # 输出解析器
        self.json_parser = JsonOutputParser()

    def generate_outline(
        self,
        topic: str,
        num_slides: int = 10,
        style: str = "professional"
    ) -> Dict:
        """
        使用 LangChain 生成大纲

        Args:
            topic: PPT主题
            num_slides: 页数
            style: 风格

        Returns:
            大纲字典
        """
        print(f"🤖 LangChain 生成大纲: {topic} ({num_slides}页, {style}风格)")

        # 创建用户提示词
        _, user_prompt = PromptTemplates.create_outline_prompt(topic, num_slides, style)

        # 创建链
        chain = (
            {"user_prompt": RunnablePassthrough()}
            | self.outline_prompt
            | self.llm
            | self.json_parser
        )

        try:
            # 执行链
            outline = chain.invoke(user_prompt)

            # 验证大纲格式
            self._validate_outline(outline, num_slides)

            print(f"✅ 大纲生成成功: {outline['title']}")
            self.last_outline = outline
            return outline

        except Exception as e:
            print(f"⚠️ 大纲生成失败: {str(e)}")
            raise

    async def generate_outline_async(
        self,
        topic: str,
        num_slides: int = 10,
        style: str = "professional"
    ) -> Dict:
        """异步生成大纲"""
        print(f"🤖 LangChain 异步生成大纲: {topic}")

        _, user_prompt = PromptTemplates.create_outline_prompt(topic, num_slides, style)

        chain = (
            {"user_prompt": RunnablePassthrough()}
            | self.outline_prompt
            | self.llm
            | self.json_parser
        )

        try:
            outline = await chain.ainvoke(user_prompt)
            self._validate_outline(outline, num_slides)
            self.last_outline = outline
            return outline
        except Exception as e:
            print(f"⚠️ 异步大纲生成失败: {str(e)}")
            raise

    def generate_slide_content(
        self,
        slide_info: Dict,
        overall_topic: str,
        total_pages: int,
        style: str = "professional"
    ) -> Dict:
        """
        生成单页内容

        Args:
            slide_info: 页面信息
            overall_topic: 整体主题
            total_pages: 总页数
            style: 风格

        Returns:
            内容字典
        """
        slide_type = slide_info.get("type", "content")
        page_num = slide_info.get("page", 1)

        print(f"   📝 第{page_num}页: {slide_info.get('title', '')}")

        if slide_type == "cover":
            return self._generate_cover_content(slide_info, overall_topic)
        elif slide_type == "conclusion":
            return self._generate_conclusion_content(slide_info, overall_topic, total_pages)
        else:
            return self._generate_content_page(slide_info, overall_topic, total_pages, style)

    async def generate_slide_content_async(
        self,
        slide_info: Dict,
        overall_topic: str,
        total_pages: int,
        style: str = "professional"
    ) -> Dict:
        """异步生成单页内容"""
        slide_type = slide_info.get("type", "content")

        if slide_type == "cover":
            return self._generate_cover_content(slide_info, overall_topic)
        elif slide_type == "conclusion":
            return await self._generate_conclusion_content_async(
                slide_info, overall_topic, total_pages
            )
        else:
            return await self._generate_content_page_async(
                slide_info, overall_topic, total_pages, style
            )

    def _generate_cover_content(self, slide_info: Dict, topic: str) -> Dict:
        """生成封面页内容"""
        return {
            "title": slide_info.get("title", topic),
            "subtitle": slide_info.get("description", f"关于{topic}的深入探讨"),
            "page_number": 1,
            "content": [],
            "type": "cover"
        }

    def _generate_conclusion_content(self, slide_info: Dict, topic: str, total_pages: int) -> Dict:
        """生成结束页内容"""
        user_prompt = PromptTemplates.get_conclusion_prompt(
            topic,
            [],  # 可以传入关键要点
            total_pages
        )

        chain = (
            {"user_prompt": RunnablePassthrough()}
            | self.conclusion_prompt
            | self.llm
            | self.json_parser
        )

        try:
            content = chain.invoke(user_prompt)
            content["type"] = "conclusion"
            return content
        except Exception as e:
            print(f"      ⚠️ 使用默认结束页: {str(e)}")
            return {
                "title": slide_info.get("title", "谢谢"),
                "content": ["感谢您的聆听", "欢迎提问与交流"],
                "type": "conclusion"
            }

    async def _generate_conclusion_content_async(
        self, slide_info: Dict, topic: str, total_pages: int
    ) -> Dict:
        """异步生成结束页内容"""
        user_prompt = PromptTemplates.get_conclusion_prompt(
            topic, [], total_pages
        )

        chain = (
            {"user_prompt": RunnablePassthrough()}
            | self.conclusion_prompt
            | self.llm
            | self.json_parser
        )

        try:
            content = await chain.ainvoke(user_prompt)
            content["type"] = "conclusion"
            return content
        except Exception as e:
            print(f"      ⚠️ 使用默认结束页: {str(e)}")
            return {
                "title": slide_info.get("title", "谢谢"),
                "content": ["感谢您的聆听", "欢迎提问与交流"],
                "type": "conclusion"
            }

    def _generate_content_page(
        self,
        slide_info: Dict,
        overall_topic: str,
        total_pages: int,
        style: str
    ) -> Dict:
        """生成内容页"""
        system_prompt, user_prompt = PromptTemplates.create_content_prompt(
            slide_info, overall_topic, total_pages, style
        )

        # 使用自定义系统提示词
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt)
        ])

        chain = (
            {"user_prompt": RunnablePassthrough()}
            | prompt
            | self.llm
            | self.json_parser
        )

        try:
            content = chain.invoke("")
            content["type"] = "content"
            return content
        except Exception as e:
            print(f"      ⚠️ 使用默认内容: {str(e)}")
            return {
                "title": slide_info.get("title", ""),
                "content": ["内容生成中...", "请稍候..."],
                "type": "content"
            }

    async def _generate_content_page_async(
        self,
        slide_info: Dict,
        overall_topic: str,
        total_pages: int,
        style: str
    ) -> Dict:
        """异步生成内容页"""
        system_prompt, user_prompt = PromptTemplates.create_content_prompt(
            slide_info, overall_topic, total_pages, style
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt)
        ])

        chain = (
            {"user_prompt": RunnablePassthrough()}
            | prompt
            | self.llm
            | self.json_parser
        )

        try:
            content = await chain.ainvoke("")
            content["type"] = "content"
            return content
        except Exception as e:
            print(f"      ⚠️ 使用默认内容: {str(e)}")
            return {
                "title": slide_info.get("title", ""),
                "content": ["内容生成中...", "请稍候..."],
                "type": "content"
            }

    def modify_content(
        self,
        original_content: Dict,
        modification_request: str
    ) -> Dict:
        """
        修改内容（带对话记忆）

        Args:
            original_content: 原始内容
            modification_request: 修改要求

        Returns:
            修改后的内容
        """
        print(f"🔄 LangChain 修改内容: {modification_request}")

        # 转换为对话格式
        self.memory.add_user_message(
            f"原始内容: {original_content}"
        )
        self.memory.add_ai_message(
            f"已理解原始内容"
        )

        chain = (
            {
                "modification_request": RunnablePassthrough(),
                "chat_history": lambda x: self.memory.messages
            }
            | self.modification_prompt
            | self.llm
            | self.json_parser
        )

        try:
            modified_content = chain.invoke(modification_request)

            # 更新记忆
            self.memory.add_user_message(modification_request)
            self.memory.add_ai_message(
                f"已修改内容: {modified_content}"
            )

            print(f"✅ 内容修改完成")
            return modified_content

        except Exception as e:
            print(f"❌ 修改失败: {str(e)}")
            return original_content

    def generate_batch_contents(
        self,
        slides_info: List[Dict],
        overall_topic: str,
        total_pages: int,
        style: str = "professional"
    ) -> List[Dict]:
        """
        批量生成内容（使用并行处理）

        Args:
            slides_info: 页面信息列表
            overall_topic: 整体主题
            total_pages: 总页数
            style: 风格

        Returns:
            内容列表
        """
        from langchain.schema.runnable import RunnableParallel

        print(f"🚀 并行生成 {len(slides_info)} 页内容...")

        # 创建并行任务
        tasks = []
        for slide_info in slides_info:
            task = {
                "slide_info": slide_info,
                "generate": RunnablePassthrough.assign(
                    content=lambda x: self.generate_slide_content(
                        x["slide_info"],
                        overall_topic,
                        total_pages,
                        style
                    )
                )
            }
            tasks.append(task)

        # 执行并行任务
        try:
            results = []
            for slide_info in slides_info:
                content = self.generate_slide_content(
                    slide_info, overall_topic, total_pages, style
                )
                results.append(content)

            self.last_contents = results
            return results

        except Exception as e:
            print(f"⚠️ 批量生成失败: {str(e)}")
            raise

    async def generate_batch_contents_async(
        self,
        slides_info: List[Dict],
        overall_topic: str,
        total_pages: int,
        style: str = "professional"
    ) -> List[Dict]:
        """异步批量生成内容"""
        import asyncio

        tasks = [
            self.generate_slide_content_async(
                slide_info, overall_topic, total_pages, style
            )
            for slide_info in slides_info
        ]

        try:
            results = await asyncio.gather(*tasks)
            self.last_contents = results
            return results
        except Exception as e:
            print(f"⚠️ 异步批量生成失败: {str(e)}")
            raise

    def _validate_outline(self, outline: Dict, expected_slides: int) -> None:
        """验证大纲格式"""
        if "title" not in outline:
            raise ValueError("大纲缺少title字段")

        if "slides" not in outline or not isinstance(outline["slides"], list):
            raise ValueError("大纲缺少slides数组")

        if len(outline["slides"]) < expected_slides - 2:
            print(f"⚠️ 警告: 生成的页数({len(outline['slides'])})少于预期({expected_slides})")

        if outline["slides"][0].get("type") != "cover":
            print("⚠️ 警告: 第一页不是封面页")

        if outline["slides"][-1].get("type") != "conclusion":
            print("⚠️ 警告: 最后一页不是结束页")