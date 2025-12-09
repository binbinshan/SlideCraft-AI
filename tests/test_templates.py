"""
测试Prompt模板效果
运行: python tests/test_prompts.py
"""
import os
import sys
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.prompts.templates import PromptTemplates

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("请在.env文件中设置DEEPSEEK_API_KEY")


def test_outline_generation():
    """测试大纲生成"""
    print("=" * 70)
    print("测试1: 大纲生成Prompt")
    print("=" * 70)

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    # 测试不同主题和风格
    test_cases = [
        {
            "topic": "如何成为一名AI Agent应用工程师",
            "num_slides": 6,
            "style": "professional"
        }
        # },
        # {
        #     "topic": "如何开始你的第一个创业项目",
        #     "num_slides": 10,
        #     "style": "startup"
        # },
        # {
        #     "topic": "Python编程基础入门",
        #     "num_slides": 12,
        #     "style": "teaching"
        # }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 测试案例 {i}:")
        print(f"   主题: {test['topic']}")
        print(f"   页数: {test['num_slides']}")
        print(f"   风格: {test['style']}")
        print("-" * 70)

        system_prompt, user_prompt = PromptTemplates.create_outline_prompt(
            test['topic'],
            test['num_slides'],
            test['style']
        )

        try:
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "deepseek-chat"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2048,
                temperature=0.7
            )

            response_text = response.choices[0].message.content.strip()
            response_text = re.sub(r'^```json\s*|\s*```$', '', response_text, flags=re.MULTILINE)

            outline = json.loads(response_text)

            print(f"✅ 生成成功!")
            print(f"   标题: {outline['title']}")
            print(f"   页数: {len(outline['slides'])}")
            print(f"\n   大纲预览:")
            for slide in outline['slides'][:3]:
                print(f"      第{slide['page']}页: {slide['title']} ({slide['type']})")
            if len(outline['slides']) > 3:
                print(f"      ...")
                last = outline['slides'][-1]
                print(f"      第{last['page']}页: {last['title']} ({last['type']})")

            # 保存结果
            output_dir = "output/test_prompts"
            os.makedirs(output_dir, exist_ok=True)
            with open(f"{output_dir}/outline_{i}.json", "w", encoding="utf-8") as f:
                json.dump(outline, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"❌ 生成失败: {str(e)}")
            continue

        print()


def test_content_generation():
    """测试内容生成"""
    print("\n" + "=" * 70)
    print("测试2: 内容生成Prompt")
    print("=" * 70)

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    # 读取所有outline JSON文件
    outline_dir = Path("output/test_prompts")
    outline_files = sorted(outline_dir.glob("outline_*.json"))

    if not outline_files:
        print(f"❌ 在 {outline_dir} 目录中未找到outline_*.json文件")
        return

    # 读取最后一个outline文件作为示例
    outline_file = outline_files[-1]
    print(f"\n📂 从文件加载: {outline_file.name}")

    with open(outline_file, 'r', encoding='utf-8') as f:
        outline_data = json.load(f)

    overall_topic = outline_data['title']
    print(f"\n📋 演示主题: {overall_topic}")
    print(f"📋 副标题: {outline_data.get('subtitle', '')}")

    # 创建一个字典来存储所有生成的内容
    all_content = {
        "title": overall_topic,
        "subtitle": outline_data.get('subtitle', ''),
        "total_pages": len(outline_data['slides']),
        "slides": []
    }

    # 遍历所有幻灯片（包括封面页和总结页）
    all_slides = outline_data['slides']

    for slide_info in all_slides:
        print(f"\n" + "-" * 70)
        print(f"📝 处理页面 {slide_info['page']}:")
        print(f"   标题: {slide_info['title']}")
        print(f"   类型: {slide_info['type']}")

        # 对于封面页和总结页，直接添加基本信息，不需要生成内容
        if slide_info['type'] in ['cover', 'conclusion']:
            slide_content = {
                "page": slide_info['page'],
                "type": slide_info['type'],
                "title": slide_info['title'],
                "description": slide_info['description']
            }
            all_content["slides"].append(slide_content)
            print(f"   ✅ 已添加 {slide_info['type']} 页")
            continue

        print(f"   描述: {slide_info['description']}")
        print("-" * 70)

        system_prompt = PromptTemplates.SYSTEM_CONTENT_WRITER
        user_prompt = PromptTemplates.get_content_prompt(
            slide_info['title'],
            slide_info['description'],
            overall_topic,
            slide_info['page'],
            len(outline_data['slides']),
            "professional"
        )

        try:
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "deepseek-chat"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1024,
                temperature=0.7
            )

            response_text = response.choices[0].message.content.strip()
            response_text = re.sub(r'^```json\s*|\s*```$', '', response_text, flags=re.MULTILINE)

            content = json.loads(response_text)

            # 添加页面信息
            content['page'] = slide_info['page']
            content['type'] = slide_info['type']
            all_content["slides"].append(content)

            print(f"✅ 内容生成成功!")
            print(f"\n   标题: {content['title']}")
            print(f"   要点:")
            for i, point in enumerate(content['content'], 1):
                print(f"      {i}. {point}")
            if 'notes' in content:
                print(f"\n   备注: {content['notes']}")

        except Exception as e:
            print(f"❌ 生成失败: {str(e)}")
            # 即使生成失败，也保留基本信息
            slide_content = {
                "page": slide_info['page'],
                "type": slide_info['type'],
                "title": slide_info['title'],
                "description": slide_info['description'],
                "content": [],
                "error": str(e)
            }
            all_content["slides"].append(slide_content)
            continue

    # 保存所有内容到一个JSON文件
    output_dir = "output/test_prompts"
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"{output_dir}/complete_content_{outline_file.stem}.json"

    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(all_content, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"✅ 所有内容已保存到: {output_filename}")
    print(f"   总共处理了 {len(all_content['slides'])} 页幻灯片")
    print("=" * 70)


def test_different_styles():
    """测试不同风格的效果"""
    print("\n" + "=" * 70)
    print("测试3: 不同风格对比")
    print("=" * 70)

    topic = "区块链技术的发展与应用"
    styles = ["professional", "creative", "academic", "startup"]

    for style in styles:
        print(f"\n🎨 风格: {style}")
        print("-" * 70)

        guidelines = PromptTemplates.get_style_guidelines(style)
        print(f"   语调: {guidelines['tone']}")
        print(f"   语言: {guidelines['language']}")
        print(f"   结构: {guidelines['structure']}")


def main():
    """主测试函数"""
    print("🧪 Prompt模板测试套件")
    print()

    # 测试1: 大纲生成
    test_outline_generation()

    # 测试2: 内容生成
    test_content_generation()

    # 测试3: 风格对比
    # test_different_styles()

    print("\n" + "=" * 70)
    print("✅ 所有测试完成!")
    print("   查看生成的文件: output/test_prompts/")
    print("=" * 70)


if __name__ == "__main__":
    main()
