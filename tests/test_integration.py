"""
集成测试 - 测试完整流程
运行: python tests/test_integration.py
"""
import os
import sys
from dotenv import load_dotenv

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import SlideCrafter
from utils.helpers import ensure_dir

load_dotenv()


def test_complete_workflow():
    """测试完整的生成流程"""
    print("=" * 80)
    print("集成测试: 完整工作流")
    print("=" * 80)

    # 测试用例
    test_cases = [
        {
            "topic": "机器学习基础入门",
            "num_slides": 6,
            "style": "teaching",
            "template": "business"
        },
        {
            "topic": "创业公司融资策略",
            "num_slides": 8,
            "style": "startup",
            "template": "creative"
        }
    ]

    crafter = SlideCrafter()

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"测试案例 {i}/{len(test_cases)}")
        print(f"{'=' * 80}")

        try:
            ppt_path = crafter.generate_ppt(
                topic=test["topic"],
                num_slides=test["num_slides"],
                style=test["style"],
                template=test["template"],
                save_intermediate=True
            )

            # 验证文件存在
            if os.path.exists(ppt_path):
                file_size = os.path.getsize(ppt_path) / 1024  # KB
                print(f"\n✅ 测试通过!")
                print(f"   文件大小: {file_size:.2f} KB")
            else:
                print(f"\n❌ 测试失败: 文件不存在")

        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()


def test_different_styles():
    """测试不同风格"""
    print("\n" + "=" * 80)
    print("风格测试: 测试所有风格")
    print("=" * 80)

    topic = "数字化转型的关键要素"
    styles = ["professional", "creative", "academic", "startup", "teaching"]

    crafter = SlideCrafter()

    for style in styles:
        print(f"\n测试风格: {style}")
        print("-" * 80)

        try:
            ppt_path = crafter.generate_ppt(
                topic=topic,
                num_slides=5,
                style=style,
                template="business",
                save_intermediate=False
            )
            print(f"✅ {style}风格测试通过")

        except Exception as e:
            print(f"❌ {style}风格测试失败: {str(e)}")


def test_different_templates():
    """测试不同模板"""
    print("\n" + "=" * 80)
    print("模板测试: 测试所有模板")
    print("=" * 80)

    topic = "产品发布策略"
    templates = ["business", "creative", "academic"]

    crafter = SlideCrafter()

    for template in templates:
        print(f"\n测试模板: {template}")
        print("-" * 80)

        try:
            ppt_path = crafter.generate_ppt(
                topic=topic,
                num_slides=5,
                style="professional",
                template=template,
                save_intermediate=False
            )
            print(f"✅ {template}模板测试通过")

        except Exception as e:
            print(f"❌ {template}模板测试失败: {str(e)}")


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 80)
    print("边界测试")
    print("=" * 80)

    crafter = SlideCrafter()

    # 测试1: 最少页数
    print("\n测试1: 最少页数(3页)")
    try:
        crafter.generate_ppt(
            topic="简短演示",
            num_slides=3,
            save_intermediate=False
        )
        print("✅ 最少页数测试通过")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

    # 测试2: 较多页数
    print("\n测试2: 较多页数(15页)")
    try:
        crafter.generate_ppt(
            topic="详细技术报告",
            num_slides=15,
            save_intermediate=False
        )
        print("✅ 较多页数测试通过")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

    # 测试3: 特殊字符
    print("\n测试3: 特殊字符处理")
    try:
        crafter.generate_ppt(
            topic="AI技术 & 应用: 2024年趋势",
            num_slides=5,
            save_intermediate=False
        )
        print("✅ 特殊字符测试通过")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")


def main():
    """运行所有测试"""
    ensure_dir("output")
    ensure_dir("output/logs")

    print("🧪 SlideCraft AI 集成测试套件\n")

    # 测试1: 完整工作流
    test_complete_workflow()

    # 测试2: 不同风格
    test_different_styles()

    # 测试3: 不同模板
    test_different_templates()

    # 测试4: 边界情况
    test_edge_cases()

    print("\n" + "=" * 80)
    print("✅ 所有测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    main()