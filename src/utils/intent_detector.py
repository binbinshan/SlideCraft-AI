"""
Intent Detector - 使用LLM检测用户意图
"""
import json
import re
from typing import Dict, Optional, Tuple
from openai import OpenAI
from prompts.templates import PromptTemplates
from utils.helpers import parse_json_response


class IntentDetector:
    """用户意图检测器"""

    INTENT_TYPES = {
        "create_ppt": "创建PPT",
        "modify_ppt": "修改PPT",
        "view_content": "查看内容",
        "download_ppt": "下载PPT",
        "ask_help": "询问帮助",
        "check_status": "查看状态",
        "general_chat": "一般对话"
    }

    def __init__(self, api_key: str, base_url: str = None, model: str = "gpt-3.5-turbo"):
        """
        初始化意图检测器

        Args:
            api_key: OpenAI API密钥
            base_url: API基础URL（可选）
            model: 使用的模型
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model

    def detect_intent(self, message: str, context: Dict = None) -> Tuple[str, Dict]:
        """
        检测用户意图

        Args:
            message: 用户消息
            context: 会话上下文（包含之前的对话信息）

        Returns:
            Tuple[intent_type, extracted_params)
        """
        # 构建提示词
        system_prompt = PromptTemplates.build_intent_system_prompt(context)
        user_prompt = PromptTemplates.build_intent_user_prompt(message)

        try:
            # 调用LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            response_text = response.choices[0].message.content.strip()
            modified_content = parse_json_response(response_text)
            # 解析响应
            result = self._parse_llm_response(response_text,modified_content)
            return result

        except Exception as e:
            print(f"Intent detection error: {e}")
            # 返回默认意图
            return "general_chat", {"error": str(e)}





    def _parse_llm_response(self, content : str,modified_content: dict) -> Tuple[str, Dict]:
        """解析LLM响应"""
        try:
            # 尝试直接解析JSON
            intent = modified_content.get("intent", "general_chat")
            parameters = modified_content.get("parameters", {})
            confidence = modified_content.get("confidence", 0.0)
            response_suggestion = modified_content.get("response_suggestion", "")

            # 添加额外的解析结果
            parameters.update({
                "confidence": confidence,
                "response_suggestion": response_suggestion,
                "raw_response": content
            })

            return intent, parameters

        except json.JSONDecodeError:
            # 如果JSON解析失败，尝试从文本中提取信息
            return self._fallback_parse(content)

    def _fallback_parse(self, response: str) -> Tuple[str, Dict]:
        """备用解析方法"""
        # 简单的关键词匹配作为备用
        response_lower = response.lower()

        if any(word in response_lower for word in ["create", "生成", "创建", "做", "制作"]):
            return "create_ppt", {"response_suggestion": response}
        elif any(word in response_lower for word in ["modify", "修改", "改", "调整"]):
            return "modify_ppt", {"response_suggestion": response}
        elif any(word in response_lower for word in ["view", "查看", "看看", "显示"]):
            return "view_content", {"response_suggestion": response}
        elif any(word in response_lower for word in ["download", "下载"]):
            return "download_ppt", {"response_suggestion": response}
        elif any(word in response_lower for word in ["help", "帮助", "怎么", "如何"]):
            return "ask_help", {"response_suggestion": response}
        elif any(word in response_lower for word in ["status", "进度", "状态"]):
            return "check_status", {"response_suggestion": response}
        else:
            return "general_chat", {"response_suggestion": response}

    def extract_topic_from_message(self, message: str) -> Optional[str]:
        """从消息中提取PPT主题"""
        patterns = [
            r'(?:关于|主题是|做成).*?([^\n，。！？]+)(?:的?[pP][pP][tT]|的演示文稿)?',
            r'([pP][pP][tT]).*?关于([^\n，。！？]+)',
            r'(?:创建|生成|做一个).*?([^\n，。！？]+)(?:的?[pP][pP][tT])?',
        ]

        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                topic = match.group(1) if match.lastindex == 1 else match.group(2)
                if topic and len(topic.strip()) > 2:
                    return topic.strip()

        return None

    def extract_page_number(self, message: str) -> Optional[int]:
        """从消息中提取页码"""
        patterns = [
            r'第\s*(\d+)\s*[页张]',
            r'(\d+)\s*[页张]',
            r'page\s*(\d+)',
            r'slide\s*(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

        return None