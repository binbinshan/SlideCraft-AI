"""
SlideCraft AI - 高级界面
支持对话历史和智能交互
"""
import os
import sys
import json
import gradio as gr
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import SlideCrafter
from generators.ppt_generator import PPTGenerator
from utils.conversation import ConversationManager
from utils.helpers import ensure_dir, Logger
from utils.intent_detector import IntentDetector

load_dotenv()

# 全局对话管理器
conv_manager = ConversationManager()
crafter = None
intent_detector = None
logger = Logger(log_file="output/logs/app_advanced.log")


def initialize():
    """初始化系统"""
    global crafter, intent_detector
    if crafter is None:
        crafter = SlideCrafter()

    # 初始化意图检测器
    if intent_detector is None:
        api_key = os.getenv('DEEPSEEK_API_KEY')
        base_url = os.getenv('OPENAI_BASE_URL')
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment variables")

        logger.info(message=f"api_key= {api_key},base_url = {base_url} ")
        intent_detector = IntentDetector(
            api_key=api_key,
            base_url=base_url,
            model=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        )

    # 创建新会话
    session = conv_manager.create_session()
    session.add_system_message("系统初始化完成")

    return session.session_id, "✅ 系统已就绪,开始新对话"


def process_message(message, session_id, chat_history):
    """
    处理用户消息 - 使用LLM智能理解用户意图

    Args:
        message: 用户消息
        session_id: 会话ID
        chat_history: 聊天历史

    Returns:
        更新后的聊天历史
    """
    global crafter, intent_detector
    session = conv_manager.get_session(session_id)
    if session is None:
        return chat_history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": "❌ 会话已过期,请刷新页面"}
        ]

    # 添加用户消息
    session.add_user_message(message)

    # 使用LLM检测用户意图
    context = session.get_all_context()
    intent, parameters = intent_detector.detect_intent(message, context)
    logger.info(f"intent = {intent} ,parameters = {parameters}")
    # 根据意图执行相应操作
    if intent == "create_ppt":
        topic = parameters.get("topic")
        if not topic:
            # 如果LLM没有提取到主题，使用备用方法
            topic = intent_detector.extract_topic_from_message(message)

        if topic:
            # 从LLM参数中获取或使用默认值
            num_slides = parameters.get("num_slides", 5)
            logger.info(num_slides)
            if isinstance(num_slides, str) and num_slides.isdigit():
                num_slides = int(num_slides)
            num_slides = min(20, max(3, num_slides))

            style = parameters.get("style", "professional")
            template = parameters.get("template", "business")

            # 如果LLM提供了建议回复，使用它
            if parameters.get("response_suggestion"):
                response = parameters["response_suggestion"]
            else:
                response = f"🎯 正在为您生成主题为「{topic}」的PPT...\n\n"
                response += f"📋 主题: {topic}\n"
                response += f"📊 页数: {num_slides}\n"
                response += f"🎨 风格: {style}\n\n"
                response += "⏳ 正在生成中，请稍候..."

            # 保存上下文
            session.update_context(
                topic=topic,
                num_slides=num_slides,
                style=style,
                template=template
            )

            try:
                # 实际生成PPT
                if crafter is None:
                    crafter = SlideCrafter()

                ppt_path = crafter.generate_ppt(
                    topic=topic,
                    num_slides=num_slides,
                    style=style,
                    template=template
                )

                # 保存生成的PPT信息到会话
                session.update_context(
                    ppt_path=ppt_path,
                    outline=crafter.agent.last_outline if hasattr(crafter.agent, 'last_outline') else None,
                    contents=crafter.agent.last_contents if hasattr(crafter.agent, 'last_contents') else None
                )
                logger.info(session.get_all_context())
                response = f"✅ PPT生成成功!\n\n"
                response += f"📁 文件位置: {ppt_path}\n"
                response += f"📋 主题: {topic}\n"
                response += f"📊 页数: {num_slides}\n\n"
                response += "您可以:\n"
                response += "• 下载PPT文件\n"
                response += "• 说「修改第X页」来调整内容\n"
                response += "• 说「查看第X页」来查看具体内容"

            except Exception as e:
                response = f"❌ PPT生成失败: {str(e)}\n\n"
                response += "请检查:\n"
                response += "• API密钥是否配置正确\n"
                response += "• 网络连接是否正常\n"
                response += "• 重试或调整参数"
        else:
            # 没有主题，询问详情
            if parameters.get("response_suggestion"):
                response = parameters["response_suggestion"]
            else:
                response = "🎯 我理解您想生成一个新的PPT。\n\n"
                response += "为了更好地帮助您,请提供以下信息:\n"
                response += "1. PPT的主题是什么?\n"
                response += "2. 需要多少页?(建议5-15页)\n"
                response += "3. 适用场景?(商务汇报/教学/创意展示等)\n\n"
                response += "例如: 「生成一个关于人工智能的PPT，10页，商务风格」"

    elif intent == "modify_ppt":
        if session.get_context("topic"):
            # 从LLM参数中获取页码和修改内容
            page_num = parameters.get("page_number")
            modification_request = parameters.get("new_content")

            # 如果LLM没有提取到，使用备用方法
            if not page_num:
                page_num = intent_detector.extract_page_number(message)
            if not modification_request:
                modification_request = message  # 使用整个消息作为修改请求

            # 确保 page_num 是整数
            if page_num:
                try:
                    if isinstance(page_num, str) and page_num.isdigit():
                        page_num = int(page_num)
                    elif isinstance(page_num, float):
                        page_num = int(page_num)
                    elif not isinstance(page_num, int):
                        page_num = None
                except:
                    page_num = None

            if page_num and modification_request:
                # 有具体的修改要求，执行修改
                contents = session.get_context("contents")
                outline = session.get_context("outline")
                logger.info(contents)
                if contents and 0 < page_num <= len(contents):
                    response = f"✏️ 正在修改第{page_num}页...\n\n"

                    try:
                        if crafter is None:
                            crafter = SlideCrafter()

                        # 修改内容
                        original_content = contents[page_num - 1]
                        modified_content = crafter.modify_slide(
                            original_content,
                            modification_request
                        )

                        # 更新内容列表
                        contents[page_num - 1] = modified_content
                        session.update_context(contents=contents)

                        # 重新生成PPT
                        template = session.get_context("template")
                        generator = PPTGenerator(template=template)
                        ppt_path = generator.create_presentation(outline, contents)
                        session.update_context(ppt_path=ppt_path)

                        # 记录修改历史
                        modifications = session.get_context("modifications") or []
                        modifications.append({
                            "page": page_num,
                            "request": modification_request,
                            "timestamp": datetime.now().isoformat()
                        })
                        session.update_context(modifications=modifications)

                        response = f"✅ 第{page_num}页修改完成!\n\n"
                        response += f"修改内容: {modification_request}\n"
                        response += f"📁 文件已更新: {ppt_path}\n\n"
                        response += "您可以:\n"
                        response += "• 继续修改其他页面\n"
                        response += "• 下载更新后的PPT\n"
                        response += "• 查看修改后的内容"

                    except Exception as e:
                        response = f"❌ 修改失败: {str(e)}"
                else:
                    response = f"❌ 页码超出范围。当前PPT共{len(contents) if contents else 0}页。"
            else:
                # 询问具体修改内容
                if parameters.get("response_suggestion"):
                    response = parameters["response_suggestion"]
                else:
                    response = "✏️ 我理解您想修改PPT内容。\n\n"
                    response += f"当前PPT主题: {session.get_context('topic')}\n"
                    response += f"总页数: {len(session.get_context('contents') or [])}\n\n"
                    response += "请告诉我:\n"
                    response += "1. 要修改哪一页?(如: 第3页)\n"
                    response += "2. 具体要怎么修改?\n\n"
                    response += "例如: 「修改第3页，添加更多数据分析的内容」"
        else:
            response = "看起来还没有生成PPT,请先生成一个PPT吧!"

    elif intent == "view_content":
        page_num = parameters.get("page_number")

        # 确保 page_num 是整数
        if page_num:
            try:
                if isinstance(page_num, str) and page_num.isdigit():
                    page_num = int(page_num)
                elif isinstance(page_num, float):
                    page_num = int(page_num)
                elif not isinstance(page_num, int):
                    page_num = None
            except:
                page_num = None

        if page_num:
            # 查看特定页面
            contents = session.get_context("contents")
            if contents and 0 < page_num <= len(contents):
                content = contents[page_num - 1]
                response = f"📄 第{page_num}页内容：\n\n{content}\n\n"
            else:
                response = f"❌ 页码超出范围。当前PPT共{len(contents) if contents else 0}页。"
        else:
            # 查看整体信息
            if parameters.get("response_suggestion"):
                response = parameters["response_suggestion"]
            else:
                response = "👁️ 我理解您想查看PPT内容。\n\n"
                if session.get_context("topic"):
                    response += f"当前PPT: {session.get_context('topic')}\n"
                    response += "请在【编辑PPT】标签页选择页码查看详细内容。"
                else:
                    response += "还没有生成PPT哦,要不要先创建一个?"

    elif intent == "download_ppt":
        ppt_path = session.get_context("ppt_path")
        if ppt_path and os.path.exists(ppt_path):
            response = f"📥 您可以下载PPT文件：{ppt_path}\n\n"
            response += "文件已保存在output目录下。"
        else:
            response = "还没有可下载的PPT文件，请先生成一个PPT吧！"

    elif intent == "ask_help":
        if parameters.get("response_suggestion"):
            response = parameters["response_suggestion"]
        else:
            response = "📖 很高兴为您提供帮助!\n\n"
            response += "SlideCraft AI 主要功能:\n"
            response += "1. **生成PPT**: 输入主题,AI自动生成完整PPT\n"
            response += "2. **编辑内容**: 查看和修改任意页面\n"
            response += "3. **多种风格**: 支持商务、创意、学术等风格\n"
            response += "4. **智能对话**: 通过对话方式指导操作\n\n"
            response += "详细教程请查看【使用帮助】标签页。"

    elif intent == "check_status":
        if session.get_context("topic"):
            mods = len(session.get_context("modifications") or [])
            response = f"📊 当前进度:\n\n"
            response += f"PPT主题: {session.get_context('topic')}\n"
            response += f"已修改次数: {mods}\n"
            response += f"状态: ✅ 已完成"
        else:
            response = "还没有开始生成PPT哦!"

    else:  # general_chat or unknown intent
        if parameters.get("response_suggestion"):
            response = parameters["response_suggestion"]
        else:
            response = "🤔 我可能没有完全理解您的意思。\n\n"
            response += "您可以:\n"
            response += "• 说'生成PPT'开始创建演示文稿\n"
            response += "• 说'修改内容'来调整已生成的页面\n"
            response += "• 说'查看内容'来浏览PPT\n"
            response += "• 说'帮助'获取详细指南\n\n"
            response += "或者直接在各个标签页进行操作!"

    # 添加助手回复
    session.add_assistant_message(response)

    # 保存意图检测日志
    session.add_system_message(f"[意图检测] Intent: {intent}, Parameters: {json.dumps(parameters, ensure_ascii=False)}")

    # 更新聊天历史
    return chat_history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": response}
    ]


