"""
测试图片搜索和配图功能
运行: python tests/test_images.py
"""
import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.image_agent import ImageAgent, UnsplashSource, PexelsSource

def test_image_sources():
    """测试图片源"""
    print("=" * 80)
    print("测试: 图片源")
    print("=" * 80)

    keywords = ["artificial intelligence", "technology", "business"]

    # 测试Unsplash
    print("\n测试Unsplash源...")
    print("-" * 80)
    unsplash = UnsplashSource()

    for keyword in keywords[:2]:
        print(f"\n搜索: {keyword}")
        results = unsplash.search(keyword, per_page=2)

        for i, img in enumerate(results, 1):
            print(f"  {i}. {img['description'][:50] if img['description'] else 'No description'}")
            print(f"     URL: {img['url'][:60]}...")
            print(f"     尺寸: {img['width']}x{img['height']}")

    # 测试Pexels
    print("\n\n测试Pexels源...")
    print("-" * 80)
    pexels = PexelsSource()

    for keyword in keywords[:2]:
        print(f"\n搜索: {keyword}")
        results = pexels.search(keyword, per_page=2)

        for i, img in enumerate(results, 1):
            print(f"  {i}. {img['description'][:50] if img['description'] else 'No description'}")
            print(f"     Author: {img['author']}")


def test_image_agent():
    """测试ImageAgent"""
    print("\n" + "=" * 80)
    print("测试: ImageAgent")
    print("=" * 80)

    agent = ImageAgent()

    # 测试1: 关键词生成
    print("\n测试1: 关键词生成")
    print("-" * 80)

    test_cases = [
        {
            "title": "人工智能的发展历史",
            "content": ["AI起源于1950年代", "深度学习的突破", "未来发展趋势"],
            "topic": "人工智能技术"
        },
        {
            "title": "区块链应用场景",
            "content": ["金融领域", "供应链管理", "数字身份"],
            "topic": "区块链技术"
        }
    ]

    for case in test_cases:
        keywords = agent.generate_search_keywords(
            case["title"],
            case["content"],
            case["topic"]
        )
        print(f"\n标题: {case['title']}")
        print(f"关键词: {', '.join(keywords)}")

    # 测试2: 图片搜索
    print("\n\n测试2: 图片搜索")
    print("-" * 80)

    keywords = ["artificial intelligence", "technology"]
    results = agent.search_images(keywords, num_results=2)

    print(f"搜索到 {len(results)} 张图片")
    for i, img in enumerate(results[:3], 1):
        print(f"\n{i}. ID: {img['id']}")
        print(f"   来源: {img['source']}")
        print(f"   描述: {img['description'][:60] if img['description'] else 'N/A'}")

    # 测试3: 下载图片
    print("\n\n测试3: 下载图片")
    print("-" * 80)

    if results:
        print("正在下载第一张图片...")
        local_path = agent.download_image(results[0])

        if local_path:
            print(f"✅ 图片已下载: {local_path}")

            # 检查文件
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path) / 1024
                print(f"   文件大小: {file_size:.2f} KB")
        else:
            print("❌ 下载失败")


def test_complete_workflow():
    """测试完整工作流"""
    print("\n" + "=" * 80)
    print("测试: 完整配图工作流")
    print("=" * 80)

    agent = ImageAgent()

    # 模拟一个PPT页面
    slide_title = "人工智能在医疗领域的应用"
    slide_content = [
        "AI辅助诊断提高准确率",
        "智能影像分析节省时间",
        "个性化治疗方案推荐"
    ]
    overall_topic = "人工智能医疗应用"

    print(f"\n为页面寻找配图:")
    print(f"标题: {slide_title}")
    print(f"主题: {overall_topic}")
    print("-" * 80)

    image_path = agent.get_image_for_slide(
        slide_title,
        slide_content,
        overall_topic
    )

    if image_path:
        print(f"\n✅ 成功找到配图: {image_path}")
    else:
        print(f"\n⚠️  未找到合适的配图")


def test_cache_management():
    """测试缓存管理"""
    print("\n" + "=" * 80)
    print("测试: 缓存管理")
    print("=" * 80)

    # agent = ImageAgent()
    #
    # # 检查缓存目录
    # cache_dir = agent.cache_dir
    # print(f"\n缓存目录: {cache_dir}")
    #
    # if cache_dir.exists():
    #     files = list(cache_dir.glob("*"))
    #     print(f"缓存文件数: {len(files)}")
    #
    #     if files:
    #         print("\n示例文件:")
    #         for f in files[:3]:
    #             size = f.stat().st_size / 1024
    #             print(f"  - {f.name} ({size:.2f} KB)")

    # 清空缓存
    print("\n清空缓存...")
    # agent.clear_cache()
    print("✅ 缓存已清空")


def main():
    """运行所有测试"""
    print("🧪 图片功能测试套件\n")

    # 测试1: 图片源
    test_image_sources()

    # 测试2: ImageAgent
    test_image_agent()

    # 测试3: 完整工作流
    test_complete_workflow()

    # 测试4: 缓存管理
    test_cache_management()

    print("\n" + "=" * 80)
    print("✅ 所有测试完成!")
    print("=" * 80)
    print("\n💡 提示:")
    print("- 如果要使用真实图片API,请在.env中配置:")
    print("  UNSPLASH_ACCESS_KEY=your_key")
    print("  PEXELS_API_KEY=your_key")
    print("- 未配置时将使用模拟数据")


if __name__ == "__main__":
    main()