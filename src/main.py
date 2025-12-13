"""
SlideCraft AI 主程序
整合所有模块,提供完整的PPT生成功能
"""
import os
import time
from typing import Dict, List
from dotenv import load_dotenv

from agents.content_agent import ContentAgent
from generators.ppt_generator import PPTGenerator
from utils.helpers import (
    ensure_dir,
    save_json,
    format_timestamp,
    estimate_generation_time,
    format_time,
    summarize_outline,
    create_progress_bar,
    Logger
)

load_dotenv()


class SlideCrafter:
    """SlideCraft AI 主类"""

    def __init__(
            self,
            api_key: str = None,
            model: str = None,
            log_file: str = None
    ):
        """
        初始化SlideCrafter

        Args:
            api_key: OpenAI API密钥
            model: 模型名称
            log_file: 日志文件路径
        """
        # API配置
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "deepseek-chat")

        if not self.api_key:
            raise ValueError("请设置OPENAI_API_KEY环境变量或传入api_key参数")

        # 初始化组件
        self.agent = ContentAgent(
            api_key=self.api_key,
            model=self.model,
        )

        self.logger = Logger(log_file)

        # 确保输出目录存在
        ensure_dir("output")
        ensure_dir("output/logs")

        self.logger.info("SlideCrafter初始化完成")

    def generate_ppt(
            self,
            topic: str,
            num_slides: int = 10,
            style: str = "professional",
            template: str = "business",
            save_intermediate: bool = True
    ) -> str:
        """
        生成完整的PPT

        Args:
            topic: PPT主题
            num_slides: 页数
            style: 内容风格
            template: 模板样式
            save_intermediate: 是否保存中间结果

        Returns:
            生成的PPT文件路径
        """
        start_time = time.time()
        timestamp = format_timestamp()

        print("=" * 80)
        print("🚀 SlideCraft AI 启动")
        print("=" * 80)
        print(f"📋 主题: {topic}")
        print(f"📊 页数: {num_slides}")
        print(f"🎨 风格: {style}")
        print(f"📄 模板: {template}")
        print(f"⏱️  预计时间: {format_time(estimate_generation_time(num_slides))}")
        print("=" * 80)

        self.logger.info(f"开始生成PPT: {topic}")

        try:
            # 步骤1: 生成大纲
            print("\n📝 步骤 1/3: 生成大纲...")
            outline = self.agent.generate_outline(topic, num_slides, style)

            # 保存大纲到 agent 属性
            self.agent.last_outline = outline

            print(f"\n{summarize_outline(outline)}")

            if save_intermediate:
                outline_path = f"output/logs/outline_{timestamp}.json"
                save_json(outline, outline_path)
                self.logger.info(f"大纲已保存: {outline_path}")

            # 步骤2: 生成内容
            print(f"\n📝 步骤 2/3: 生成各页内容...")
            contents = []
            total_slides = len(outline["slides"])

            for i, slide_info in enumerate(outline["slides"], 1):
                progress = create_progress_bar(i - 1, total_slides)
                print(f"\n{progress}")

                content = self.agent.generate_slide_content(
                    slide_info,
                    topic,
                    total_slides,
                    style
                )
                contents.append(content)

            print(f"\n{create_progress_bar(total_slides, total_slides)}")
            print("✅ 所有内容生成完成!")

            # 保存内容到 agent 属性
            self.agent.last_contents = contents

            if save_intermediate:
                contents_path = f"output/logs/contents_{timestamp}.json"
                save_json(contents, contents_path)
                self.logger.info(f"内容已保存: {contents_path}")

            # 步骤3: 创建PPT
            print(f"\n📝 步骤 3/3: 创建PPT文件...")
            generator = PPTGenerator(template=template)
            ppt_path = generator.create_presentation(outline, contents)

            # 完成
            elapsed_time = time.time() - start_time
            print("\n" + "=" * 80)
            print("🎉 PPT生成完成!")
            print("=" * 80)
            print(f"📁 文件位置: {ppt_path}")
            print(f"⏱️  用时: {format_time(int(elapsed_time))}")
            print(f"📊 总页数: {len(contents)}")
            print("=" * 80)

            self.logger.info(f"PPT生成成功: {ppt_path} (用时: {int(elapsed_time)}秒)")

            return ppt_path

        except Exception as e:
            self.logger.error(f"PPT生成失败: {str(e)}")
            print(f"\n❌ 生成失败: {str(e)}")
            raise

    def modify_slide(
            self,
            content: Dict,
            modification: str
    ) -> Dict:
        """
        修改某一页内容

        Args:
            content: 原始内容
            modification: 修改要求

        Returns:
            修改后的内容
        """
        return self.agent.modify_content(content, modification)

    def regenerate_slide(
            self,
            slide_info: Dict,
            topic: str,
            total_pages: int,
            style: str = "professional"
    ) -> Dict:
        """
        重新生成某一页

        Args:
            slide_info: 页面信息
            topic: 主题
            total_pages: 总页数
            style: 风格

        Returns:
            新生成的内容
        """
        return self.agent.generate_slide_content(
            slide_info,
            topic,
            total_pages,
            style
        )


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="SlideCraft AI - AI驱动的PPT生成系统")
    parser.add_argument("topic", help="PPT主题")
    parser.add_argument("-n", "--num-slides", type=int, default=10, help="页数(默认10)")
    parser.add_argument("-s", "--style", default="professional",
                        choices=["professional", "creative", "academic", "startup", "teaching"],
                        help="内容风格")
    parser.add_argument("-t", "--template", default="business",
                        choices=["business", "creative", "academic"],
                        help="模板样式")
    parser.add_argument("--no-save-intermediate", action="store_true",
                        help="不保存中间结果")

    args = parser.parse_args()

    # 创建实例
    crafter = SlideCrafter(
        log_file=f"output/logs/slidecraft_{format_timestamp()}.log"
    )

    # 生成PPT
    crafter.generate_ppt(
        topic=args.topic,
        num_slides=args.num_slides,
        style=args.style,
        template=args.template,
        save_intermediate=not args.no_save_intermediate
    )


if __name__ == "__main__":
    main()