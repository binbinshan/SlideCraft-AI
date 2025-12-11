import os
import sys
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.agents import content_agent

load_dotenv()


def main():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    """测试内容修改功能"""
    print("=" * 70)
    topic = "保护野生动物的重要性"
    agent = content_agent.ContentAgent(api_key=api_key, model=model)
    outline = agent.generate_outline(topic=topic, num_slides=5, style="professional")
    print(outline)
    for slide in outline['slides']:
        print(f"Slide {slide['page']}: {slide['title']} ({slide['type']}) - {slide.get('description', '')}")
        content = agent.generate_slide_content(slide_info=slide, overall_topic=topic, total_pages=5, style="professional")
        print(content)
        print("=" * 10)

        if content['page_number'] == 3:
            m_content = agent.modify_content(content,"在每句话开头添加❤️")
            print(m_content)

"""
调用链路
generate_outline() - 生成PPT大纲
    ↓ PromptTemplates.create_outline_prompt() - 创建提示词
        ↓ PromptTemplates.SYSTEM_OUTLINE_DESIGNER (系统提示)
        ↓ PromptTemplates.get_outline_prompt() (用户提示)
    ↓ LLM 生成

循环大纲处理每页:
    ↓ agent.generate_slide_content() - 为每页生成内容
        ↓ 判断幻灯片类型 (slide_type):
            ↓ if "cover"
                ↓ _generate_cover_content() 生成封面内容
            ↓ if "conclusion"
                ↓ _generate_conclusion_content()
                    PromptTemplates.get_conclusion_prompt(用户提示)
                    PromptTemplates.SYSTEM_CONTENT_WRITER(系统提示)
                ↓ LLM 生成内容
            ↓ else
                ↓ _generate_content_page()
                    PromptTemplates.get_content_prompt(用户提示)
                    PromptTemplates.SYSTEM_CONTENT_WRITER(系统提示)          
                ↓ LLM 生成内容 
        ↓ agent.modify_content 修改幻灯片内容:
            ↓ PromptTemplates.get_modification_prompt(用户提示)
            ↓ PromptTemplates.SYSTEM_CONTENT_WRITER
            ↓ LLM 生成修改内容
"""
if __name__ == '__main__':
    main()