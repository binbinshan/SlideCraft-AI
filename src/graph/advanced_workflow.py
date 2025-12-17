"""
高级 PPT 生成工作流
支持复杂的条件分支、状态管理和并行处理
"""
from typing import Dict, List, Optional, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableLambda
import json
import asyncio
from datetime import datetime

from agents.langchain_content_agent import LangChainContentAgent
from agents.image_agent import ImageAgent
from generators.ppt_generator import PPTGenerator
from utils.helpers import save_json, format_timestamp, Logger


class AdvancedPPTState(TypedDict):
    """高级PPT生成状态"""
    # 输入参数
    topic: str
    num_slides: int
    style: str
    template: str
    add_images: bool
    quality_mode: str  # "fast", "balanced", "high"

    # 生成配置
    auto_approve_outline: bool
    enable_review: bool
    user_requirements: List[str]

    # 中间结果
    outline: Optional[Dict]
    outline_approved: bool
    outline_feedback: Optional[str]
    contents: Optional[List[Dict]]
    images: Optional[List[Optional[str]]]
    quality_score: Optional[float]

    # 处理状态
    current_step: str
    progress: float
    errors: List[str]
    warnings: List[str]

    # 元数据
    timestamp: str
    log_file: str
    thread_id: str
    start_time: datetime
    end_time: Optional[datetime]

    # 输出
    ppt_path: Optional[str]
    generation_report: Optional[Dict]


