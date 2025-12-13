"""
测试意图检测系统
"""
import os
from dotenv import load_dotenv
from src.utils.intent_detector import IntentDetector

load_dotenv()

# 测试意图检测
def test_intent_detection():
    api_key = os.getenv('DEEPSEEK_API_KEY')
    base_url = os.getenv('OPENAI_BASE_URL')
    model = os.getenv('DEEPSEEK_MODEL')

    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        return

    detector = IntentDetector(
        api_key=api_key,
        base_url=base_url,
        model=model
    )


    # 测试消息列表
    test_messages = [
        {
            "message": "帮我做一个关于人工智能的PPT，10页",
            "expected_intent": "create_ppt",
            "context": {}
        },

        {
            "message": "修改第3页，添加更多数据分析的内容",
            "expected_intent": "modify_ppt",
            "context": {"topic": "人工智能", "contents": ["", "", ""]}
        },
        # {
        #     "message": "查看第5页的内容",
        #     "expected_intent": "view_content",
        #     "context": {"topic": "人工智能", "contents": ["", "", "", "", ""]}
        # },
        # {
        #     "message": "怎么使用这个系统？",
        #     "expected_intent": "ask_help",
        #     "context": {}
        # },
        # {
        #     "message": "当前的进度怎么样了？",
        #     "expected_intent": "check_status",
        #     "context": {"topic": "人工智能"}
        # },
        # {
        #     "message": "下载我的PPT文件",
        #     "expected_intent": "download_ppt",
        #     "context": {"ppt_path": "output/test.pptx"}
        # },
        # {
        #     "message": "你好，今天天气真好",
        #     "expected_intent": "general_chat",
        #     "context": {}
        # }
    ]

    print("=" * 60)
    print("🧪 测试意图检测系统")
    print("=" * 60)

    for i, test_case in enumerate(test_messages, 1):
        print(f"\n📝 测试案例 {i}:")
        print(f"消息: {test_case['message']}")
        print(f"期望意图: {test_case['expected_intent']}")

        try:
            intent, params = detector.detect_intent(
                test_case['message'],
                test_case['context']
            )

            print(f"检测意图: {intent}")
            print(f"置信度: {params.get('confidence', 0):.2f}")
            print(f"提取参数: {params}")

            if intent == test_case['expected_intent']:
                print("✅ 测试通过")
            else:
                print("❌ 测试失败")

        except Exception as e:
            print(f"❌ 错误: {str(e)}")

    print("\n" + "=" * 60)
    print("✨ 测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_intent_detection()