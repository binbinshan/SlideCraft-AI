"""
测试 LangChain/LangGraph 重构后的功能
"""
import os
import sys
import asyncio
import json
from dotenv import load_dotenv

# 添加 src 目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()


async def test_langchain_content_agent():
    """测试 LangChain Content Agent"""
    print("\n" + "="*60)
    print("测试 LangChain Content Agent")
    print("="*60)

    from agents.langchain_content_agent import LangChainContentAgent

    agent = LangChainContentAgent(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        model="deepseek-chat"
    )

    # 测试异步大纲生成
    print("\n1. 测试异步大纲生成...")
    try:
        outline = await agent.generate_outline_async(
            topic="人工智能在医疗领域的应用",
            num_slides=8,
            style="professional"
        )
        print(f"✅ 大纲生成成功: {outline['title']}")
        print(f"   生成页数: {len(outline['slides'])}")
    except Exception as e:
        print(f"❌ 大纲生成失败: {str(e)}")

    # 测试异步批量内容生成
    print("\n2. 测试异步批量内容生成...")
    try:
        if 'outline' in locals():
            contents = await agent.generate_batch_contents_async(
                slides_info=outline["slides"],
                overall_topic="人工智能在医疗领域的应用",
                total_pages=8,
                style="professional"
            )
            print(f"✅ 内容生成成功: {len(contents)} 页")
            print(f"   第一页标题: {contents[0].get('title', 'N/A')}")
        else:
            print("⚠️ 跳过内容生成（大纲生成失败）")
    except Exception as e:
        print(f"❌ 内容生成失败: {str(e)}")


async def test_basic_workflow():
    """测试基础工作流"""
    print("\n" + "="*60)
    print("测试基础 PPT 工作流")
    print("="*60)

    from graph.ppt_workflow import PPTWorkflow

    config = {
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "model": "deepseek-chat",
        "log_file": f"output/logs/test_workflow_{format_timestamp()}.log"
    }

    workflow = PPTWorkflow(config)

    # 测试输入
    inputs = {
        "topic": "机器学习基础入门",
        "num_slides": 6,
        "style": "teaching",
        "template": "academic",
        "add_images": False,  # 测试时不添加图片
        "outline": None,
        "contents": None,
        "images": None,
        "ppt_path": None,
        "current_step": "",
        "progress": 0.0,
        "errors": [],
        "timestamp": format_timestamp(),
        "log_file": config["log_file"]
    }

    try:
        # 运行工作流
        print("\n开始运行工作流...")
        final_state = await workflow.run(inputs)

        if final_state.get("errors"):
            print("❌ 工作流出错:")
            for error in final_state["errors"]:
                print(f"   - {error}")
        else:
            print("✅ 工作流执行成功!")
            print(f"   PPT路径: {final_state.get('ppt_path', 'N/A')}")
            print(f"   最终进度: {final_state.get('progress', 0)*100:.1f}%")

    except Exception as e:
        print(f"❌ 工作流执行失败: {str(e)}")


async def test_advanced_workflow():
    """测试高级工作流"""
    print("\n" + "="*60)
    print("测试高级 PPT 工作流（质量检查）")
    print("="*60)

    from graph.advanced_workflow import AdvancedPPTWorkflow

    config = {
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "model": "deepseek-chat",
        "log_file": f"output/logs/test_advanced_{format_timestamp()}.log"
    }

    workflow = AdvancedPPTWorkflow(config)

    # 测试输入
    inputs = {
        "topic": "深度学习研究进展",
        "num_slides": 10,
        "style": "academic",
        "template": "academic",
        "add_images": False,
        "quality_mode": "high",
        "auto_approve_outline": False,
        "enable_review": True,
        "user_requirements": [],
        "current_step": "",
        "progress": 0.0,
        "errors": [],
        "warnings": [],
        "timestamp": format_timestamp(),
        "log_file": config["log_file"],
        "thread_id": None,
        "start_time": None,
        "end_time": None,
        "outline": None,
        "outline_approved": False,
        "outline_feedback": None,
        "contents": None,
        "images": None,
        "quality_score": None,
        "ppt_path": None,
        "generation_report": None
    }

    try:
        print("\n开始运行高级工作流...")
        final_state = await workflow.run(inputs)

        if final_state.get("errors"):
            print("❌ 高级工作流出错:")
            for error in final_state["errors"]:
                print(f"   - {error}")
        else:
            print("✅ 高级工作流执行成功!")
            print(f"   质量评分: {final_state.get('quality_score', 'N/A')}/100")
            print(f"   警告数量: {len(final_state.get('warnings', []))}")
            if final_state.get("generation_report"):
                report = final_state["generation_report"]
                print(f"   生成耗时: {report.get('duration_seconds', 0):.1f}秒")

    except Exception as e:
        print(f"❌ 高级工作流执行失败: {str(e)}")


