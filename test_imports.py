#!/usr/bin/env python3
"""Test script to verify all imports work correctly"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    try:
        from agents.langchain_content_agent import LangChainContentAgent
        print("✅ LangChainContentAgent imported successfully")

        from utils.langchain_integration import LangChainIntegration
        print("✅ LangChainIntegration imported successfully")

        from graph.advanced_workflow import AdvancedPPTWorkflow, AdvancedPPTState
        print("✅ AdvancedPPTWorkflow imported successfully")

        from graph.ppt_workflow import PPTWorkflow, PPTGenerationState
        print("✅ PPTWorkflow imported successfully")

        return True

    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)