#!/usr/bin/env python3
"""
Quick test script to verify your PPT generator is working correctly.
Run this to test both successful generation and stop functionality.
"""

import time
import threading
from backend import generate_presentation, GenerationStopped, PPTGenerationError

def test_successful_generation():
    """Test a complete successful generation"""
    print("🧪 Test 1: Successful Generation")
    print("-" * 40)
    
    try:
        file_path, metadata = generate_presentation(
            topic="Introduction to Python programming basics",
            font_name="Arial", 
            font_size=12
        )
        print(f"✅ SUCCESS: Generated {metadata['slide_count']} slides")
        print(f"📁 File: {file_path}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_stop_functionality():
    """Test the stop functionality"""
    print("\n🧪 Test 2: Stop Functionality")
    print("-" * 40)
    
    # Create stop event
    stop_event = threading.Event()
    
    def stop_after_delay():
        """Stop generation after 3 seconds"""
        time.sleep(3)
        print("⏹️ Sending stop signal...")
        stop_event.set()
    
    # Start stop timer
    stop_thread = threading.Thread(target=stop_after_delay, daemon=True)
    stop_thread.start()
    
    try:
        file_path, metadata = generate_presentation(
            topic="Create a comprehensive 20-slide presentation on machine learning algorithms including supervised learning, unsupervised learning, deep learning, neural networks, and practical applications",
            font_name="Arial",
            font_size=12,
            stop_event=stop_event
        )
        print(f"❌ UNEXPECTED: Generation completed despite stop signal")
        print("(This might happen if generation was very fast)")
        return False
    except GenerationStopped:
        print("✅ SUCCESS: Generation stopped correctly")
        return True
    except PPTGenerationError as e:
        if "stopped" in str(e).lower():
            print("✅ SUCCESS: Generation stopped correctly")
            return True
        else:
            print(f"❌ FAILED: Unexpected error: {e}")
            return False
    except Exception as e:
        if "stopped" in str(e).lower():
            print("✅ SUCCESS: Generation stopped correctly")
            return True
        print(f"❌ FAILED: Unexpected error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 PPT Generator Test Suite")
    print("=" * 50)
    
    test1_passed = test_successful_generation()
    test2_passed = test_stop_functionality()
    
    print("\n📊 Test Results:")
    print("=" * 50)
    print(f"✅ Successful Generation: {'PASS' if test1_passed else 'FAIL'}")
    print(f"⏹️ Stop Functionality: {'PASS' if test2_passed else 'FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! Your PPT generator is working perfectly!")
        print("🚀 Ready for production use!")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")
    
    return test1_passed and test2_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)