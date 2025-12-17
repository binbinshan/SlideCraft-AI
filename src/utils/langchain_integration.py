"""
LangChain/LangGraph 集成工具
提供统一的接口和工具函数
"""
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
import asyncio
import json
from datetime import datetime
from pathlib import Path

from langchain_core.tools import tool
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_community.chat_message_histories import ChatMessageHistory

from graph.ppt_workflow import PPTWorkflow, PPTGenerationState
from graph.advanced_workflow import AdvancedPPTWorkflow, AdvancedPPTState
from agents.langchain_content_agent import LangChainContentAgent
from utils.helpers import Logger, format_timestamp


class PPTGenerationCallbackHandler(BaseCallbackHandler):
    """PPT生成过程的回调处理器"""

    def __init__(self, logger: Logger = None):
        self.logger = logger or Logger()
        self.steps = []
        self.tokens_used = 0
        self.start_time = None

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """LLM开始时调用"""
        if not self.start_time:
            self.start_time = datetime.now()
        self.logger.info(f"LLM开始处理 {len(prompts)} 个提示")

    def on_llm_end(self, response, **kwargs) -> None:
        """LLM结束时调用"""
        self.tokens_used += response.llm_output.get('token_usage', {}).get('total_tokens', 0)
        self.logger.info(f"LLM处理完成，累计使用 {self.tokens_used} tokens")

    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs) -> None:
        """链开始时调用"""
        step_name = serialized.get('name', 'Unknown')
        self.steps.append(step_name)
        self.logger.info(f"开始执行步骤: {step_name}")

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs) -> None:
        """链结束时调用"""
        step_name = self.steps[-1] if self.steps else 'Unknown'
        self.logger.info(f"步骤完成: {step_name}")

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """工具开始时调用"""
        tool_name = serialized.get('name', 'Unknown')
        self.logger.info(f"使用工具: {tool_name}")

    def on_tool_end(self, output: str, **kwargs) -> None:
        """工具结束时调用"""
        self.logger.info("工具执行完成")


