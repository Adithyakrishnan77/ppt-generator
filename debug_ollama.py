#!/usr/bin/env python3
"""
Debug script to diagnose Ollama integration issues
"""

import subprocess
import json

def test_ollama_direct():
    """Test Ollama directly with a simple prompt"""
    print("🔍 Testing Ollama Direct Connection")
    print("-" * 50)
    
    simple_prompt = """You are a slide generator. Create exactly 2 slides about Python.
Return ONLY this JSON format:

<json>
[
  {"title": "Introduction to Python", "points": []},
  {"title": "Python Basics", "points": ["• Python is a programming language", "• It uses simple syntax"]}
]
</json>"""

    try:
        print("Sending request to llama3.1...")
        result = subprocess.run(
            ["ollama", "run", "llama3.1"],
            input=simple_prompt,
            text=True,
            capture_output=True,
            timeout=60,  # Increased timeout
            encoding="utf-8"
        )
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT length: {len(result.stdout)} characters")
        print(f"STDERR: {result.stderr}")
        print("\nRaw Ollama Response:")
        print("=" * 30)
        print(result.stdout)
        print("=" * 30)
        
        return result.stdout.strip()
        
    except subprocess.TimeoutExpired:
        print("❌ Ollama request timed out")
        return None
    except FileNotFoundError:
        print("❌ Ollama not found. Install with: curl -fsSL https://ollama.ai/install.sh | sh")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_json_extraction(response):
    """Test JSON extraction from Ollama response"""
    if not response:
        return None
        
    print("\n🔍 Testing JSON Extraction")
    print("-" * 50)
    
    # Try to find JSON tags
    import re
    json_match = re.search(r"<json>\s*(.*?)\s*</json>", response, re.DOTALL | re.IGNORECASE)
    
    if json_match:
        json_str = json_match.group(1).strip()
        print(f"Found JSON block: {len(json_str)} characters")
        print("JSON content:")
        print(json_str)
        
        # Try to parse
        try:
            parsed = json.loads(json_str)
            print(f"✅ Successfully parsed JSON: {type(parsed)}")
            return parsed
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            return None
    else:
        print("❌ No <json>...</json> tags found in response")
        return None

def test_model_availability():
    """Check what models are available"""
    print("\n🔍 Checking Available Models")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print("Available models:")
        print(result.stdout)
        
        # Check if qwen3 is available
        if "qwen3" in result.stdout:
            print("✅ qwen3 model found")
            return True
        else:
            print("❌ qwen3 model not found")
            print("Install with: ollama pull qwen3")
            return False
            
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False

def main():
    """Main diagnostic function"""
    print("🚀 Ollama Integration Diagnostics")
    print("=" * 60)
    
    # Step 1: Check model availability
    model_ok = test_model_availability()
    if not model_ok:
        print("\n❌ Fix: Run 'ollama pull qwen3' first")
        return False
    
    # Step 2: Test direct Ollama connection
    response = test_ollama_direct()
    if not response:
        print("\n❌ Ollama connection failed")
        return False
    
    # Step 3: Test JSON extraction
    parsed = test_json_extraction(response)
    if parsed:
        print("\n✅ Ollama integration working correctly!")
        return True
    else:
        print("\n❌ JSON parsing failed - prompt needs adjustment")
        return False

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n🔧 Suggested fixes:")
        print("1. Install qwen3: ollama pull qwen3")
        print("2. Try different model: ollama pull llama2")
        print("3. Check Ollama service: ollama serve")