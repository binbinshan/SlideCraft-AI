"""
基于 LangGraph 的 Gradio Web 应用
"""
import gradio as gr
import asyncio
import os
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import time

from main_langgraph import SlideCrafterV2
from utils.langchain_integration import LangChainIntegration
from utils.helpers import format_time, format_timestamp
from dotenv import load_dotenv

load_dotenv()


class LangGraphApp:
    """基于 LangGraph 的 Web 应用"""

    def __init__(self):
        """初始化应用"""
        # 初始化核心组件
        self.api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "deepseek-chat")

        if not self.api_key:
            raise ValueError("请设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY 环境变量")

        # 创建实例
        self.crafter = SlideCrafterV2(api_key=self.api_key, model=self.model)
        self.integration = LangChainIntegration({
            "api_key": self.api_key,
            "model": self.model,
            "log_file": f"output/logs/app_{format_timestamp()}.log"
        })

        # 状态管理
        self.current_generation = None
        self.generation_history = []

    def generate_ppt_with_progress(
        self,
        topic: str,
        num_slides: int,
        style: str,
        template: str,
        add_images: bool,
        quality_mode: str,
        progress=gr.Progress()
    ) -> Tuple[str, str, str]:
        """生成PPT并显示进度"""
        if not topic.strip():
            return "❌ 请输入PPT主题", "", ""

        # 初始化进度
        progress(0, desc="初始化...")

        # 生成任务ID
        task_id = f"task_{format_timestamp()}"

        try:
            # 定义进度回调
            def progress_callback(p: float, step: str):
                progress(p, desc=step)

            # 异步生成
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                self.crafter.generate_ppt_async(
                    topic=topic,
                    num_slides=num_slides,
                    style=style,
                    template=template,
                    add_images=add_images,
                    progress_callback=progress_callback
                )
            )

            loop.close()

            if result["success"]:
                # 保存到历史
                self.generation_history.append({
                    "topic": topic,
                    "timestamp": format_timestamp(),
                    "ppt_path": result["ppt_path"],
                    "elapsed_time": result["elapsed_time"],
                    "style": style,
                    "template": template
                })

                return (
                    f"✅ PPT生成成功！\n\n"
                    f"📁 文件位置: {result['ppt_path']}\n"
                    f"⏱️ 用时: {format_time(int(result['elapsed_time']))}",
                    result["ppt_path"],
                    json.dumps(result["state"], ensure_ascii=False, indent=2)
                )
            else:
                return (
                    f"❌ 生成失败\n\n错误信息: {result.get('error', '未知错误')}",
                    "",
                    ""
                )

        except Exception as e:
            return f"❌ 发生错误: {str(e)}", "", ""

    async def stream_generate_ppt(
        self,
        topic: str,
        num_slides: int,
        style: str,
        template: str,
        add_images: bool,
        quality_mode: str
    ):
        """流式生成PPT"""
        if not topic.strip():
            yield "❌ 请输入PPT主题", "", ""
            return

        yield "🚀 开始生成PPT...", "", ""

        try:
            async for update in self.integration.stream_generation(
                topic=topic,
                num_slides=num_slides,
                style=style,
                template=template,
                add_images=add_images,
                quality_mode=quality_mode
            ):
                if update["type"] == "progress":
                    yield (
                        f"📝 {update['step']}... ({update['progress']*100:.1f}%)",
                        "",
                        ""
                    )
                elif update["type"] == "outline_ready":
                    yield (
                        "✅ 大纲生成完成！",
                        "",
                        json.dumps(update["outline"], ensure_ascii=False, indent=2)
                    )
                elif update["type"] == "contents_ready":
                    yield (
                        "✅ 内容生成完成！",
                        "",
                        "内容已准备就绪..."
                    )
                elif update["type"] == "complete":
                    ppt_path = update["ppt_path"]
                    report = update.get("report", {})
                    yield (
                        f"🎉 PPT生成完成！\n\n"
                        f"📁 文件位置: {ppt_path}\n"
                        f"📊 质量评分: {report.get('quality_score', 'N/A')}/100\n"
                        f"📄 页数: {report.get('slides_generated', 'N/A')}\n"
                        f"🖼️ 图片数: {report.get('images_added', 'N/A')}",
                        ppt_path,
                        json.dumps(report, ensure_ascii=False, indent=2)
                    )
                elif update["type"] == "error":
                    yield (
                        f"❌ 生成失败\n\n错误: {', '.join(update['errors'])}",
                        "",
                        ""
                    )

        except Exception as e:
            yield f"❌ 发生错误: {str(e)}", "", ""

    def modify_content_with_feedback(
        self,
        original_content: str,
        feedback: str
    ) -> str:
        """根据反馈修改内容"""
        try:
            content = json.loads(original_content) if original_content else {}
            if not content:
                return "❌ 请先提供原始内容"

            # 分析反馈
            analysis = self.integration.analyze_feedback(feedback, content)

            # 使用LangChain修改内容
            modified = self.crafter.modify_slide(content, feedback)

            return (
                f"📊 反馈分析:\n{analysis.get('analysis', '无')}\n\n"
                f"✨ 修改后的内容:\n{json.dumps(modified, ensure_ascii=False, indent=2)}"
            )

        except Exception as e:
            return f"❌ 修改失败: {str(e)}"

    def get_generation_history(self) -> str:
        """获取生成历史"""
        if not self.generation_history:
            return "暂无生成历史"

        history_text = "## 生成历史\n\n"
        for i, record in enumerate(reversed(self.generation_history[-10:]), 1):
            history_text += f"### {i}. {record['topic']}\n"
            history_text += f"- 时间: {record['timestamp']}\n"
            history_text += f"- 风格: {record['style']} | 模板: {record['template']}\n"
            history_text += f"- 用时: {format_time(int(record['elapsed_time']))}\n"
            history_text += f"- 文件: {record['ppt_path']}\n\n"

        return history_text

    def analyze_topic(self, topic: str, requirements: str) -> str:
        """分析主题"""
        if not topic.strip():
            return "请输入PPT主题"

        req_list = [r.strip() for r in requirements.split('\n') if r.strip()] if requirements else []

        try:
            analysis = self.integration.create_chain_of_thought(topic, req_list)
            return analysis
        except Exception as e:
            return f"分析失败: {str(e)}"

    def create_interface(self):
        """创建Gradio界面"""
        with gr.Blocks(
            title="SlideCraft AI V2 - 基于LangGraph",
        ) as app:
            gr.Markdown("""
            # 🚀 SlideCraft AI V2

            基于 **LangChain** 和 **LangGraph** 构建的新一代智能PPT生成系统

            ✨ 新特性:
            - 🔄 流式生成与实时进度跟踪
            - 🧠 智能内容分析与优化
            - 💾 会话历史与记忆管理
            - ⚡ 并行处理提升性能
            - 🎯 质量检查与自动重试
            """)

            with gr.Tabs():
                # 标签1: 快速生成
                with gr.Tab("📝 快速生成"):
                    with gr.Row():
                        with gr.Column(scale=2):
                            topic_input = gr.Textbox(
                                label="PPT主题",
                                placeholder="例如：人工智能在教育领域的应用",
                                lines=2
                            )

                            with gr.Row():
                                num_slides = gr.Slider(
                                    3, 30, value=10,
                                    label="页数",
                                    info="建议3-30页"
                                )
                                style = gr.Dropdown(
                                    ["professional", "creative", "academic", "startup", "teaching"],
                                    value="professional",
                                    label="内容风格"
                                )

                            with gr.Row():
                                template = gr.Dropdown(
                                    ["business", "creative", "academic"],
                                    value="business",
                                    label="视觉模板"
                                )
                                quality_mode = gr.Dropdown(
                                    ["fast", "balanced", "high"],
                                    value="balanced",
                                    label="质量模式"
                                )

                            add_images = gr.Checkbox(
                                label="自动添加配图",
                                value=False
                            )

                            generate_btn = gr.Button(
                                "🚀 生成PPT",
                                variant="primary",
                                size="lg"
                            )

                        with gr.Column(scale=1):
                            status_output = gr.Textbox(
                                label="生成状态",
                                lines=10,
                                max_lines=20,
                                interactive=False,
                                elem_classes=["generation-status"]
                            )

                    with gr.Row():
                        ppt_file = gr.File(
                            label="下载PPT",
                            visible=True
                        )
                        debug_info = gr.Code(
                            label="调试信息",
                            language="json",
                            visible=False
                        )

                # 标签2: 智能分析
                with gr.Tab("🧠 智能分析"):
                    with gr.Row():
                        with gr.Column():
                            analyze_topic = gr.Textbox(
                                label="PPT主题",
                                placeholder="输入要分析的主题",
                                lines=2
                            )
                            analyze_requirements = gr.Textbox(
                                label="特殊要求",
                                placeholder="每行一个要求",
                                lines=5
                            )
                            analyze_btn = gr.Button("📊 分析主题", variant="primary")

                        with gr.Column():
                            analysis_output = gr.Markdown(
                                label="分析结果"
                            )

                # 标签3: 内容优化
                with gr.Tab("✨ 内容优化"):
                    with gr.Row():
                        with gr.Column():
                            original_content = gr.Code(
                                label="原始内容",
                                language="json"
                            )
                            feedback = gr.Textbox(
                                label="修改要求",
                                lines=3,
                                placeholder="例如：让内容更简洁、添加具体案例等",
                            )
                            modify_btn = gr.Button("🔄 修改内容", variant="primary")

                        with gr.Column():
                            modified_output = gr.Markdown(
                                label="修改结果"
                            )

                # 标签4: 生成历史
                with gr.Tab("📚 生成历史"):
                    history_output = gr.Markdown(
                        label="历史记录"
                    )
                    refresh_history_btn = gr.Button("🔄 刷新历史")

            # 事件绑定
            generate_btn.click(
                fn=self.generate_ppt_with_progress,
                inputs=[
                    topic_input,
                    num_slides,
                    style,
                    template,
                    add_images,
                    quality_mode
                ],
                outputs=[status_output, ppt_file, debug_info]
            )

            # 流式生成（作为高级选项）
            generate_stream_btn = gr.Button(
                "🚀 流式生成（高级）",
                variant="secondary",
                size="sm"
            )
            generate_stream_btn.click(
                fn=self.stream_generate_ppt,
                inputs=[
                    topic_input,
                    num_slides,
                    style,
                    template,
                    add_images,
                    quality_mode
                ],
                outputs=[status_output, ppt_file, debug_info]
            )

            analyze_btn.click(
                fn=self.analyze_topic,
                inputs=[analyze_topic, analyze_requirements],
                outputs=[analysis_output]
            )

            modify_btn.click(
                fn=self.modify_content_with_feedback,
                inputs=[original_content, feedback],
                outputs=[modified_output]
            )

            refresh_history_btn.click(
                fn=self.get_generation_history,
                outputs=[history_output]
            )

            # 初始化时加载历史
            app.load(
                fn=self.get_generation_history,
                outputs=[history_output]
            )

        return app

    def launch(self, **kwargs):
        """启动应用"""
        app = self.create_interface()
        app.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            theme=gr.themes.Soft(),
            css="""
                  .progress-bar { margin: 10px 0; }
                  .generation-status { font-family: monospace; }
                  """,
            **kwargs
        )


def main():
    """主函数"""
    try:
        app = LangGraphApp()
        print("🚀 启动 SlideCraft AI V2 (基于 LangGraph)")
        print("📱 访问地址: http://localhost:7860")
        print("⚡ 新特性: 流式生成、智能分析、内容优化")
        app.launch()
    except Exception as e:
        print(f"❌ 启动失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()