"""
ContentAgent - 负责PPT内容生成的AI Agent
"""
import json
import re
import time
from typing import Dict, List, Optional
from openai import OpenAI

from prompts.templates import PromptTemplates


class ContentAgent:
    """内容生成Agent"""

    def __init__(
            self,
            api_key: str,
            model: str = "gpt-4o",
            max_retries: int = 3
    ):
        """
        初始化ContentAgent

        Args:
            api_key: OpenAI API密钥
            model: 使用的模型
            use_proxy: 是否使用代理
            max_retries: 最大重试次数
        """
        self.model = model
        self.max_retries = max_retries

        # 创建客户端

        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


    def generate_outline(
            self,
            topic: str,
            num_slides: int = 10,
            style: str = "professional"
    ) -> Dict:
        """
        生成PPT大纲

        Args:
            topic: PPT主题
            num_slides: 页数
            style: 风格(professional/creative/academic/startup/teaching)

        Returns:
            大纲字典,包含title, subtitle, slides

        Raises:
            Exception: 生成失败
        """
        print(f"🤖 生成大纲: {topic} ({num_slides}页, {style}风格)")

        system_prompt, user_prompt = PromptTemplates.create_outline_prompt(topic, num_slides, style)

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=2048,
                    temperature=0.7
                )

                response_text = response.choices[0].message.content.strip()

                # 清理JSON
                outline = self._parse_json_response(response_text)

                # 验证大纲格式
                self._validate_outline(outline, num_slides)

                print(f"✅ 大纲生成成功: {outline['title']}")
                return outline

            except json.JSONDecodeError as e:
                print(f"⚠️  JSON解析失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    raise Exception(f"大纲生成失败: JSON解析错误 - {str(e)}")

            except Exception as e:
                print(f"⚠️  生成失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise

    def generate_slide_content(
            self,
            slide_info: Dict,
            overall_topic: str,
            total_pages: int,
            style: str = "professional"
    ) -> Dict:
        """
        为单页生成详细内容

        Args:
            slide_info: 页面信息(包含page, title, type, description)
            overall_topic: 整体主题
            total_pages: 总页数
            style: 风格

        Returns:
            内容字典,包含title, content, notes
        """
        slide_type = slide_info.get("type", "content")
        page_num = slide_info.get("page", 1)

        print(f"   📝 第{page_num}页: {slide_info.get('title', '')}")

        # 根据页面类型选择不同的生成策略
        if slide_type == "cover":
            return self._generate_cover_content(slide_info, overall_topic)
        elif slide_type == "conclusion":
            return self._generate_conclusion_content(slide_info, overall_topic)
        else:
            return self._generate_content_page(slide_info, overall_topic, total_pages, style)

    def _generate_cover_content(self, slide_info: Dict, topic: str) -> Dict:
        """生成封面页内容"""
        return {
            "title": slide_info.get("title", topic),
            "subtitle": slide_info.get("description", f"关于{topic}的深入探讨"),
            "page_number": 1,
            "content": [],
            "type": "cover"
        }

    def _generate_conclusion_content(self, slide_info: Dict, topic: str) -> Dict:
        """生成结束页内容"""
        prompt = PromptTemplates.get_conclusion_prompt(
            topic,
            []  # 这里可以传入关键要点
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": PromptTemplates.SYSTEM_CONTENT_WRITER},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=512,
                temperature=0.7
            )

            response_text = response.choices[0].message.content.strip()
            content = self._parse_json_response(response_text)
            content["type"] = "conclusion"
            return content

        except Exception as e:
            print(f"      ⚠️  使用默认结束页: {str(e)}")
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
            slide_info,
            overall_topic,
            total_pages,
            style
        )

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=1024,
                    temperature=0.7
                )

                response_text = response.choices[0].message.content.strip()
                content = self._parse_json_response(response_text)
                content["type"] = "content"
                return content

            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    print(f"      ⚠️  使用默认内容: {str(e)}")
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
        修改已生成的内容

        Args:
            original_content: 原始内容
            modification_request: 修改要求

        Returns:
            修改后的内容
        """
        print(f"🔄 修改内容: {modification_request}")

        prompt = PromptTemplates.get_modification_prompt(
            original_content,
            modification_request
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": PromptTemplates.SYSTEM_CONTENT_WRITER},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024,
                temperature=0.7
            )

            response_text = response.choices[0].message.content.strip()
            modified_content = self._parse_json_response(response_text)

            print(f"✅ 内容修改完成")
            return modified_content

        except Exception as e:
            print(f"❌ 修改失败: {str(e)}")
            return original_content

    def _parse_json_response(self, response_text: str) -> Dict:
        """
        解析JSON响应,处理各种格式问题

        Args:
            response_text: 原始响应文本

        Returns:
            解析后的字典
        """
        # 移除markdown标记
        text = re.sub(r'^```json\s*|\s*```$', '', response_text, flags=re.MULTILINE)
        text = re.sub(r'^```\s*|\s*```$', '', text, flags=re.MULTILINE)
        text = text.strip()

        # 尝试解析
        return json.loads(text)

    def _validate_outline(self, outline: Dict, expected_slides: int) -> None:
        """
        验证大纲格式

        Args:
            outline: 大纲字典
            expected_slides: 期望的页数

        Raises:
            ValueError: 格式不正确
        """
        if "title" not in outline:
            raise ValueError("大纲缺少title字段")

        if "slides" not in outline or not isinstance(outline["slides"], list):
            raise ValueError("大纲缺少slides数组")

        if len(outline["slides"]) < expected_slides - 2:
            print(f"⚠️  警告: 生成的页数({len(outline['slides'])})少于预期({expected_slides})")

        # 验证第一页和最后一页
        if outline["slides"][0].get("type") != "cover":
            print("⚠️  警告: 第一页不是封面页")

        if outline["slides"][-1].get("type") != "conclusion":
            print("⚠️  警告: 最后一页不是结束页")