def test_integration_tools():
    """测试集成工具"""
    print("\n" + "="*60)
    print("测试 LangChain 集成工具")
    print("="*60)

    from utils.langchain_integration import LangChainIntegration

    integration = LangChainIntegration({
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "model": "deepseek-chat",
        "log_file": f"output/logs/test_integration_{format_timestamp()}.log"
    })

    # 测试主题分析
    print("\n1. 测试主题分析...")
    try:
        analysis = integration.create_chain_of_thought(
            topic="量子计算的商业化前景",
            requirements=["需要包含实际案例", "分析技术挑战", "讨论市场机会"]
        )
        print("✅ 主题分析完成")
        print("   分析结果片段:", analysis[:100] + "...")
    except Exception as e:
        print(f"❌ 主题分析失败: {str(e)}")

    # 测试参数优化
    print("\n2. 测试参数优化...")
    try:
        params = integration.optimize_generation_params(
            topic="人工智能在医疗领域的应用",
            style="academic",
            previous_attempts=[
                {"temperature": 0.9, "success": False},
                {"temperature": 0.5, "success": True}
            ]
        )
        print("✅ 参数优化完成")
        print(f"   优化后温度: {params.get('temperature', 'N/A')}")
    except Exception as e:
        print(f"❌ 参数优化失败: {str(e)}")


def test_slidecrafter_v2():
    """测试 SlideCrafter V2"""
    print("\n" + "="*60)
    print("测试 SlideCrafter V2")
    print("="*60)

    from main_langgraph import SlideCrafterV2

    crafter = SlideCrafterV2(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        model="deepseek-chat"
    )

    # 测试进度回调
    progress_updates = []
    def progress_callback(progress: float, step: str):
        progress_updates.append((progress, step))
        print(f"   进度更新: {step} ({progress*100:.1f}%)")

    print("\n测试异步PPT生成...")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            crafter.generate_ppt_async(
                topic="区块链技术简介",
                num_slides=5,
                style="startup",
                template="creative",
                add_images=False,
                progress_callback=progress_callback
            )
        )

        loop.close()

        if result["success"]:
            print("✅ PPT生成成功!")
            print(f"   文件路径: {result['ppt_path']}")
            print(f"   用时: {result['elapsed_time']:.1f}秒")
            print(f"   进度更新次数: {len(progress_updates)}")
        else:
            print("❌ PPT生成失败:")
            print(f"   错误: {result.get('error', 'N/A')}")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")


def format_timestamp():
    """格式化时间戳"""
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")


async def main():
    """运行所有测试"""
    print("🚀 开始测试 LangChain/LangGraph 重构版本")
    print("="*60)

    # 检查环境
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ 错误: 请设置 DEEPSEEK_API_KEY 环境变量")
        return

    # 确保输出目录存在
    os.makedirs("output", exist_ok=True)
    os.makedirs("output/logs", exist_ok=True)
    os.makedirs("output/image_cache", exist_ok=True)

    # 运行测试
    tests = [
        ("LangChain Content Agent", test_langchain_content_agent),
        ("基础工作流", test_basic_workflow),
        ("高级工作流", test_advanced_workflow),
        ("集成工具", test_integration_tools),
        ("SlideCrafter V2", test_slidecrafter_v2)
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"运行测试: {test_name}")
        print('='*60)

        try:
            start_time = asyncio.get_event_loop().time()
            await test_func() if asyncio.iscoroutinefunction(test_func) else test_func()
            elapsed = asyncio.get_event_loop().time() - start_time
            results[test_name] = {"status": "✅ 通过", "time": f"{elapsed:.1f}s"}
        except Exception as e:
            results[test_name] = {"status": "❌ 失败", "error": str(e)}

    # 输出测试总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    for test_name, result in results.items():
        status = result["status"]
        if "✅" in status:
            print(f"{status} {test_name} ({result.get('time', 'N/A')})")
        else:
            print(f"{status} {test_name} - {result.get('error', 'Unknown error')}")

    print("\n✨ 测试完成!")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())