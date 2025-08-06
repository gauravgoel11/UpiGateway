#!/usr/bin/env python3
"""
Manual ChromeDriver fix for Windows
"""
import os
import shutil
import requests
import zipfile
import tempfile
from pathlib import Path

def download_chromedriver_manually():
    """Download and install ChromeDriver manually"""
    print("🔧 Manual ChromeDriver Installation")
    print("=" * 40)
    
    # Chrome version detection
    try:
        import winreg
        # Try to get Chrome version from registry
        chrome_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        version, _ = winreg.QueryValueEx(chrome_key, "version")
        major_version = version.split('.')[0]
        print(f"✓ Detected Chrome version: {version}")
        winreg.CloseKey(chrome_key)
    except:
        print("⚠️  Could not detect Chrome version, using latest")
        major_version = "latest"
    
    # Download URL for ChromeDriver
    if major_version == "latest":
        download_url = "https://chromedriver.storage.googleapis.com/LATEST_RELEASE"
        try:
            response = requests.get(download_url)
            version = response.text.strip()
            print(f"✓ Latest ChromeDriver version: {version}")
        except:
            version = "119.0.6045.105"  # Fallback version
            print(f"⚠️  Using fallback version: {version}")
    else:
        version = f"{major_version}.0.0.0"  # Simplified versioning
        print(f"✓ Using ChromeDriver version: {version}")
    
    # Download ChromeDriver
    chromedriver_url = f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_win32.zip"
    
    try:
        print("📥 Downloading ChromeDriver...")
        response = requests.get(chromedriver_url)
        response.raise_for_status()
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "chromedriver.zip")
            
            # Save zip file
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            # Extract zip
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find chromedriver.exe
            chromedriver_exe = os.path.join(temp_dir, "chromedriver.exe")
            if not os.path.exists(chromedriver_exe):
                raise FileNotFoundError("chromedriver.exe not found in downloaded archive")
            
            # Create target directory
            target_dir = os.path.expanduser("~/.wdm/drivers/chromedriver/manual/")
            os.makedirs(target_dir, exist_ok=True)
            
            # Copy chromedriver.exe
            target_path = os.path.join(target_dir, "chromedriver.exe")
            shutil.copy2(chromedriver_exe, target_path)
            
            # Make executable (Windows doesn't need this, but just in case)
            os.chmod(target_path, 0o755)
            
            print(f"✅ ChromeDriver installed successfully at: {target_path}")
            return target_path
            
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

def test_manual_chromedriver():
    """Test the manually installed ChromeDriver"""
    chromedriver_path = download_chromedriver_manually()
    
    if not chromedriver_path:
        print("❌ Manual installation failed")
        return False
    
    try:
        print("\n🧪 Testing manual ChromeDriver...")
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # Fix WebGL warnings and enable software rendering
        chrome_options.add_argument("--disable-3d-apis")
        chrome_options.add_argument("--disable-webgl")
        chrome_options.add_argument("--disable-webgl2")
        chrome_options.add_argument("--use-gl=swiftshader")
        chrome_options.add_argument("--enable-unsafe-swiftshader")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        
        # Create service with manual path
        service = Service(chromedriver_path)
        
        # Start browser
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Test navigation
        driver.get("https://httpbin.org/get")
        title = driver.title
        print(f"✅ Browser test successful! Page title: {title}")
        
        # Close browser
        driver.quit()
        
        print(f"\n🎉 SUCCESS! Use this path in your app:")
        print(f"   {chromedriver_path}")
        
        return chromedriver_path
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    result = test_manual_chromedriver()
    if result:
        print(f"\n✅ ChromeDriver is ready! Path: {result}")
    else:
        print("\n❌ Manual setup failed. You may need to:")
        print("   1. Install Google Chrome")
        print("   2. Check your internet connection")
        print("   3. Run as administrator")