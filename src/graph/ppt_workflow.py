"""
基于LangGraph的PPT生成工作流
"""
from typing import Dict, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from agents.content_agent import ContentAgent
from agents.image_agent import ImageAgent
from generators.ppt_generator import PPTGenerator
from utils.helpers import save_json, format_timestamp
from utils.helpers import Logger


class PPTGenerationState(TypedDict):
    """PPT生成状态"""
    # 输入参数
    topic: str
    num_slides: int
    style: str
    template: str
    add_images: bool

    # 中间结果
    outline: Optional[Dict]
    contents: Optional[List[Dict]]
    images: Optional[List[Optional[str]]]

    # 输出
    ppt_path: Optional[str]

    # 元数据
    timestamp: str
    log_file: str
    errors: List[str]

    # 进度跟踪
    current_step: str
    progress: float


class PPTWorkflow:
    """基于LangGraph的PPT生成工作流"""

    def __init__(self, config: Dict):
        """
        初始化工作流

        Args:
            config: 配置字典，包含API密钥等
        """
        self.config = config
        self.logger = Logger(config.get("log_file"))

        # 初始化各个组件
        self.content_agent = ContentAgent(
            api_key=config.get("api_key"),
            model=config.get("model", "deepseek-chat")
        )

        # 初始化PPT生成器，使用默认模板
        self.ppt_generator = PPTGenerator(template=config.get("template", "business"))

        if config.get("add_images", False):
            self.image_agent = ImageAgent()
        else:
            self.image_agent = None

        # 创建工作流图
        self.workflow = self._create_workflow()

        # 添加检查点支持
        self.memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.memory)

    def _create_workflow(self) -> StateGraph:
        """创建工作流图"""
        workflow = StateGraph(PPTGenerationState)

        # 添加节点
        workflow.add_node("initialize", self._initialize)
        workflow.add_node("generate_outline", self._generate_outline)
        workflow.add_node("generate_contents", self._generate_contents)
        workflow.add_node("search_images", self._search_images)
        workflow.add_node("create_ppt", self._create_ppt)
        workflow.add_node("handle_error", self._handle_error)

        # 设置入口点
        workflow.set_entry_point("initialize")

        # 添加边
        workflow.add_edge("initialize", "generate_outline")
        workflow.add_edge("generate_outline", "generate_contents")

        # 条件边：是否需要搜索图片
        workflow.add_conditional_edges(
            "generate_contents",
            self._should_search_images,
            {
                "search": "search_images",
                "skip": "create_ppt"
            }
        )

        workflow.add_edge("search_images", "create_ppt")
        workflow.add_edge("create_ppt", END)

        # 错误处理边
        workflow.add_conditional_edges(
            "generate_outline",
            self._check_for_errors,
            {
                "error": "handle_error",
                "continue": "generate_contents"
            }
        )

        workflow.add_conditional_edges(
            "generate_contents",
            self._check_for_errors,
            {
                "error": "handle_error",
                "continue": "search_images"  # 会进入下一个条件判断
            }
        )

        workflow.add_edge("handle_error", END)

        return workflow

    async def _initialize(self, state: PPTGenerationState) -> PPTGenerationState:
        """初始化步骤"""
        self.logger.info(f"开始初始化工作流: {state['topic']}")

        state["current_step"] = "初始化"
        state["progress"] = 0.05
        state["timestamp"] = format_timestamp()
        state["errors"] = []

        return state

    async def _generate_outline(self, state: PPTGenerationState) -> PPTGenerationState:
        """生成大纲"""
        try:
            self.logger.info("开始生成大纲")
            state["current_step"] = "生成大纲"
            state["progress"] = 0.1

            outline = self.content_agent.generate_outline(
                topic=state["topic"],
                num_slides=state["num_slides"],
                style=state["style"]
            )

            state["outline"] = outline
            state["progress"] = 0.3

            # 保存大纲
            outline_path = f"output/logs/outline_{state['timestamp']}.json"
            save_json(outline, outline_path)
            self.logger.info(f"大纲已保存: {outline_path}")

            return state

        except Exception as e:
            error_msg = f"大纲生成失败: {str(e)}"
            self.logger.error(error_msg)
            state["errors"].append(error_msg)
            return state

    async def _generate_contents(self, state: PPTGenerationState) -> PPTGenerationState:
        """并行生成所有页面内容"""
        try:
            self.logger.info("开始生成内容")
            state["current_step"] = "生成内容"

            if not state["outline"]:
                raise ValueError("缺少大纲信息")

            # 使用异步并行处理内容生成
            contents = await self._generate_contents_parallel(
                state["outline"]["slides"],
                state["topic"],
                state["style"]
            )

            state["contents"] = contents
            state["progress"] = 0.6

            # 保存内容
            contents_path = f"output/logs/contents_{state['timestamp']}.json"
            save_json(contents, contents_path)
            self.logger.info(f"内容已保存: {contents_path}")

            return state

        except Exception as e:
            error_msg = f"内容生成失败: {str(e)}"
            self.logger.error(error_msg)
            state["errors"].append(error_msg)
            return state

    async def _generate_contents_parallel(
        self,
        slides: List[Dict],
        topic: str,
        style: str
    ) -> List[Dict]:
        """并行生成内容"""
        total_slides = len(slides)
        contents = [None] * total_slides

        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(3)  # 最多3个并发请求

        async def generate_single_content(index: int, slide_info: Dict):
            async with semaphore:
                content = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.content_agent.generate_slide_content,
                    slide_info,
                    topic,
                    total_slides,
                    style
                )
                contents[index] = content
                return content

        # 创建所有任务
        tasks = [
            generate_single_content(i, slide)
            for i, slide in enumerate(slides)
        ]

        # 等待所有任务完成
        await asyncio.gather(*tasks)

        return contents

    async def _search_images(self, state: PPTGenerationState) -> PPTGenerationState:
        """并行搜索配图"""
        try:
            self.logger.info("开始搜索配图")
            state["current_step"] = "搜索配图"

            if not self.image_agent or not state["contents"]:
                state["images"] = []
                return state

            # 使用异步并行搜索图片
            images = await self._search_images_parallel(
                state["contents"],
                state["outline"]["slides"],
                state["topic"]
            )

            state["images"] = images
            state["progress"] = 0.8

            img_count = sum(1 for img in images if img)
            self.logger.info(f"配图搜索完成: {img_count}/{len(images)}")

            return state

        except Exception as e:
            error_msg = f"配图搜索失败: {str(e)}"
            self.logger.error(error_msg)
            state["errors"].append(error_msg)
            # 配图失败不应该阻止整个流程
            state["images"] = []
            return state

    async def _search_images_parallel(
        self,
        contents: List[Dict],
        slides: List[Dict],
        topic: str
    ) -> List[Optional[str]]:
        """并行搜索图片"""
        images = []

        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(5)  # 最多5个并发图片搜索

        async def search_single_image(index: int, content: Dict):
            slide_type = content.get("type", "content")

            # 只为内容页添加图片
            if slide_type != "content":
                return None

            async with semaphore:
                try:
                    image_path = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self.image_agent.get_image_for_slide,
                        content.get("title", ""),
                        content.get("content", []),
                        topic
                    )
                    return image_path
                except Exception as e:
                    self.logger.warning(f"第{index+1}页配图失败: {str(e)}")
                    return None

        # 创建所有任务
        tasks = [
            search_single_image(i, content)
            for i, content in enumerate(contents)
        ]

        # 等待所有任务完成
        images = await asyncio.gather(*tasks)

        return images

    async def _create_ppt(self, state: PPTGenerationState) -> PPTGenerationState:
        """创建PPT文件"""
        try:
            self.logger.info("开始创建PPT")
            state["current_step"] = "创建PPT"
            state["progress"] = 0.9

            # 模板已在初始化时设置

            # 创建PPT
            ppt_path = self.ppt_generator.create_presentation(
                outline=state["outline"],
                contents=state["contents"],
                images=state.get("images") if state["add_images"] else None
            )

            state["ppt_path"] = ppt_path
            state["progress"] = 1.0

            self.logger.info(f"PPT创建完成: {ppt_path}")

            return state

        except Exception as e:
            error_msg = f"PPT创建失败: {str(e)}"
            self.logger.error(error_msg)
            state["errors"].append(error_msg)
            return state

    async def _handle_error(self, state: PPTGenerationState) -> PPTGenerationState:
        """处理错误"""
        self.logger.error(f"工作流出错: {state['errors']}")
        state["current_step"] = "错误"
        return state

    def _should_search_images(self, state: PPTGenerationState) -> str:
        """判断是否需要搜索图片"""
        return "search" if state["add_images"] and not state["errors"] else "skip"

    def _check_for_errors(self, state: PPTGenerationState) -> str:
        """检查是否有错误"""
        return "error" if state["errors"] else "continue"

    async def run(self, inputs: Dict, thread_id: str = None) -> Dict:
        """
        运行工作流

        Args:
            inputs: 输入参数
            thread_id: 线程ID，用于恢复中断的执行

        Returns:
            最终状态
        """
        # 当使用checkpointer时，必须提供thread_id
        if not thread_id:
            import uuid
            thread_id = str(uuid.uuid4())

        config = {"configurable": {"thread_id": thread_id}}
        final_state = await self.app.ainvoke(inputs, config=config)

        return final_state

    def run_sync(self, inputs: Dict, thread_id: str = None) -> Dict:
        """同步运行工作流"""
        return asyncio.run(self.run(inputs, thread_id))

    def get_workflow_graph(self) -> str:
        """获取工作流的可视化表示"""
        try:
            import mermaid
            graph = self.workflow.get_graph()
            return graph.draw_mermaid()
        except ImportError:
            return "需要安装 mermaid-py 来可视化工作流"