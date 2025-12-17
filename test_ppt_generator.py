#!/usr/bin/env python3
"""Test PPT generator to verify the template fix"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_ppt_generator():
    try:
        from generators.ppt_generator import PPTGenerator

        # Test with template initialization
        print("Testing PPTGenerator with template initialization...")
        generator = PPTGenerator(template="business")

        # Verify template is properly set
        if isinstance(generator.template, dict):
            print("✅ Template is properly set as a dictionary")
            print(f"   Template name: {generator.template.get('name', 'Unknown')}")
        else:
            print(f"❌ Template is not a dictionary: {type(generator.template)}")
            return False

        # Test creating a simple presentation
        outline = {
            "title": "Test Presentation",
            "slides": [
                {"type": "cover", "title": "Test Title", "page": 1},
                {"type": "content", "title": "Content Slide", "page": 2},
                {"type": "conclusion", "title": "Thank You", "page": 3}
            ]
        }

        contents = [
            {"title": "Test Title", "subtitle": "Test Subtitle", "type": "cover", "content": []},
            {"title": "Content Slide", "content": ["Point 1", "Point 2", "Point 3"], "type": "content"},
            {"title": "Thank You", "content": ["Thanks for listening"], "type": "conclusion"}
        ]

        print("\nCreating test presentation...")
        try:
            # Ensure output directory exists
            os.makedirs("output", exist_ok=True)

            ppt_path = generator.create_presentation(
                outline=outline,
                contents=contents
            )
            print(f"✅ PPT created successfully: {ppt_path}")

            # Verify file exists
            if os.path.exists(ppt_path):
                print("✅ PPT file exists on disk")
                return True
            else:
                print("❌ PPT file not found on disk")
                return False

        except Exception as e:
            print(f"❌ PPT creation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ppt_generator()
    if success:
        print("\n✅ PPT generator test passed!")
    else:
        print("\n❌ PPT generator test failed!")
    sys.exit(0 if success else 1)