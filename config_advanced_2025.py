#!/usr/bin/env python3
"""
Advanced UPI Gateway Configuration for 2025
Comprehensive setup for bypassing PhonePe's latest anti-bot measures
"""

import os

# ================================
# CAPTCHA Solving Services
# ================================
# Get API keys from:
# - CapSolver: https://capsolver.com/
# - SolveCaptcha: https://solvecaptcha.com/
# - 2Captcha: https://2captcha.com/

CAPTCHA_SERVICES = {
    'CAPSOLVER_API_KEY': 'your_capsolver_api_key_here',
    'SOLVECAPTCHA_API_KEY': 'your_solvecaptcha_api_key_here', 
    'TWOCAPTCHA_API_KEY': 'your_2captcha_api_key_here'
}

# Preferred service order (first available will be used)
CAPTCHA_SERVICE_PRIORITY = ['capsolver', 'solvecaptcha', '2captcha']

# ================================
# Residential Proxy Configuration
# ================================
# For best results, use residential or mobile proxies
# Recommended providers (based on 2025 research):
# - Bright Data, Oxylabs, Smartproxy, Proxy-Seller

PROXY_POOLS = {
    # Residential proxies (best for hCaptcha bypass)
    'residential': [
        # Format: 'http://username:password@ip:port'
        # Example: 'http://user123:pass456@192.168.1.100:8080'
    ],
    
    # Mobile proxies (excellent for rate limit bypass)
    'mobile': [
        # Format: 'http://username:password@mobile_ip:port'
    ],
    
    # Datacenter proxies (backup option)
    'datacenter': [
        # Format: 'http://username:password@datacenter_ip:port'
    ]
}

# ================================
# Advanced Browser Configuration
# ================================
BROWSER_CONFIG = {
    # Use headless mode (recommended for servers)
    'headless': True,
    
    # Browser stealth settings
    'stealth_mode': True,
    'disable_webdriver_detection': True,
    'randomize_fingerprints': True,
    
    # Performance settings
    'disable_images': True,  # Faster loading
    'disable_css': False,    # Keep CSS for proper rendering
    'page_load_timeout': 30,
    'script_timeout': 30,
    
    # User agent rotation
    'rotate_user_agents': True,
    'custom_user_agents': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
}

# ================================
# Rate Limiting Configuration
# ================================
RATE_LIMITING = {
    # Delays between requests (seconds)
    'min_delay': 2.0,
    'max_delay': 8.0,
    
    # Retry settings
    'max_retries': 3,
    'retry_backoff_factor': 2,
    
    # Rate limit handling
    'respect_retry_after': True,
    'max_wait_time': 300,  # 5 minutes max
    
    # Proxy rotation on rate limits
    'rotate_proxy_on_429': True
}

# ================================
# PhonePe Specific Settings
# ================================
PHONEPE_SETTINGS = {
    # Automation behavior
    'human_like_delays': True,
    'random_mouse_movements': True,
    'realistic_typing_speed': True,
    
    # OTP handling
    'otp_wait_timeout': 240,  # 4 minutes
    'auto_detect_otp_field': True,
    
    # Session management
    'session_persistence': True,
    'cookie_management': True,
    
    # Error handling
    'auto_retry_on_captcha': True,
    'fallback_to_manual_otp': True
}

# ================================
# Security and Compliance
# ================================
SECURITY_SETTINGS = {
    # Request limits
    'max_daily_requests': 1000,
    'max_hourly_requests': 100,
    
    # Logging
    'log_level': 'INFO',
    'save_screenshots_on_error': True,
    'log_requests': False,  # Set to True for debugging
    
    # Data handling
    'encrypt_stored_tokens': True,
    'auto_cleanup_old_sessions': True,
    'respect_robots_txt': True
}

# ================================
# Environment Variables Setup
# ================================
def setup_environment():
    """Set up environment variables for the application"""
    
    # Set CAPTCHA service API keys
    for service, api_key in CAPTCHA_SERVICES.items():
        if api_key and api_key != f'your_{service.lower()}_here':
            os.environ[service] = api_key
    
    # Set other configuration
    os.environ['PHONEPE_LOG_LEVEL'] = SECURITY_SETTINGS['log_level']
    os.environ['PHONEPE_MAX_RETRIES'] = str(RATE_LIMITING['max_retries'])
    
    print("✅ Environment configured successfully")

# ================================
# Example Usage
# ================================
def get_example_usage():
    """Return example usage code"""
    return """
# Example: Setting up the advanced UPI Gateway

from app import BrowserAutomation, ProxyManager, PhonePeAPIClient
import config_advanced_2025 as config

# Setup environment
config.setup_environment()

# Initialize proxy manager
proxy_manager = ProxyManager()
if config.PROXY_POOLS['residential']:
    proxy_manager.add_proxy_pool('residential', config.PROXY_POOLS['residential'])

# Initialize PhonePe client with proxy support
phonepe_client = PhonePeAPIClient(proxy_manager=proxy_manager)

# Initialize browser automation with CAPTCHA solving
browser_automation = BrowserAutomation()

# Start automation
result = browser_automation.phonepe_automated_login(
    phone_number="your_phone_number",
    headless=config.BROWSER_CONFIG['headless']
)

if result['success']:
    print("🎉 Login successful!")
    print(f"Session ID: {result['session_id']}")
else:
    print(f"❌ Login failed: {result['error']}")
"""

# ================================
# Validation
# ================================
def validate_config():
    """Validate the configuration"""
    issues = []
    
    # Check if at least one CAPTCHA service is configured
    captcha_configured = any(
        key != f'your_{service.lower()}_here' 
        for service, key in CAPTCHA_SERVICES.items()
    )
    if not captcha_configured:
        issues.append("⚠️  No CAPTCHA services configured - hCaptcha bypass will fail")
    
    # Check proxy configuration
    total_proxies = sum(len(proxies) for proxies in PROXY_POOLS.values())
    if total_proxies == 0:
        issues.append("⚠️  No proxies configured - may get rate limited or IP blocked")
    
    # Check rate limiting settings
    if RATE_LIMITING['max_retries'] > 5:
        issues.append("⚠️  Too many retries configured - may trigger additional blocks")
    
    if issues:
        print("Configuration Issues Found:")
        for issue in issues:
            print(issue)
        return False
    else:
        print("✅ Configuration validation passed")
        return True

if __name__ == "__main__":
    print("🔧 Advanced UPI Gateway Configuration (2025)")
    print("=" * 50)
    
    # Validate configuration
    if validate_config():
        setup_environment()
        print("\n" + get_example_usage())
    else:
        print("\n❌ Please fix configuration issues before proceeding")