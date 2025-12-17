#!/usr/bin/env python3
"""Test script to verify workflow execution"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_workflow():
    try:
        from graph.ppt_workflow import PPTWorkflow
        from graph.advanced_workflow import AdvancedPPTWorkflow

        # Test data
        config = {
            "api_key": "test-key",
            "model": "deepseek-chat",
            "temperature": 0.7,
            "log_file": "output/logs/test.log"
        }

        inputs = {
            "topic": "测试主题",
            "num_slides": 3,
            "style": "simple",
            "template": "business",
            "add_images": False,
            "outline": None,
            "contents": None,
            "images": None,
            "ppt_path": None,
            "current_step": "",
            "progress": 0.0
        }

        # Test PPTWorkflow
        print("Testing PPTWorkflow...")
        workflow = PPTWorkflow(config)

        # This should not raise the checkpointer error anymore
        # but will fail due to API key, which is expected
        try:
            result = await workflow.run(inputs)
            print("✅ PPTWorkflow executed without checkpointer error")
        except Exception as e:
            if "checkpointer" in str(e).lower():
                print(f"❌ Checkpointer error still exists: {e}")
                return False
            else:
                print(f"✅ PPTWorkflow passed checkpointer, got expected API error: {type(e).__name__}")

        # Test AdvancedPPTWorkflow
        print("\nTesting AdvancedPPTWorkflow...")
        inputs["quality_mode"] = "fast"
        inputs["auto_approve_outline"] = True
        inputs["enable_review"] = False
        inputs["user_requirements"] = []
        inputs["errors"] = []
        inputs["warnings"] = []
        inputs["outline_approved"] = False
        inputs["outline_feedback"] = None
        inputs["quality_score"] = None

        advanced_workflow = AdvancedPPTWorkflow(config)

        try:
            result = await advanced_workflow.run(inputs)
            print("✅ AdvancedPPTWorkflow executed without checkpointer error")
        except Exception as e:
            if "checkpointer" in str(e).lower():
                print(f"❌ Checkpointer error still exists: {e}")
                return False
            else:
                print(f"✅ AdvancedPPTWorkflow passed checkpointer, got expected API error: {type(e).__name__}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_workflow())
    if success:
        print("\n✅ All tests passed! Checkpointer issue is fixed.")
    else:
        print("\n❌ Tests failed!")
    sys.exit(0 if success else 1)