def create_advanced_interface():
    """创建高级界面"""

    ensure_dir("output")
    ensure_dir("output/logs")
    ensure_dir("output/conversations")

    with gr.Blocks(
            title="SlideCraft AI - 智能对话版"
    ) as app:

        gr.HTML("""
        <div class="main-header">
            <h1>🤖 SlideCraft AI - 智能对话版</h1>
            <p>通过自然对话生成和编辑PPT</p>
        </div>
        """)

        # 会话状态
        session_id = gr.State(value=None)

        with gr.Tabs():
            # Tab 1: 智能对话
            with gr.Tab("💬 智能对话"):
                gr.Markdown("""
                ## 与AI对话,轻松创建PPT

                您可以用自然语言告诉我您的需求,例如:
                - "帮我做一个关于人工智能的PPT"
                - "修改第3页,添加更多数据"
                - "查看第5页的内容"
                - "重新生成第2页"
                """)

                chatbot = gr.Chatbot(
                    label="对话历史",
                    show_label=True
                )

                with gr.Row():
                    msg_input = gr.Textbox(
                        label="输入消息",
                        placeholder="告诉我您想做什么...",
                        lines=2,
                        scale=4
                    )

                with gr.Row():
                    send_btn = gr.Button("发送", variant="primary")
                    clear_btn = gr.Button("清空对话")
                    save_btn = gr.Button("保存对话历史")

                save_status = gr.Textbox(label="状态", lines=1, interactive=False)

                # 绑定事件
                def user_submit(message, history, sess_id):
                    if not message.strip():
                        return history, ""
                    return process_message(message, sess_id, history), ""

                send_btn.click(
                    fn=user_submit,
                    inputs=[msg_input, chatbot, session_id],
                    outputs=[chatbot, msg_input]
                )

                msg_input.submit(
                    fn=user_submit,
                    inputs=[msg_input, chatbot, session_id],
                    outputs=[chatbot, msg_input]
                )

                def clear_chat():
                    return []

                clear_btn.click(
                    fn=clear_chat,
                    outputs=[chatbot]
                )

                def save_conversation(sess_id):
                    session = conv_manager.get_session(sess_id)
                    if session:
                        path = session.save()
                        return f"✅ 对话已保存: {path}"
                    return "❌ 没有对话记录"

                save_btn.click(
                    fn=save_conversation,
                    inputs=[session_id],
                    outputs=[save_status]
                )

            # Tab 3: 对话历史
            with gr.Tab("📜 对话历史"):
                gr.Markdown("## 查看对话摘要和历史记录")

                refresh_btn = gr.Button("🔄 刷新")

                summary_text = gr.Textbox(
                    label="对话摘要",
                    lines=8,
                    interactive=False
                )

                history_text = gr.Textbox(
                    label="完整历史",
                    lines=15,
                    interactive=False
                )

                def refresh_history(sess_id):
                    session = conv_manager.get_session(sess_id)
                    if session:
                        return session.summary(), session.format_for_display()
                    return "没有对话记录", ""

                refresh_btn.click(
                    fn=refresh_history,
                    inputs=[session_id],
                    outputs=[summary_text, history_text]
                )

        # 页面加载时初始化
        def on_load():
            sess_id, msg = initialize()
            return sess_id, [{"role": "assistant", "content": msg}]

        app.load(
            fn=on_load,
            outputs=[session_id, chatbot]
        )

    return app


if __name__ == "__main__":
    app = create_advanced_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7862,
        share=False,
        show_error=True,
        theme=gr.themes.Soft(),
        css="""
        .chat-container { height: 500px; overflow-y: auto; }
        .main-header {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        """
    )
