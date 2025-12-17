"""
使用 LangGraph 重构的 SlideCraft AI 主程序
"""
import os
import time
import asyncio
from typing import Dict, Optional
from dotenv import load_dotenv

from graph.ppt_workflow import PPTWorkflow, PPTGenerationState
from utils.helpers import (
    ensure_dir,
    format_timestamp,
    estimate_generation_time,
    format_time,
    summarize_outline
)

load_dotenv()


class SlideCrafterV2:
    """SlideCraft AI V2 - 基于 LangGraph 的新版本"""

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        log_file: str = None
    ):
        """
        初始化SlideCrafter V2

        Args:
            api_key: API密钥
            model: 模型名称
            log_file: 日志文件路径
        """
        # API配置
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "deepseek-chat")

        if not self.api_key:
            raise ValueError("请设置DEEPSEEK_API_KEY或OPENAI_API_KEY环境变量")

        # 确保输出目录存在
        ensure_dir("output")
        ensure_dir("output/logs")
        ensure_dir("output/image_cache")

        # 初始化工作流配置
        self.config = {
            "api_key": self.api_key,
            "model": self.model,
            "log_file": log_file or f"output/logs/slidecraft_v2_{format_timestamp()}.log"
        }

    async def generate_ppt_async(
        self,
        topic: str,
        num_slides: int = 10,
        style: str = "professional",
        template: str = "business",
        add_images: bool = False,
        thread_id: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        异步生成PPT

        Args:
            topic: PPT主题
            num_slides: 页数
            style: 内容风格
            template: 模板样式
            add_images: 是否添加配图
            thread_id: 线程ID（用于恢复中断的执行）
            progress_callback: 进度回调函数

        Returns:
            生成结果字典，包含状态和文件路径
        """
        print("=" * 80)
        print("🚀 SlideCraft AI V2 启动 (基于 LangGraph)")
        print("=" * 80)
        print(f"📋 主题: {topic}")
        print(f"📊 页数: {num_slides}")
        print(f"🎨 风格: {style}")
        print(f"📄 模板: {template}")
        print(f"🖼️  配图: {'是' if add_images else '否'}")

        # 计算预计时间
        estimated_time = estimate_generation_time(num_slides)
        if add_images:
            estimated_time += num_slides * 3
        print(f"⏱️  预计时间: {format_time(estimated_time)}")
        print("=" * 80)

        # 创建工作流
        workflow = PPTWorkflow({
            **self.config,
            "add_images": add_images
        })

        # 准备输入
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
            "progress": 0.0
        }

        # 启动进度监控任务
        if progress_callback:
            progress_task = asyncio.create_task(
                self._monitor_progress(workflow, thread_id, progress_callback)
            )

        start_time = time.time()

        try:
            # 运行工作流
            final_state = await workflow.run(inputs, thread_id)

            # 完成
            elapsed_time = time.time() - start_time

            if final_state.get("errors"):
                print("\n❌ 生成过程中出现错误:")
                for error in final_state["errors"]:
                    print(f"  - {error}")
                return {
                    "success": False,
                    "errors": final_state["errors"],
                    "state": final_state
                }

            print("\n" + "=" * 80)
            print("🎉 PPT生成完成!")
            print("=" * 80)
            print(f"📁 文件位置: {final_state['ppt_path']}")
            print(f"⏱️  用时: {format_time(int(elapsed_time))}")
            print(f"📊 总页数: {len(final_state['contents'])}")
            if add_images:
                img_count = sum(1 for img in final_state['images'] if img)
                print(f"🖼️  配图数: {img_count}")
            print("=" * 80)

            return {
                "success": True,
                "ppt_path": final_state["ppt_path"],
                "elapsed_time": elapsed_time,
                "state": final_state
            }

        except Exception as e:
            print(f"\n❌ 生成失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "state": None
            }

    def generate_ppt(
        self,
        topic: str,
        num_slides: int = 10,
        style: str = "professional",
        template: str = "business",
        add_images: bool = False,
        thread_id: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        同步生成PPT（向后兼容）

        Args:
            topic: PPT主题
            num_slides: 页数
            style: 内容风格
            template: 模板样式
            add_images: 是否添加配图
            thread_id: 线程ID
            progress_callback: 进度回调函数

        Returns:
            生成结果字典
        """
        return asyncio.run(
            self.generate_ppt_async(
                topic=topic,
                num_slides=num_slides,
                style=style,
                template=template,
                add_images=add_images,
                thread_id=thread_id,
                progress_callback=progress_callback
            )
        )

    async def _monitor_progress(
        self,
        workflow: PPTWorkflow,
        thread_id: Optional[str],
        callback: callable
    ):
        """监控进度并调用回调函数"""
        if not thread_id:
            return

        last_progress = 0
        last_step = ""

        while True:
            try:
                # 获取当前状态
                state = await workflow.app.aget_state(
                    {"configurable": {"thread_id": thread_id}}
                )

                if state and state.values:
                    current_progress = state.values.get("progress", 0)
                    current_step = state.values.get("current_step", "")

                    # 如果进度或步骤发生变化，调用回调
                    if (abs(current_progress - last_progress) > 0.01 or
                        current_step != last_step):
                        callback(current_progress, current_step)
                        last_progress = current_progress
                        last_step = current_step

                    # 如果进度完成，退出监控
                    if current_progress >= 1.0:
                        break

                await asyncio.sleep(0.5)  # 每0.5秒检查一次

            except Exception:
                break

    def get_workflow_visualization(self) -> str:
        """获取工作流可视化图"""
        workflow = PPTWorkflow(self.config)
        return workflow.get_workflow_graph()

    def resume_generation(self, thread_id: str) -> Dict:
        """恢复中断的生成任务"""
        print(f"🔄 恢复生成任务: {thread_id}")
        return self.generate_ppt("", thread_id=thread_id)

    # 向后兼容的方法
    def modify_slide(self, content: Dict, modification: str) -> Dict:
        """修改幻灯片内容（保留原有接口）"""
        from agents.content_agent import ContentAgent
        agent = ContentAgent(self.api_key, self.model)
        return agent.modify_content(content, modification)

    def regenerate_slide(
        self,
        slide_info: Dict,
        topic: str,
        total_pages: int,
        style: str = "professional"
    ) -> Dict:
        """重新生成幻灯片（保留原有接口）"""
        from agents.content_agent import ContentAgent
        agent = ContentAgent(self.api_key, self.model)
        return agent.generate_slide_content(slide_info, topic, total_pages, style)


async def main():
    """异步主程序入口"""
    import argparse

    parser = argparse.ArgumentParser(description="SlideCraft AI V2 - 基于LangGraph的PPT生成系统")
    parser.add_argument("topic", help="PPT主题")
    parser.add_argument("-n", "--num-slides", type=int, default=10, help="页数(默认10)")
    parser.add_argument("-s", "--style", default="professional",
                        choices=["professional", "creative", "academic", "startup", "teaching"],
                        help="内容风格")
    parser.add_argument("-t", "--template", default="business",
                        choices=["business", "creative", "academic"],
                        help="模板样式")
    parser.add_argument("--add-images", action="store_true", help="自动添加配图")
    parser.add_argument("--thread-id", help="线程ID（用于恢复任务）")

    args = parser.parse_args()

    # 创建实例
    crafter = SlideCrafterV2()

    # 定义进度回调
    def progress_callback(progress: float, step: str):
        """进度显示回调"""
        bar_length = 40
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\r[{bar}] {progress*100:.1f}% - {step}", end="", flush=True)

    # 生成PPT
    result = await crafter.generate_ppt_async(
        topic=args.topic,
        num_slides=args.num_slides,
        style=args.style,
        template=args.template,
        add_images=args.add_images,
        thread_id=args.thread_id,
        progress_callback=progress_callback
    )

    if not result["success"]:
        exit(1)


if __name__ == "__main__":
    # Windows 使用不同的策略
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())