class AdvancedPPTWorkflow:
    """高级PPT生成工作流"""

    def __init__(self, config: Dict):
        """
        初始化高级工作流

        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = Logger(config.get("log_file"))

        # 初始化智能代理
        self.content_agent = LangChainContentAgent(
            api_key=config.get("api_key"),
            model=config.get("model", "deepseek-chat"),
            temperature=0.7
        )

        self.ppt_generator = PPTGenerator(template=config.get("template", "business"))

        if config.get("add_images", False):
            self.image_agent = ImageAgent()
        else:
            self.image_agent = None

        # 创建高级工作流图
        self.workflow = self._create_advanced_workflow()

        # 添加持久化支持
        self.memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.memory)

    def _create_advanced_workflow(self) -> StateGraph:
        """创建高级工作流图"""
        workflow = StateGraph(AdvancedPPTState)

        # 添加节点
        workflow.add_node("initialize", self._initialize)
        workflow.add_node("analyze_requirements", self._analyze_requirements)
        workflow.add_node("generate_outline", self._generate_outline)
        workflow.add_node("review_outline", self._review_outline)
        workflow.add_node("refine_outline", self._refine_outline)
        workflow.add_node("generate_contents", self._generate_contents)
        workflow.add_node("enhance_contents", self._enhance_contents)
        workflow.add_node("search_images", self._search_images)
        workflow.add_node("optimize_images", self._optimize_images)
        workflow.add_node("create_ppt", self._create_ppt)
        workflow.add_node("quality_check", self._quality_check)
        workflow.add_node("generate_report", self._generate_report)
        workflow.add_node("handle_error", self._handle_error)
        workflow.add_node("retry_step", self._retry_step)

        # 设置入口点
        workflow.set_entry_point("initialize")

        # 添加流程边
        workflow.add_edge("initialize", "analyze_requirements")
        workflow.add_edge("analyze_requirements", "generate_outline")
        workflow.add_edge("generate_outline", "review_outline")

        # 大纲审查分支
        workflow.add_conditional_edges(
            "review_outline",
            self._outline_review_decision,
            {
                "approve": "generate_contents",
                "refine": "refine_outline",
                "error": "handle_error"
            }
        )

        workflow.add_edge("refine_outline", "review_outline")

        # 内容生成后处理
        workflow.add_edge("generate_contents", "enhance_contents")

        workflow.add_conditional_edges(
            "enhance_contents",
            self._should_search_images,
            {
                "search": "search_images",
                "skip": "create_ppt"
            }
        )

        workflow.add_edge("search_images", "optimize_images")
        workflow.add_edge("optimize_images", "create_ppt")
        workflow.add_edge("create_ppt", "quality_check")

        # 质量检查分支
        workflow.add_conditional_edges(
            "quality_check",
            self._quality_check_decision,
            {
                "pass": "generate_report",
                "retry": "retry_step",
                "fail": "handle_error"
            }
        )

        workflow.add_edge("retry_step", "generate_contents")
        workflow.add_edge("generate_report", END)
        workflow.add_edge("handle_error", END)

        # 错误处理
        workflow.add_conditional_edges(
            "generate_outline",
            self._check_for_errors,
            {
                "error": "handle_error",
                "continue": "review_outline"
            }
        )

        return workflow

    async def _initialize(self, state: AdvancedPPTState) -> AdvancedPPTState:
        """初始化工作流"""
        self.logger.info(f"初始化高级工作流: {state['topic']}")

        state["current_step"] = "初始化"
        state["progress"] = 0.02
        state["timestamp"] = format_timestamp()
        state["errors"] = []
        state["warnings"] = []
        state["outline_approved"] = False
        state["outline_feedback"] = None
        state["quality_score"] = None
        state["start_time"] = datetime.now()

        return state

    async def _analyze_requirements(self, state: AdvancedPPTState) -> AdvancedPPTState:
        """分析生成需求"""
        self.logger.info("分析生成需求")
        state["current_step"] = "分析需求"
        state["progress"] = 0.05

        # 根据质量模式调整参数
        if state["quality_mode"] == "fast":
            state["auto_approve_outline"] = True
            state["enable_review"] = False
        elif state["quality_mode"] == "high":
            state["auto_approve_outline"] = False
            state["enable_review"] = True

        # 智能调整页数
        if state["num_slides"] < 3:
            state["num_slides"] = 3
            state["warnings"].append("页数自动调整为3页")
        elif state["num_slides"] > 30:
            state["num_slides"] = 30
            state["warnings"].append("页数自动调整为30页以保证质量")

        return state

    async def _generate_outline(self, state: AdvancedPPTState) -> AdvancedPPTState:
        """生成大纲"""
        try:
            self.logger.info("开始生成大纲")
            state["current_step"] = "生成大纲"
            state["progress"] = 0.1

            # 根据质量模式调整温度
            if state["quality_mode"] == "high":
                self.content_agent.temperature = 0.5  # 更保守
            else:
                self.content_agent.temperature = 0.7  # 更有创意

            outline = await self.content_agent.generate_outline_async(
                topic=state["topic"],
                num_slides=state["num_slides"],
                style=state["style"]
            )

            state["outline"] = outline
            state["progress"] = 0.2

            # 保存大纲
            outline_path = f"output/logs/outline_{state['timestamp']}.json"
            save_json(outline, outline_path)

            return state

        except Exception as e:
            error_msg = f"大纲生成失败: {str(e)}"
            self.logger.error(error_msg)
            state["errors"].append(error_msg)
            return state

    async def _review_outline(self, state: AdvancedPPTState) -> AdvancedPPTState:
        """审查大纲质量"""
        self.logger.info("审查大纲质量")
        state["current_step"] = "审查大纲"
        state["progress"] = 0.25

        if state["auto_approve_outline"]:
            state["outline_approved"] = True
            state["outline_feedback"] = "自动批准"
            return state

        # 简单的质量检查
        outline = state.get("outline")
        if not outline:
            state["errors"].append("大纲为空")
            return state

        # 检查页数
        actual_slides = len(outline.get("slides", []))
        expected_slides = state["num_slides"]

        if abs(actual_slides - expected_slides) > 2:
            state["outline_feedback"] = f"页数不匹配: 生成{actual_slides}页, 期望{expected_slides}页"
            state["outline_approved"] = False
        else:
            state["outline_approved"] = True
            state["outline_feedback"] = "大纲质量良好"

        return state

    async def _refine_outline(self, state: AdvancedPPTState) -> AdvancedPPTState:
        """优化大纲"""
        self.logger.info("优化大纲")
        state["current_step"] = "优化大纲"
        state["progress"] = 0.3

        # 这里可以实现更智能的大纲优化逻辑
        # 目前简单地重新生成
        try:
            outline = await self.content_agent.generate_outline_async(
                topic=state["topic"],
                num_slides=state["num_slides"],
                style=state["style"]
            )
            state["outline"] = outline
            state["outline_approved"] = True
            state["outline_feedback"] = "优化后批准"
        except Exception as e:
            state["errors"].append(f"大纲优化失败: {str(e)}")

        return state

    async def _generate_contents(self, state: AdvancedPPTState) -> AdvancedPPTState:
        """生成内容"""
        try:
            self.logger.info("生成内容")
            state["current_step"] = "生成内容"

            if not state["outline"]:
                raise ValueError("缺少大纲信息")

            # 并行生成内容
            contents = await self.content_agent.generate_batch_contents_async(
                slides_info=state["outline"]["slides"],
                overall_topic=state["topic"],
                total_pages=state["num_slides"],
                style=state["style"]
            )

            state["contents"] = contents
            state["progress"] = 0.6

            # 保存内容
            contents_path = f"output/logs/contents_{state['timestamp']}.json"
            save_json(contents, contents_path)

            return state

        except Exception as e:
            error_msg = f"内容生成失败: {str(e)}"
            self.logger.error(error_msg)
            state["errors"].append(error_msg)
            return state

    async def _enhance_contents(self, state: AdvancedPPTState) -> AdvancedPPTState:
        """增强内容质量"""
        if state["quality_mode"] != "high":
            return state

        self.logger.info("增强内容质量")
        state["current_step"] = "增强内容"
        state["progress"] = 0.65

        # 实现内容增强逻辑
        # 例如：优化语言、添加过渡语句、确保一致性等

        return state

    async def _search_images(self, state: AdvancedPPTState) -> AdvancedPPTState:
        """搜索图片"""
        try:
            self.logger.info("搜索配图")
            state["current_step"] = "搜索配图"

            if not self.image_agent or not state["contents"]:
                state["images"] = []
                return state

            # 并行搜索图片
            images = await self._search_images_parallel(
                state["contents"],
                state["outline"]["slides"],
                state["topic"]
            )

            state["images"] = images
            state["progress"] = 0.75

            return state

        except Exception as e:
            error_msg = f"图片搜索失败: {str(e)}"
            self.logger.warning(error_msg)
            state["warnings"].append(error_msg)
            state["images"] = []
            return state

    async def _search_images_parallel(
        self,
        contents: List[Dict],
        slides: List[Dict],
        topic: str
    ) -> List[Optional[str]]:
        """并行搜索图片"""
        semaphore = asyncio.Semaphore(5)

        async def search_image(content: Dict):
            if content.get("type") != "content":
                return None

            async with semaphore:
                try:
                    return await asyncio.get_event_loop().run_in_executor(
                        None,
                        self.image_agent.get_image_for_slide,
                        content.get("title", ""),
                        content.get("content", []),
                        topic
                    )
                except Exception:
                    return None

        tasks = [search_image(c) for c in contents]
        return await asyncio.gather(*tasks)

    async def _optimize_images(self, state: AdvancedPPTState) -> AdvancedPPTState:
        """优化图片"""
        if state["quality_mode"] != "high":
            return state

        self.logger.info("优化图片")
        state["current_step"] = "优化图片"
        state["progress"] = 0.8

        # 实现图片优化逻辑
        # 例如：调整尺寸、压缩、选择最佳图片等

        return state

    async def _create_ppt(self, state: AdvancedPPTState) -> AdvancedPPTState:
        """创建PPT"""
        try:
            self.logger.info("创建PPT")
            state["current_step"] = "创建PPT"
            state["progress"] = 0.85

            # 模板已在初始化时设置

            ppt_path = self.ppt_generator.create_presentation(
                outline=state["outline"],
                contents=state["contents"],
                images=state.get("images") if state["add_images"] else None
            )

            state["ppt_path"] = ppt_path
            state["progress"] = 0.9

            return state

        except Exception as e:
            error_msg = f"PPT创建失败: {str(e)}"
            self.logger.error(error_msg)
            state["errors"].append(error_msg)
            return state

    async def _quality_check(self, state: AdvancedPPTState) -> AdvancedPPTState:
        """质量检查"""
        self.logger.info("执行质量检查")
        state["current_step"] = "质量检查"
        state["progress"] = 0.95

        # 简单的质量评分
        score = 100

        # 检查错误
        if state["errors"]:
            score -= len(state["errors"]) * 20

        # 检查警告
        if state["warnings"]:
            score -= len(state["warnings"]) * 5

        # 检查完整性
        if not state.get("ppt_path"):
            score -= 50

        state["quality_score"] = max(0, score)
        state["end_time"] = datetime.now()

        return state

    async def _generate_report(self, state: AdvancedPPTState) -> AdvancedPPTState:
        """生成报告"""
        self.logger.info("生成报告")
        state["current_step"] = "生成报告"
        state["progress"] = 1.0

        # 计算耗时
        duration = None
        if state["end_time"] and state["start_time"]:
            duration = (state["end_time"] - state["start_time"]).total_seconds()

        # 生成报告
        report = {
            "topic": state["topic"],
            "slides_generated": len(state.get("contents", [])),
            "quality_score": state["quality_score"],
            "duration_seconds": duration,
            "errors": state["errors"],
            "warnings": state["warnings"],
            "template_used": state["template"],
            "style_used": state["style"],
            "images_added": len([i for i in state.get("images", []) if i]),
            "timestamp": state["timestamp"]
        }

        state["generation_report"] = report

        # 保存报告
        report_path = f"output/logs/report_{state['timestamp']}.json"
        save_json(report, report_path)

        return state

    async def _handle_error(self, state: AdvancedPPTState) -> AdvancedPPTState:
        """处理错误"""
        self.logger.error(f"工作流出错: {state['errors']}")
        state["current_step"] = "错误"
        state["end_time"] = datetime.now()
        return state

    async def _retry_step(self, state: AdvancedPPTState) -> AdvancedPPTState:
        """重试步骤"""
        self.logger.info("重试生成")
        state["current_step"] = "重试"
        state["errors"] = []  # 清除错误
        return state

    def _outline_review_decision(self, state: AdvancedPPTState) -> str:
        """大纲审查决策"""
        if state["errors"]:
            return "error"
        elif state["outline_approved"]:
            return "approve"
        elif state["outline_feedback"] and not state["auto_approve_outline"]:
            return "refine"
        else:
            return "approve"

    def _should_search_images(self, state: AdvancedPPTState) -> str:
        """是否搜索图片"""
        return "search" if state["add_images"] and not state["errors"] else "skip"

    def _quality_check_decision(self, state: AdvancedPPTState) -> str:
        """质量检查决策"""
        if state["errors"] or (state["quality_score"] and state["quality_score"] < 60):
            return "fail"
        elif state["quality_score"] and state["quality_score"] < 80:
            return "retry"
        else:
            return "pass"

    def _check_for_errors(self, state: AdvancedPPTState) -> str:
        """检查错误"""
        return "error" if state["errors"] else "continue"

    async def run(self, inputs: Dict, thread_id: str = None) -> Dict:
        """运行高级工作流"""
        # 当使用checkpointer时，必须提供thread_id
        if not thread_id:
            import uuid
            thread_id = str(uuid.uuid4())

        config = {"configurable": {"thread_id": thread_id}}
        final_state = await self.app.ainvoke(inputs, config=config)

        return final_state

    def run_sync(self, inputs: Dict, thread_id: str = None) -> Dict:
        """同步运行"""
        return asyncio.run(self.run(inputs, thread_id))