class LangChainIntegration:
    """LangChain 集成工具类"""

    def __init__(self, config: Dict):
        """
        初始化集成工具

        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = Logger(config.get("log_file"))

        # 初始化回调处理器
        self.callback_handler = PPTGenerationCallbackHandler(self.logger)

        # 初始化内容Agent
        self.content_agent = LangChainContentAgent(
            api_key=config.get("api_key"),
            model=config.get("model", "deepseek-chat"),
            temperature=config.get("temperature", 0.7)
        )

        # 初始化记忆
        self.memory = ChatMessageHistory()

    @tool
    def generate_outline_tool(self, topic: str, num_slides: int, style: str) -> Dict:
        """
        生成PPT大纲的工具

        Args:
            topic: PPT主题
            num_slides: 页数
            style: 风格

        Returns:
            大纲字典
        """
        return self.content_agent.generate_outline(topic, num_slides, style)

    @tool
    def modify_content_tool(self, content: Dict, modification: str) -> Dict:
        """
        修改内容的工具

        Args:
            content: 原始内容
            modification: 修改要求

        Returns:
            修改后的内容
        """
        return self.content_agent.modify_content(content, modification)

    async def stream_generation(
        self,
        topic: str,
        num_slides: int = 10,
        style: str = "professional",
        template: str = "business",
        add_images: bool = False,
        quality_mode: str = "balanced"
    ) -> AsyncGenerator[Dict, None]:
        """
        流式生成PPT

        Args:
            topic: PPT主题
            num_slides: 页数
            style: 风格
            template: 模板
            add_images: 是否添加图片
            quality_mode: 质量模式

        Yields:
            生成状态更新
        """
        yield {"type": "start", "message": "开始生成PPT"}

        # 选择工作流
        if quality_mode == "high":
            workflow = AdvancedPPTWorkflow(self.config)
            inputs = {
                "topic": topic,
                "num_slides": num_slides,
                "style": style,
                "template": template,
                "add_images": add_images,
                "quality_mode": quality_mode,
                "auto_approve_outline": False,
                "enable_review": True,
                "user_requirements": [],
                "current_step": "",
                "progress": 0.0,
                "errors": [],
                "warnings": [],
                "timestamp": format_timestamp(),
                "log_file": self.config.get("log_file"),
                "thread_id": None
            }
        else:
            workflow = PPTWorkflow(self.config)
            inputs = {
                "topic": topic,
                "num_slides": num_slides,
                "style": style,
                "template": template,
                "add_images": add_images,
                "outline": None,
                "contents": None,
                "images": None,
                "ppt_path": None,
                "current_step": "",
                "progress": 0.0,
                "errors": [],
                "timestamp": format_timestamp(),
                "log_file": self.config.get("log_file")
            }

        # 运行工作流并流式更新
        thread_id = f"stream_{format_timestamp()}"

        try:
            # 初始化
            state = await workflow.app.ainvoke(
                inputs,
                config={"configurable": {"thread_id": thread_id}}
            )
            yield {"type": "step", "step": "初始化", "progress": 0.05}

            # 逐步执行
            while state["progress"] < 1.0 and not state["errors"]:
                # 获取当前状态
                current_state = await workflow.app.aget_state(
                    {"configurable": {"thread_id": thread_id}}
                )

                if current_state and current_state.values:
                    state = current_state.values
                    yield {
                        "type": "progress",
                        "step": state.get("current_step", ""),
                        "progress": state.get("progress", 0)
                    }

                    # 特定步骤的额外信息
                    if state.get("outline") and not state.get("contents"):
                        yield {
                            "type": "outline_ready",
                            "outline": state["outline"]
                        }

                    if state.get("contents") and not state.get("ppt_path"):
                        yield {
                            "type": "contents_ready",
                            "contents": state["contents"]
                        }

                await asyncio.sleep(0.5)

            # 最终状态
            if state.get("ppt_path"):
                yield {
                    "type": "complete",
                    "ppt_path": state["ppt_path"],
                    "report": state.get("generation_report")
                }
            elif state.get("errors"):
                yield {
                    "type": "error",
                    "errors": state["errors"]
                }

        except Exception as e:
            yield {
                "type": "error",
                "errors": [str(e)]
            }

    def create_chain_of_thought(self, topic: str, requirements: List[str]) -> str:
        """
        创建思维链来优化生成逻辑

        Args:
            topic: PPT主题
            requirements: 特殊要求列表

        Returns:
            优化后的生成策略
        """
        from langchain.chains import LLMChain
        from langchain_core.prompts import PromptTemplate

        prompt = PromptTemplate.from_template("""
        作为PPT设计专家，请分析以下需求并制定生成策略：

        主题：{topic}
        特殊要求：{requirements}

        请分析：
        1. 这个主题适合什么样的结构？
        2. 应该突出哪些关键点？
        3. 选择什么样的风格最合适？
        4. 需要什么样的视觉元素？
        5. 如何组织内容逻辑？

        输出格式：
        策略分析：
        - 结构设计：
        - 内容重点：
        - 风格选择：
        - 视觉建议：
        - 逻辑组织：
        """)

        chain = LLMChain(
            llm=self.content_agent.llm,
            prompt=prompt
        )

        result = chain.invoke({
            "topic": topic,
            "requirements": ", ".join(requirements) if requirements else "无特殊要求"
        })

        # 保存到记忆
        self.memory.add_user_message(f"分析主题: {topic}, 要求: {requirements}")
        self.memory.add_ai_message(result["text"])

        return result["text"]

    def analyze_feedback(self, feedback: str, original_content: Dict) -> Dict:
        """
        分析用户反馈并生成改进建议

        Args:
            feedback: 用户反馈
            original_content: 原始内容

        Returns:
            改进建议
        """
        from langchain.chains import LLMChain
        from langchain_core.prompts import PromptTemplate

        prompt = PromptTemplate.from_template("""
        分析用户反馈并提供具体的改进建议：

        原始内容：{original_content}
        用户反馈：{feedback}

        请分析：
        1. 用户不满意的具体方面
        2. 需要改进的内容类型
        3. 具体的改进建议
        4. 修改的优先级

        输出JSON格式：
        {{
            "analysis": "问题分析",
            "improvements": [
                {{
                    "aspect": "改进方面",
                    "suggestion": "具体建议",
                    "priority": "high/medium/low"
                }}
            ]
        }}
        """)

        chain = LLMChain(
            llm=self.content_agent.llm,
            prompt=prompt
        )

        try:
            result = chain.invoke({
                "original_content": json.dumps(original_content, ensure_ascii=False),
                "feedback": feedback
            })

            # 解析JSON
            import re
            json_match = re.search(r'\{.*\}', result["text"], re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"analysis": result["text"], "improvements": []}

        except Exception as e:
            self.logger.error(f"反馈分析失败: {str(e)}")
            return {"analysis": "分析失败", "improvements": []}

    def optimize_generation_params(
        self,
        topic: str,
        style: str,
        previous_attempts: List[Dict] = None
    ) -> Dict:
        """
        基于历史尝试优化生成参数

        Args:
            topic: PPT主题
            style: 风格
            previous_attempts: 之前的尝试记录

        Returns:
            优化后的参数
        """
        base_params = {
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 0.9,
            "frequency_penalty": 0
        }

        # 根据主题类型调整
        if "学术" in topic or "研究" in topic:
            base_params["temperature"] = 0.5
            base_params["max_tokens"] = 1536
        elif "创意" in topic or "设计" in topic:
            base_params["temperature"] = 0.8
            base_params["max_tokens"] = 2560

        # 根据风格调整
        style_adjustments = {
            "professional": {"temperature": -0.1, "frequency_penalty": 0.1},
            "creative": {"temperature": 0.1, "frequency_penalty": -0.1},
            "academic": {"temperature": -0.2, "max_tokens": -256}
        }

        if style in style_adjustments:
            for param, adjustment in style_adjustments[style].items():
                base_params[param] = max(0, base_params.get(param, 0) + adjustment)

        # 基于历史尝试调整
        if previous_attempts:
            # 简单的失败分析
            failed_temps = [a.get("temperature", 0.7) for a in previous_attempts if not a.get("success")]
            if failed_temps:
                # 避免使用失败的温度
                avg_failed_temp = sum(failed_temps) / len(failed_temps)
                if abs(base_params["temperature"] - avg_failed_temp) < 0.1:
                    base_params["temperature"] += 0.2

        return base_params

    def export_session_history(self, filepath: str):
        """导出会话历史"""
        history = {
            "messages": [msg.dict() for msg in self.memory.messages],
            "timestamp": format_timestamp(),
            "config": self.config
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        self.logger.info(f"会话历史已导出到: {filepath}")

    def import_session_history(self, filepath: str):
        """导入会话历史"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                history = json.load(f)

            # 恢复消息
            from langchain_core.messages import HumanMessage, AIMessage
            for msg_data in history.get("messages", []):
                if msg_data.get("type") == "human":
                    self.memory.add_user_message(msg_data.get("content", ""))
                elif msg_data.get("type") == "ai":
                    self.memory.add_ai_message(msg_data.get("content", ""))

            self.logger.info(f"会话历史已从 {filepath} 导入")

        except Exception as e:
            self.logger.error(f"导入会话历史失败: {str(e)}")