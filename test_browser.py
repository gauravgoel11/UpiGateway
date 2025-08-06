#!/usr/bin/env python3
"""
Simple test script to verify browser automation setup
"""

def test_selenium_basic():
    """Test basic selenium functionality"""
    try:
        print("Testing Selenium import...")
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        print("✓ Selenium imports successful")
        
        print("\nTesting ChromeDriver installation...")
        try:
            driver_path = ChromeDriverManager().install()
            print(f"✓ ChromeDriver installed at: {driver_path}")
        except Exception as e:
            print(f"❌ ChromeDriver installation failed: {e}")
            print("Trying to clear cache and reinstall...")
            import shutil
            import os
            cache_dir = os.path.expanduser("~/.wdm")
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)
                print("✓ Cleared ChromeDriver cache")
            
            driver_path = ChromeDriverManager().install()
            print(f"✓ ChromeDriver installed successfully after cache clear: {driver_path}")
        
        print("\nTesting Chrome options...")
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        print("✓ Chrome options configured")
        
        print("\nTesting Chrome browser startup...")
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✓ Chrome browser started successfully")
        
        print("\nTesting navigation...")
        driver.get("https://httpbin.org/get")
        title = driver.title
        print(f"✓ Navigation successful, page title: {title}")
        
        print("\nCleaning up...")
        driver.quit()
        print("✓ Browser closed successfully")
        
        print("\n🎉 ALL TESTS PASSED! Browser automation is working.")
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Solution: Run 'pip install selenium webdriver-manager'")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Check the error message above for specific issues.")
        return False

if __name__ == "__main__":
    print("🔧 Browser Automation Test")
    print("=" * 40)
    success = test_selenium_basic()
    if success:
        print("\n✅ Your system is ready for browser automation!")
    else:
        print("\n❌ Setup needs attention. Please check the errors above.")