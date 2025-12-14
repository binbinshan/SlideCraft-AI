"""
SlideCraft AI - Gradio Web界面
提供友好的用户交互体验
"""
import os
import sys
import gradio as gr
from dotenv import load_dotenv
import json
from datetime import datetime

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import SlideCrafter
from utils.helpers import (
    ensure_dir,
    estimate_generation_time,
    format_time,
    summarize_outline
)

load_dotenv()

# 全局变量存储当前会话
current_session = {
    "crafter": None,
    "outline": None,
    "contents": [],
    "ppt_path": None,
    "topic": None,
    "style": None,
    "template": None
}


def initialize_crafter():
    """初始化SlideCrafter实例"""
    if current_session["crafter"] is None:
        try:
            current_session["crafter"] = SlideCrafter(
                log_file=f"output/logs/app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            )
            return "✅ 系统初始化成功"
        except Exception as e:
            return f"❌ 初始化失败: {str(e)}"
    return "✅ 系统已就绪"


def generate_ppt(topic, num_slides, style, template, add_images, progress=gr.Progress()):
    """
    生成PPT的主函数

    Args:
        topic: 主题
        num_slides: 页数
        style: 风格
        template: 模板
        add_images: 是否添加配图
        progress: Gradio进度条

    Returns:
        (状态信息, 大纲预览, PPT文件路径, 下载按钮可见性)
    """
    if not topic or topic.strip() == "":
        return "❌ 请输入PPT主题", "", None, gr.update(visible=False)

    try:
        # 初始化
        progress(0, desc="初始化中...")
        initialize_crafter()
        crafter = current_session["crafter"]

        # 保存配置
        current_session["topic"] = topic
        current_session["style"] = style
        current_session["template"] = template

        # 估算时间
        estimated_time = estimate_generation_time(num_slides)
        if add_images:
            estimated_time += num_slides * 3

        status_msg = f"🚀 开始生成PPT...\n⏱️ 预计用时: {format_time(estimated_time)}\n"

        # 直接调用主程序的generate_ppt方法
        progress(0.1, desc="生成中...")

        ppt_path = crafter.generate_ppt(
            topic=topic,
            num_slides=num_slides,
            style=style,
            template=template,
            save_intermediate=True,
            add_images=add_images
        )

        # 获取生成的大纲和内容
        outline = crafter.agent.last_outline
        contents = crafter.agent.last_contents

        current_session["outline"] = outline
        current_session["contents"] = contents
        current_session["ppt_path"] = ppt_path

        # 生成大纲预览
        outline_preview = f"""
        📋 **大纲预览**
        
        **标题:** {outline['title']}
        **总页数:** {len(outline['slides'])}
        
        **页面结构:**
        """
        for slide in outline["slides"]:
            outline_preview += f"\n{slide['page']}. {slide['title']} ({slide['type']})"

        status_msg += f"\n✅ 大纲生成完成 ({len(outline['slides'])}页)"
        status_msg += f"\n✅ 所有内容生成完成"

        if add_images:
            status_msg += f"\n✅ 配图搜索完成"

        status_msg += f"\n\n🎉 **PPT生成成功!**\n📁 文件: {ppt_path}"

        return (
            status_msg,
            outline_preview,
            ppt_path,
            gr.update(visible=True)
        )

    except Exception as e:
        import traceback
        error_msg = f"❌ 生成失败: {str(e)}\n\n详细错误:\n{traceback.format_exc()}"
        return error_msg, "", None, gr.update(visible=False)


def modify_slide_content(slide_number, modification_request):
    """
    修改指定页面的内容

    Args:
        slide_number: 页码
        modification_request: 修改要求

    Returns:
        状态信息
    """
    if current_session["contents"] is None or len(current_session["contents"]) == 0:
        return "❌ 请先生成PPT"

    try:
        slide_idx = int(slide_number) - 1

        if slide_idx < 0 or slide_idx >= len(current_session["contents"]):
            return f"❌ 页码无效,请输入1-{len(current_session['contents'])}之间的数字"

        crafter = current_session["crafter"]
        original_content = current_session["contents"][slide_idx]

        # 修改内容
        modified_content = crafter.modify_slide(original_content, modification_request)
        current_session["contents"][slide_idx] = modified_content

        # 重新生成PPT
        from generators.ppt_generator import PPTGenerator
        generator = PPTGenerator(template=current_session["template"])
        ppt_path = generator.create_presentation(
            current_session["outline"],
            current_session["contents"]
        )
        current_session["ppt_path"] = ppt_path

        return f"✅ 第{slide_number}页已修改完成!\n📁 新文件: {ppt_path}"

    except ValueError:
        return "❌ 请输入有效的页码数字"
    except Exception as e:
        return f"❌ 修改失败: {str(e)}"


def regenerate_slide(slide_number):
    """
    重新生成指定页面

    Args:
        slide_number: 页码

    Returns:
        状态信息
    """
    if current_session["outline"] is None:
        return "❌ 请先生成PPT"

    try:
        slide_idx = int(slide_number) - 1

        if slide_idx < 0 or slide_idx >= len(current_session["outline"]["slides"]):
            return f"❌ 页码无效"

        crafter = current_session["crafter"]
        slide_info = current_session["outline"]["slides"][slide_idx]

        # 重新生成
        new_content = crafter.regenerate_slide(
            slide_info,
            current_session["topic"],
            len(current_session["outline"]["slides"]),
            current_session["style"]
        )
        current_session["contents"][slide_idx] = new_content

        # 重新生成PPT
        from generators.ppt_generator import PPTGenerator
        generator = PPTGenerator(template=current_session["template"])
        ppt_path = generator.create_presentation(
            current_session["outline"],
            current_session["contents"]
        )
        current_session["ppt_path"] = ppt_path

        return f"✅ 第{slide_number}页已重新生成!\n📁 新文件: {ppt_path}"

    except Exception as e:
        return f"❌ 重新生成失败: {str(e)}"


def view_slide_content(slide_number):
    """
    查看指定页面的内容

    Args:
        slide_number: 页码

    Returns:
        页面内容
    """
    if current_session["contents"] is None or len(current_session["contents"]) == 0:
        return "❌ 请先生成PPT"

    try:
        slide_idx = int(slide_number) - 1

        if slide_idx < 0 or slide_idx >= len(current_session["contents"]):
            return f"❌ 页码无效"

        content = current_session["contents"][slide_idx]

        preview = f"""
📄 **第{slide_number}页内容**

**标题:** {content.get('title', '')}

**内容:**
"""
        for i, point in enumerate(content.get('content', []), 1):
            preview += f"\n{i}. {point}"

        if 'notes' in content:
            preview += f"\n\n**备注:** {content['notes']}"

        return preview

    except Exception as e:
        return f"❌ 查看失败: {str(e)}"


# 创建Gradio界面
def create_interface():
    """创建Gradio界面"""

    # 确保输出目录存在
    ensure_dir("output")
    ensure_dir("output/logs")
    ensure_dir("output/image_cache")

    with gr.Blocks(
        title="SlideCraft AI - AI驱动的PPT生成系统",
        theme=gr.themes.Soft(),
        css="""
        .main-header {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .section-header {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 5px;
            margin-top: 15px;
        }
        """
    ) as app:

        # 标题
        gr.HTML("""
        <div class="main-header">
            <h1>🎨 SlideCraft AI</h1>
            <p>AI驱动的智能PPT生成系统</p>
            <p style="font-size: 0.9em; margin-top: 10px;">支持DeepSeek / OpenAI | 智能配图 | 多轮对话</p>
        </div>
        """)

        with gr.Tabs():
            # Tab 1: 生成PPT
            with gr.Tab("📝 生成PPT"):
                gr.Markdown("## 基础设置")

                with gr.Row():
                    with gr.Column(scale=2):
                        topic_input = gr.Textbox(
                            label="PPT主题",
                            placeholder="例如: 人工智能在医疗领域的应用",
                            lines=2
                        )

                with gr.Row():
                    num_slides = gr.Slider(
                        minimum=3,
                        maximum=20,
                        value=10,
                        step=1,
                        label="页数"
                    )

                    style_dropdown = gr.Dropdown(
                        choices=["professional", "creative", "academic", "startup", "teaching"],
                        value="professional",
                        label="内容风格"
                    )

                    template_dropdown = gr.Dropdown(
                        choices=["business", "creative", "academic"],
                        value="business",
                        label="视觉模板"
                    )

                with gr.Row():
                    add_images_checkbox = gr.Checkbox(
                        label="🖼️ 自动配图",
                        value=False,
                        info="为内容页自动搜索和添加相关图片(需要配置图片API或使用占位图)"
                    )

                generate_btn = gr.Button("🚀 生成PPT", variant="primary", size="lg")

                gr.Markdown("## 生成结果")

                with gr.Row():
                    with gr.Column():
                        status_output = gr.Textbox(
                            label="状态",
                            lines=8,
                            interactive=False
                        )

                    with gr.Column():
                        outline_output = gr.Textbox(
                            label="大纲预览",
                            lines=8,
                            interactive=False
                        )

                with gr.Row():
                    download_file = gr.File(
                        label="下载PPT",
                        visible=False
                    )

                # 绑定生成按钮
                generate_btn.click(
                    fn=generate_ppt,
                    inputs=[topic_input, num_slides, style_dropdown, template_dropdown, add_images_checkbox],
                    outputs=[status_output, outline_output, download_file, download_file]
                )

            # Tab 2: 编辑PPT
            with gr.Tab("✏️ 编辑PPT"):
                gr.Markdown("## 查看和修改页面内容")

                with gr.Row():
                    view_slide_num = gr.Number(
                        label="页码",
                        value=1,
                        minimum=1,
                        precision=0
                    )
                    view_btn = gr.Button("👁️ 查看内容")

                slide_content_output = gr.Textbox(
                    label="页面内容",
                    lines=10,
                    interactive=False
                )

                view_btn.click(
                    fn=view_slide_content,
                    inputs=[view_slide_num],
                    outputs=[slide_content_output]
                )

                gr.Markdown("---")
                gr.Markdown("## 修改内容")

                with gr.Row():
                    modify_slide_num = gr.Number(
                        label="要修改的页码",
                        value=1,
                        minimum=1,
                        precision=0
                    )

                modification_input = gr.Textbox(
                    label="修改要求",
                    placeholder="例如: 添加更多数据支撑,或者换一个角度讲",
                    lines=3
                )

                with gr.Row():
                    modify_btn = gr.Button("🔄 修改内容", variant="primary")
                    regenerate_btn = gr.Button("🔁 重新生成")

                modify_status = gr.Textbox(
                    label="修改状态",
                    lines=3,
                    interactive=False
                )

                modify_btn.click(
                    fn=modify_slide_content,
                    inputs=[modify_slide_num, modification_input],
                    outputs=[modify_status]
                )

                regenerate_btn.click(
                    fn=regenerate_slide,
                    inputs=[modify_slide_num],
                    outputs=[modify_status]
                )

            # Tab 3: 使用帮助
            with gr.Tab("❓ 使用帮助"):
                gr.Markdown("""
                # 📖 使用指南
                
                ## 🚀 快速开始
                
                1. **生成PPT**
                   - 在"生成PPT"标签页输入主题
                   - 选择页数、风格和模板
                   - 选择是否启用自动配图
                   - 点击"生成PPT"按钮
                   - 等待生成完成后下载
                
                2. **编辑PPT**
                   - 在"编辑PPT"标签页查看各页内容
                   - 输入页码和修改要求
                   - 点击"修改内容"或"重新生成"
                
                ## 🎨 风格说明
                
                - **Professional (专业)**: 适合商务汇报、工作总结
                - **Creative (创意)**: 适合创意展示、产品发布
                - **Academic (学术)**: 适合学术报告、论文展示
                - **Startup (创业)**: 适合融资路演、商业计划
                - **Teaching (教学)**: 适合课程教学、培训演示
                
                ## 📄 模板说明
                
                - **Business (商务)**: 深蓝色调,简洁专业
                - **Creative (创意)**: 多彩设计,活泼生动
                - **Academic (学术)**: 灰蓝色调,严谨规范
                
                ## 🖼️ 配图功能
                
                1. **如何启用**: 勾选"自动配图"复选框
                2. **图片来源**: 
                   - 配置了API: 使用Unsplash/Pexels真实图片
                   - 未配置: 使用Lorem Picsum占位图
                3. **API配置**: 在.env文件中设置:
                   ```
                   UNSPLASH_ACCESS_KEY=your_key
                   PEXELS_API_KEY=your_key
                   ```
                4. **注意**: 配图会增加生成时间(每页约3秒)
                
                ## 💡 使用技巧
                
                1. **主题要具体**: "人工智能在医疗诊断中的应用" 比 "人工智能" 效果更好
                2. **合理页数**: 
                   - 简短汇报: 5-8页
                   - 标准演示: 10-15页
                   - 详细报告: 15-20页
                3. **修改建议**: 
                   - "添加具体数据"
                   - "换一个案例"
                   - "更简洁一些"
                   - "补充技术细节"
                
                ## ⚙️ 系统要求
                
                - 需要DeepSeek或OpenAI API密钥
                - 建议使用deepseek-chat或gpt-4o模型
                - 网络连接稳定
                
                ## 🐛 常见问题
                
                **Q: 生成失败怎么办?**
                A: 检查API密钥配置,确保网络连接正常,查看日志output/logs/
                
                **Q: 如何提高生成质量?**
                A: 提供更详细的主题描述,选择合适的风格
                
                **Q: 配图功能不工作?**
                A: 未配置API会使用占位图,这是正常的。如需真实图片请配置Unsplash/Pexels API
                
                **Q: 可以保存中间结果吗?**
                A: 可以,所有大纲和内容会保存在output/logs目录
                
                ## 📞 反馈与支持
                
                遇到问题或有建议?
                - 查看日志: output/logs/
                - GitHub Issues
                - 邮件联系
                
                ## 🔧 命令行使用
                
                ```bash
                # 基本使用
                python src/main.py "AI技术发展" -n 8
                
                # 带配图
                python src/main.py "AI在医疗中的应用" -n 10 --add-images
                
                # 指定风格和模板
                python src/main.py "区块链技术" -n 12 -s startup -t creative
                ```
                """)

        # 页面加载时初始化
        app.load(fn=initialize_crafter, outputs=None)

    return app


if __name__ == "__main__":
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )