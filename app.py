from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
from datetime import datetime, timedelta
import random
import uuid
import re
import requests
import json
from urllib.parse import urlencode, urlparse
import threading
import time
import os

# Selenium imports for browser automation
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.firefox import GeckoDriverManager
    SELENIUM_AVAILABLE = True
    print("✅ Selenium browser automation available")
except ImportError as e:
    SELENIUM_AVAILABLE = False
    print(f"❌ Selenium not available: {e}")
    print("Install with: pip install selenium webdriver-manager")




app = Flask(__name__)
app.secret_key = 'supersecretkey123456789'  # Replace with a real secret key in production

# Custom Jinja2 filters
@app.template_filter('from_json')
def from_json_filter(value):
    """Parse JSON string to Python object"""
    try:
        return json.loads(value or '{}')
    except (json.JSONDecodeError, TypeError):
        return {}

DATABASE = 'transactions.db'

# PhonePe Business API Configuration (Updated from captured API data)
PHONEPE_CONFIG = {
    'base_url': 'https://web-api.phonepe.com',
    'business_url': 'https://business.phonepe.com',
    'login_initiate_endpoint': '/apis/mi-web/v2/auth/web/login/initiate',
    'login_verify_endpoint': '/apis/mi-web/v4/auth/web/login',
    'group_selection_endpoint': '/apis/mi-web/v1/user/groupSelection',
    'update_session_endpoint': '/apis/mi-web/v1/user/updateSession',
    'user_profile_endpoint': '/apis/mi-web/v1/user/me',
    'user_permissions_endpoint': '/apis/mi-web/v1/user/permissions',
    'merchant_profile_endpoint': '/apis/mo-web/v1/merchant/profile',
    'transaction_stats_endpoint': '/apis/mi-web/v3/transactions/metrics/stats',
}

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS phonepe_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            user_id TEXT,
            access_token TEXT,
            refresh_token TEXT,
            csrf_token TEXT,
            merchant_groups TEXT,
            selected_merchant TEXT,
            session_data TEXT,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )'''
    )
    
    # New table for captured authentication data
    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS captured_auth_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            site_domain TEXT,
            site_name TEXT,
            auth_tokens TEXT,
            cookies TEXT,
            session_storage TEXT,
            local_storage TEXT,
            api_endpoints TEXT,
            headers TEXT,
            login_credentials TEXT,
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )'''
    )
    
    # Table for browser sessions
    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS browser_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            browser_pid INTEGER,
            status TEXT DEFAULT 'active',
            current_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )'''
    )
    
    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS cached_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_id TEXT,
            transaction_data TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )'''
    )
    conn.commit()
    conn.close()

# Initialize database when app starts
with app.app_context():
    init_db()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

class PhonePeAPIClient:
    def __init__(self):
        self.session = requests.Session()
        # Generate more realistic fingerprints based on captured data
        self.device_fingerprint = f"fp_{int(time.time() * 1000)}_{''.join([str(random.randint(0, 9)) for _ in range(8)])}"
        self.browser_fingerprint = f"pbweb_{uuid.uuid4().hex[:32]}_g1YWx"
        
        # Add more realistic browser characteristics
        self.screen_resolution = "1920x1080"
        self.timezone = "Asia/Kolkata"
        self.language = "en-US,en;q=0.9"
        
        # Base headers from captured API data
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Origin': 'https://business.phonepe.com',
            'Referer': 'https://business.phonepe.com/',
            'Sec-Ch-Ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Priority': 'u=1, i',
            'X-App-Id': 'oculus',
            'X-Source-Platform': 'WEB',
            'X-Source-Type': 'WEB',
            'X-Device-Fingerprint': self.device_fingerprint,
            'Fingerprint': self.browser_fingerprint,
            'Namespace': 'insights'
        })
        
        # Initialize session with basic cookies that PhonePe expects
        self._initialize_session()
        
        # Simulate browser behavior to avoid detection
        self._simulate_browser_behavior()
    
    def _initialize_session(self):
        """Initialize session with basic cookies and setup"""
        # Generate session ID and other identifiers based on captured data
        session_id = str(uuid.uuid4())
        timestamp = str(int(time.time() * 1000))
        
        # Set basic cookies that PhonePe expects (based on captured data)
        cookies = {
            '_ppabwduref': f'PAUREF{timestamp}',
            '_ppabwdsid': session_id,
            '_ppabwdcid': 'ZXlKaGJHY2lPaUpJVXpVeE1pSjkuZXlKcGMzTWlPaUpRYUc5dVpWQmxSMkZ5Wm1sbGJHUWlMQ0pxZEdraU9pSTJNREJsWWpjMVl5MDVZalV4TFRReU4yUXRPR1U1TlMxa01ETXpNekF5Tnprek5EUWlMQ0pwWVhRaU9qRTJOekUyTURReU5ERXNJbTVpWmlJNk1UWTNNVFl3TkRFeU1Td2ljM1ZpSWpvaVFsVlRTVTVGVTFOZlYwVkNYMFJCVTBoQ1QwRlNSQ0lzSW5KdmJHVWlPaUpwYm1kbGMzUWlmUS5rdkcxQUJCNGJpcnVQSllRektFa1NYME9sUlBINVFDNW9tX2k5Mm9CNG9mV25vV0c4eFp3cTMwT1cxdEVCX3J5Zm4wTzhFVUd2MnE5VGlrMUxJaUw4Zw=='
        }
        
        for name, value in cookies.items():
            self.session.cookies.set(name, value, domain='.phonepe.com')
        
        # Add PhonePe CSRF cookie (from captured data)
        csrf_value = f'9o7C5C3YtQO4/fRXQHeVhkuxqeRKFrst9mBN5IySQD1hT3y5kDX0QnVqI2TCkAaD_{timestamp}'
        self.session.cookies.set('_CKB2N1BHVZ', csrf_value, domain='.phonepe.com')
        
        print(f"Initialized PhonePe session with cookies: {list(cookies.keys())} + CSRF cookie")
        
        # Get initial CSRF token (check if we already have one from cookies)
        self.csrf_token = self._get_csrf_token() or csrf_value
        print(f"Final CSRF token set: {self.csrf_token[:30]}... (length: {len(self.csrf_token) if self.csrf_token else 0})")
    
    def _simulate_browser_behavior(self):
        """Simulate realistic browser behavior to avoid bot detection"""
        try:
            print("Simulating browser behavior...")
            
            # Step 1: Visit main website first (like a real user)
            main_url = 'https://www.phonepe.com'
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': self.language,
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Ch-Ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Add random delay like a real user
            time.sleep(random.uniform(1.0, 3.0))
            
            response = self.session.get(main_url, headers=headers, timeout=30)
            print(f"Main site visit: {response.status_code}")
            
            # Step 2: Random delay before visiting business site
            time.sleep(random.uniform(2.0, 5.0))
            
            # Step 3: Visit business login page (like clicking a link)
            business_url = 'https://business.phonepe.com'
            headers['Referer'] = main_url
            headers['Sec-Fetch-Site'] = 'same-site'
            
            response = self.session.get(business_url, headers=headers, timeout=30)
            print(f"Business site visit: {response.status_code}")
            
            # Step 4: Small delay before login page
            time.sleep(random.uniform(1.0, 2.0))
            
            print("Browser simulation completed")
            
        except Exception as e:
            print(f"Browser simulation warning: {e} (continuing anyway...)")
    
    def _get_csrf_token(self, force_refresh=False):
        """Get CSRF token from PhonePe before making API calls"""
        try:
            # First, visit the business login page to get initial tokens
            login_page_url = 'https://business.phonepe.com/login'
            
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Ch-Ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
            
            print("Getting CSRF token from PhonePe login page...")
            response = self.session.get(login_page_url, headers=headers, timeout=30)
            print(f"Login page response: {response.status_code}")
            print(f"Response cookies: {[f'{c.name}={c.value[:20]}...' for c in response.cookies]}")
            
            # Check for PhonePe's specific CSRF cookie first (_CKB2N1BHVZ)
            for cookie in self.session.cookies:
                if cookie.name == '_CKB2N1BHVZ':
                    print(f"Found PhonePe CSRF cookie: {cookie.name} = {cookie.value[:20]}...")
                    return cookie.value
            
            # Check for CSRF token in response headers
            csrf_token = response.headers.get('x-csrf-token')
            if csrf_token:
                print(f"Found CSRF token in headers: {csrf_token[:20]}...")
                return csrf_token
            
            # Check for other potential CSRF tokens in cookies
            for cookie in self.session.cookies:
                if 'csrf' in cookie.name.lower() or 'token' in cookie.name.lower():
                    print(f"Found potential CSRF cookie: {cookie.name} = {cookie.value[:20]}...")
                    return cookie.value
            
            # Try to extract CSRF token from HTML content
            html_content = response.text
            csrf_patterns = [
                r'name="csrf[_-]?token"\s+value="([^"]+)"',
                r'"csrf[_-]?token"\s*:\s*"([^"]+)"',
                r'csrfToken["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'_token["\']?\s*[:=]\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in csrf_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    token = match.group(1)
                    print(f"Found CSRF token in HTML: {token[:20]}...")
                    return token
            
            print("No CSRF token found - PhonePe might set it later or through different method")
            return None
            
        except Exception as e:
            print(f"Error getting CSRF token: {e}")
            return None

    def initiate_login(self, phone):
        """Step 1: Initiate login with phone number (Send OTP)"""
        print(f"Starting login process for phone: {phone}")
        
        # Add realistic delay like a user typing and clicking
        time.sleep(random.uniform(0.5, 1.5))
        
        url = f"{PHONEPE_CONFIG['base_url']}{PHONEPE_CONFIG['login_initiate_endpoint']}"
        
        # Enhanced payload with more realistic data
        payload = {
            "type": "OTP_V2",
            "endpoint": phone,
            "channelType": "SMS",
            "deviceFingerprint": self.device_fingerprint,
            "browserFingerprint": self.browser_fingerprint,
            "screenResolution": self.screen_resolution,
            "timezone": self.timezone
        }
        
        # Generate a more realistic h-captcha token (PhonePe might require this)
        current_time = int(time.time() * 1000)
        h_captcha_token = f"P1_{current_time}_{''.join([str(random.randint(0, 9)) for _ in range(50)])}_verify"
        
        # Enhanced headers based on captured API data with anti-bot improvements
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': self.language,
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Origin': 'https://business.phonepe.com',
            'Referer': 'https://business.phonepe.com/login',
            'Sec-Ch-Ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Priority': 'u=1, i',
            'X-App-Id': 'oculus',
            'X-Source-Platform': 'WEB',
            'X-Source-Type': 'WEB',
            'X-Device-Fingerprint': self.device_fingerprint,
            'Fingerprint': self.browser_fingerprint,
            'Namespace': 'insights',
            'H-Captcha-Token': h_captcha_token,
            # Additional anti-bot headers
            'X-Requested-With': 'XMLHttpRequest',
            'DNT': '1',
            'Sec-GPC': '1',
            # Timing headers to simulate real user behavior
            'X-Client-Time': str(current_time),
            'X-Request-ID': str(uuid.uuid4()),
        }
        
        # Add CSRF token if available
        if hasattr(self, 'csrf_token') and self.csrf_token:
            headers['X-CSRF-Token'] = self.csrf_token
            headers['csrf-token'] = self.csrf_token
            print(f"Added CSRF token to headers: {self.csrf_token[:20]}...")
        else:
            print("No CSRF token available - proceeding without one")
        
        try:
            print(f"Attempting to call PhonePe API: {url}")
            print(f"Payload: {payload}")
            print(f"Headers: {dict(headers)}")
            
            response = self.session.post(url, json=payload, headers=headers, timeout=30)
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Response data: {data}")
                return {
                    'success': True,
                    'data': data,
                    'cookies': dict(response.cookies),
                    'csrf_token': response.headers.get('x-csrf-token'),
                    'token': data.get('token')  # Token needed for OTP verification
                }
            else:
                print(f"API Error: Status {response.status_code}, Response: {response.text}")
                
                # Check if it's a CSRF error and try to refresh token
                if response.status_code == 401 and 'csrf' in response.text.lower():
                    print("CSRF error detected, attempting to refresh CSRF token...")
                    self.csrf_token = self._get_csrf_token(force_refresh=True)
                    if self.csrf_token:
                        print("CSRF token refreshed, please try the request again")
                        return {
                            'success': False,
                            'error': 'CSRF token was invalid. A new token has been obtained. Please try again.',
                            'retry_suggested': True,
                            'status_code': response.status_code,
                            'response_text': response.text
                        }
                
                return {
                    'success': False, 
                    'error': f'PhonePe API returned {response.status_code}: {response.text}',
                    'status_code': response.status_code,
                    'response_text': response.text
                }
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            return {'success': False, 'error': f'Network error: {str(e)}'}
        except Exception as e:
            print(f"Unexpected error: {e}")
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}

    def verify_otp(self, phone, otp, token):
        """Step 2: Verify OTP and complete login"""
        url = f"{PHONEPE_CONFIG['base_url']}{PHONEPE_CONFIG['login_verify_endpoint']}"
        
        payload = {
            "loginRequest": {
                "type": "OTP_V2",
                "deviceFingerprint": self.device_fingerprint,
                "endpoint": phone,
                "otp": otp,
                "channelType": "SMS",
                "token": token
            },
            "deviceInfo": {
                "browserFingerPrint": {
                    "xosv": "Chrome 138",
                    "omid": "Web Browser",
                    "xdpi": self.browser_fingerprint
                },
                "browserFingerPrintOmid": "Web Browser",
                "browserFingerPrintXdpi": self.browser_fingerprint,
                "browserFingerPrintXosv": "Chrome 138",
                "channelType": "WEB",
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
            }
        }
        
        # Headers for OTP verification
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Origin': 'https://business.phonepe.com',
            'Referer': 'https://business.phonepe.com/',
            'Sec-Ch-Ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Priority': 'u=1, i',
            'X-App-Id': 'oculus',
            'X-Source-Platform': 'WEB',
            'X-Source-Type': 'WEB',
            'X-Device-Fingerprint': self.device_fingerprint,
            'Fingerprint': self.browser_fingerprint,
            'Namespace': 'insights',
        }
        
        # Add CSRF token if available
        if hasattr(self, 'csrf_token') and self.csrf_token:
            headers['X-CSRF-Token'] = self.csrf_token
            headers['csrf-token'] = self.csrf_token
            print(f"Added CSRF token to OTP headers: {self.csrf_token[:20]}...")
        else:
            print("No CSRF token available for OTP verification")
        
        try:
            print(f"Attempting OTP verification: {url}")
            print(f"Payload: {payload}")
            
            response = self.session.post(url, json=payload, headers=headers, timeout=30)
            print(f"OTP Response status: {response.status_code}")
            print(f"OTP Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"OTP Success! Response data: {data}")
                return {
                    'success': True,
                    'data': data,
                    'cookies': dict(response.cookies),
                    'access_token': response.cookies.get('MERCHANT_USER_A_TOKEN'),
                    'refresh_token': response.cookies.get('MERCHANT_USER_R_TOKEN'),
                    'csrf_token': response.headers.get('x-csrf-token')
                }
            else:
                print(f"OTP Error: Status {response.status_code}, Response: {response.text}")
                return {
                    'success': False, 
                    'error': f'OTP verification failed: {response.status_code} - {response.text}',
                    'status_code': response.status_code,
                    'response_text': response.text
                }
        except requests.exceptions.RequestException as e:
            print(f"OTP Network error: {e}")
            return {'success': False, 'error': f'Network error during OTP verification: {str(e)}'}
        except Exception as e:
            print(f"OTP Unexpected error: {e}")
            return {'success': False, 'error': f'Unexpected error during OTP verification: {str(e)}'}

    def get_merchant_groups(self, access_token, csrf_token):
        """Step 3: Get available merchant groups"""
        url = f"{PHONEPE_CONFIG['base_url']}{PHONEPE_CONFIG['group_selection_endpoint']}"
        
        # Update session cookies
        self.session.cookies.set('MERCHANT_USER_A_TOKEN', access_token)
        
        headers = {
            'X-Csrf-Token': csrf_token,
        }
        
        try:
            response = self.session.get(url, headers=headers)
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            else:
                return {'success': False, 'error': f'Failed to get merchant groups: {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def select_merchant(self, group_id, access_token, csrf_token):
        """Step 4: Select a merchant and update session"""
        url = f"{PHONEPE_CONFIG['base_url']}{PHONEPE_CONFIG['update_session_endpoint']}"
        
        payload = {"groupId": group_id}
        
        # Update session cookies
        self.session.cookies.set('MERCHANT_USER_A_TOKEN', access_token)
        
        headers = {
            'Content-Type': 'application/json',
            'X-Csrf-Token': csrf_token,
        }
        
        try:
            response = self.session.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'new_access_token': response.cookies.get('MERCHANT_USER_A_TOKEN'),
                    'new_csrf_token': response.headers.get('x-csrf-token')
                }
            else:
                return {'success': False, 'error': f'Failed to select merchant: {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_user_profile(self, access_token, csrf_token):
        """Get user profile information"""
        url = f"{PHONEPE_CONFIG['base_url']}{PHONEPE_CONFIG['user_profile_endpoint']}"
        
        self.session.cookies.set('MERCHANT_USER_A_TOKEN', access_token)
        
        headers = {
            'X-Csrf-Token': csrf_token,
        }
        
        try:
            response = self.session.get(url, headers=headers)
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            else:
                return {'success': False, 'error': f'Failed to get user profile: {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_user_permissions(self, access_token, csrf_token):
        """Get user permissions"""
        url = f"{PHONEPE_CONFIG['base_url']}{PHONEPE_CONFIG['user_permissions_endpoint']}"
        
        self.session.cookies.set('MERCHANT_USER_A_TOKEN', access_token)
        
        headers = {
            'X-Csrf-Token': csrf_token,
        }
        
        try:
            response = self.session.get(url, headers=headers)
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            else:
                return {'success': False, 'error': f'Failed to get user permissions: {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_merchant_profile(self, access_token, csrf_token):
        """Get merchant profile information"""
        url = f"{PHONEPE_CONFIG['base_url']}{PHONEPE_CONFIG['merchant_profile_endpoint']}"
        
        self.session.cookies.set('MERCHANT_USER_A_TOKEN', access_token)
        
        headers = {
            'X-Csrf-Token': csrf_token,
        }
        
        try:
            response = self.session.get(url, headers=headers)
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            else:
                return {'success': False, 'error': f'Failed to get merchant profile: {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_transaction_stats(self, access_token, csrf_token, date_range_payload=None):
        """Get transaction statistics"""
        url = f"{PHONEPE_CONFIG['base_url']}{PHONEPE_CONFIG['transaction_stats_endpoint']}"
        
        self.session.cookies.set('MERCHANT_USER_A_TOKEN', access_token)
        
        # Default payload for last 7 days if not provided
        if not date_range_payload:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            date_range_payload = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "granularity": "DAY"
            }
        
        headers = {
            'Content-Type': 'application/json',
            'X-Csrf-Token': csrf_token,
        }
        
        try:
            response = self.session.post(url, json=date_range_payload, headers=headers)
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            else:
                return {'success': False, 'error': f'Failed to get transaction stats: {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

class BrowserAutomation:
    def __init__(self):
        self.active_sessions = {}
        self.captured_data = []

    def create_browser_session(self, session_id):
        """Create a new browser session with Firefox (primary) or Chrome (fallback)"""
        try:
            print(f"Creating browser session: {session_id}")
            
            # Try Firefox first (better Windows compatibility)
            try:
                return self._create_firefox_session(session_id)
            except Exception as firefox_error:
                print(f"Firefox failed: {firefox_error}")
                print("Trying Chrome as fallback...")
                return self._create_chrome_session(session_id)
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _create_firefox_session(self, session_id):
        """Create Firefox browser session"""
        print("Starting Firefox browser...")
        
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--headless")
        firefox_options.add_argument("--width=1200")
        firefox_options.add_argument("--height=800")
        firefox_options.add_argument("--disable-gpu")
        
        # Install GeckoDriver automatically
        try:
            service = FirefoxService(GeckoDriverManager().install())
            print("GeckoDriver installed successfully")
        except Exception as e:
            print(f"GeckoDriver installation failed: {e}")
            raise e
        
        # Create Firefox driver
        driver = webdriver.Firefox(service=service, options=firefox_options)
        print("Firefox browser started successfully")
        
        return self._finalize_session_creation(session_id, driver, "firefox")

    def _create_chrome_session(self, session_id):
        """Create Chrome browser session (fallback)"""
        print("Starting Chrome browser...")
        
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1200,800")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Faster loading
        chrome_options.add_argument("--headless=new")  # Run in headless mode for better compatibility
        
        # Enable logging for network capture
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--log-level=0")
        chrome_options.add_argument("--v=1")
        
        # Performance logging to capture network events
        chrome_options.add_experimental_option('perfLoggingPrefs', {
            'enableNetwork': True,
            'enablePage': False,
            'enableTimeline': False
        })
        
        # Enable CDP (Chrome DevTools Protocol) for better network capture
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Install ChromeDriver
        try:
            service = ChromeService(ChromeDriverManager().install())
            print("ChromeDriver installed successfully")
        except Exception as e:
            print(f"ChromeDriver installation failed: {e}")
            raise e
        
        # Create Chrome driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Chrome browser started successfully")
        
        return self._finalize_session_creation(session_id, driver, "chrome")

    def _finalize_session_creation(self, session_id, driver, browser_type):
        """Finalize the browser session creation"""
        # Store session info
        self.active_sessions[session_id] = {
            'driver': driver,
            'session_id': session_id,
            'browser_type': browser_type,
            'created_at': datetime.now(),
            'current_url': 'about:blank',
            'captured_data': [],
            'monitoring_thread': None
        }
        
        # Start monitoring thread for this session
        monitoring_thread = threading.Thread(
            target=self._monitor_browser_session,
            args=(session_id,),
            daemon=True
        )
        monitoring_thread.start()
        self.active_sessions[session_id]['monitoring_thread'] = monitoring_thread
        
        # Store in database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO browser_sessions 
            (session_id, browser_pid, status, current_url)
            VALUES (?, ?, ?, ?)
        ''', (session_id, os.getpid(), 'active', 'about:blank'))
        conn.commit()
        conn.close()
        
        print(f"✅ {browser_type.title()} browser session created: {session_id}")
        return {'success': True, 'session_id': session_id, 'browser_type': browser_type}

    def _monitor_browser_session(self, session_id):
        """Monitor browser session for network traffic and authentication data"""
        session_info = self.active_sessions.get(session_id)
        if not session_info:
            return
            
        driver = session_info['driver']
        last_url = 'about:blank'
        
        while session_id in self.active_sessions:
            try:
                current_url = driver.current_url
                if current_url != last_url:
                    last_url = current_url
                    session_info['current_url'] = current_url
                    
                    # Update database
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute('''
                        UPDATE browser_sessions 
                        SET current_url = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE session_id = ?
                    ''', (current_url, session_id))
                    conn.commit()
                    conn.close()
                
                # Capture authentication data when on login/auth pages
                if self._is_auth_page(current_url):
                    auth_data = self._capture_auth_data(driver, current_url)
                    if auth_data:
                        session_info['captured_data'].append(auth_data)
                        self._store_captured_data(session_id, auth_data)
                
                # Capture network logs
                self._capture_network_logs(driver, session_id)
                
                time.sleep(2)  # Check every 2 seconds
                
            except WebDriverException:
                # Browser might be closed
                break
            except Exception as e:
                print(f"Error monitoring session {session_id}: {e}")
                time.sleep(5)

    def _is_auth_page(self, url):
        """Check if current page is likely an authentication page"""
        auth_indicators = [
            'login', 'signin', 'auth', 'oauth', 'sso', 'account',
            'password', 'register', 'signup', 'authentication'
        ]
        return any(indicator in url.lower() for indicator in auth_indicators)

    def _capture_auth_data(self, driver, url):
        """Capture authentication data from current page"""
        try:
            domain = urlparse(url).netloc
            site_name = domain.split('.')[0] if '.' in domain else domain
            
            # Get cookies
            cookies = driver.get_cookies()
            
            # Get local storage
            local_storage = driver.execute_script("return JSON.stringify(localStorage);")
            
            # Get session storage
            session_storage = driver.execute_script("return JSON.stringify(sessionStorage);")
            
            # Look for auth tokens in page
            auth_tokens = self._extract_auth_tokens(driver)
            
            # Get current page title for site name
            try:
                page_title = driver.title
                if page_title:
                    site_name = page_title.split(' - ')[0] if ' - ' in page_title else page_title[:50]
            except:
                pass
            
            return {
                'domain': domain,
                'site_name': site_name,
                'url': url,
                'cookies': json.dumps(cookies),
                'local_storage': local_storage,
                'session_storage': session_storage,
                'auth_tokens': json.dumps(auth_tokens),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error capturing auth data: {e}")
            return None

    def _extract_auth_tokens(self, driver):
        """Extract potential authentication tokens from page"""
        tokens = {}
        
        try:
            # Look for tokens in JavaScript variables
            js_tokens = driver.execute_script("""
                var tokens = {};
                // Common token variable names
                var tokenNames = ['token', 'accessToken', 'authToken', 'jwt', 'bearerToken', 
                                'csrf', 'xsrf', 'sessionToken', 'apiKey', 'apiToken'];
                
                tokenNames.forEach(function(name) {
                    if (window[name]) tokens[name] = window[name];
                    if (window[name.toLowerCase()]) tokens[name.toLowerCase()] = window[name.toLowerCase()];
                    if (window[name.toUpperCase()]) tokens[name.toUpperCase()] = window[name.toUpperCase()];
                });
                
                return tokens;
            """)
            tokens.update(js_tokens)
            
            # Look for tokens in meta tags
            meta_tags = driver.find_elements(By.TAG_NAME, "meta")
            for meta in meta_tags:
                name = meta.get_attribute("name")
                content = meta.get_attribute("content")
                if name and content and any(keyword in name.lower() for keyword in ['csrf', 'token', 'auth']):
                    tokens[name] = content
            
        except Exception as e:
            print(f"Error extracting tokens: {e}")
        
        return tokens

    def _capture_network_logs(self, driver, session_id):
        """Capture network requests and responses"""
        try:
            logs = driver.get_log('performance')
            api_endpoints = []
            
            for log in logs:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    response = message['message']['params']['response']
                    url = response['url']
                    
                    # Filter for API endpoints
                    if any(keyword in url.lower() for keyword in ['api', 'auth', 'login', 'token', 'oauth']):
                        api_endpoints.append({
                            'url': url,
                            'method': response.get('method', 'GET'),
                            'status': response.get('status', 0),
                            'headers': response.get('headers', {}),
                            'timestamp': datetime.now().isoformat()
                        })
            
            if api_endpoints:
                # Store API endpoints
                session_info = self.active_sessions.get(session_id)
                if session_info:
                    if 'api_endpoints' not in session_info:
                        session_info['api_endpoints'] = []
                    session_info['api_endpoints'].extend(api_endpoints)
                    
        except Exception as e:
            print(f"Error capturing network logs: {e}")

    def _store_captured_data(self, session_id, auth_data):
        """Store captured authentication data in database"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO captured_auth_data 
                (session_id, site_domain, site_name, auth_tokens, cookies, 
                 session_storage, local_storage, api_endpoints, headers)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                auth_data['domain'],
                auth_data['site_name'],
                auth_data['auth_tokens'],
                auth_data['cookies'],
                auth_data['session_storage'],
                auth_data['local_storage'],
                json.dumps(self.active_sessions[session_id].get('api_endpoints', [])),
                json.dumps({})  # headers placeholder
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error storing captured data: {e}")

    def navigate_to_url(self, session_id, url):
        """Navigate browser to specified URL"""
        session_info = self.active_sessions.get(session_id)
        if not session_info:
            return {'success': False, 'error': 'Session not found'}
        
        try:
            driver = session_info['driver']
            driver.get(url)
            return {'success': True, 'current_url': driver.current_url}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_session_info(self, session_id):
        """Get current session information"""
        session_info = self.active_sessions.get(session_id)
        if not session_info:
            return {'success': False, 'error': 'Session not found'}
        
        try:
            driver = session_info['driver']
            return {
                'success': True,
                'session_id': session_id,
                'current_url': driver.current_url,
                'title': driver.title,
                'captured_data_count': len(session_info.get('captured_data', [])),
                'created_at': session_info['created_at'].isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def close_session(self, session_id):
        """Close browser session and cleanup"""
        session_info = self.active_sessions.get(session_id)
        if not session_info:
            return {'success': False, 'error': 'Session not found'}
        
        try:
            driver = session_info['driver']
            driver.quit()
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            # Update database
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''
                UPDATE browser_sessions 
                SET status = 'closed', updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (session_id,))
            conn.commit()
            conn.close()
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_captured_data(self, session_id=None):
        """Get captured authentication data"""
        conn = get_db_connection()
        c = conn.cursor()
        
        if session_id:
            c.execute('''
                SELECT * FROM captured_auth_data 
                WHERE session_id = ? 
                ORDER BY captured_at DESC
            ''', (session_id,))
        else:
            c.execute('''
                SELECT * FROM captured_auth_data 
                ORDER BY captured_at DESC
                LIMIT 50
            ''')
        
        data = [dict(row) for row in c.fetchall()]
        conn.close()
        
        return data

    def phonepe_automated_login(self, phone_number, otp_callback=None, headless=True):
        """
        Automate PhonePe Business login using real browser
        
        Args:
            phone_number: Phone number for login
            otp_callback: Function to call when OTP is needed (should return OTP)
            headless: Whether to run browser in headless mode
            
        Returns:
            dict: Login result with session data
        """
        if not SELENIUM_AVAILABLE:
            return {
                'success': False,
                'error': 'Selenium not available. Install with: pip install selenium webdriver-manager'
            }
        
        session_id = f"phonepe_auto_{uuid.uuid4().hex[:8]}"
        print(f"🤖 Starting PhonePe automated login for {phone_number}")
        
        try:
            # Create browser session
            browser_result = self._create_phonepe_browser_session(session_id, headless)
            if not browser_result['success']:
                return browser_result
                
            driver = self.active_sessions[session_id]['driver']
            wait = WebDriverWait(driver, 10)
            
            # Step 1: Navigate to PhonePe Business login
            print("📱 Navigating to PhonePe Business login...")
            driver.get('https://business.phonepe.com/login')
            time.sleep(2)
            
            # Step 2: Enter phone number
            print(f"📞 Entering phone number: {phone_number}")
            try:
                phone_input = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="tel"], input[placeholder*="phone"], input[placeholder*="mobile"]'))
                )
                phone_input.clear()
                phone_input.send_keys(phone_number)
                time.sleep(1)
                
                # Find and click send OTP button
                send_otp_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"], button:contains("Send"), button:contains("OTP")')
                send_otp_btn.click()
                print("✅ OTP request sent")
                time.sleep(3)
                
            except (TimeoutException, NoSuchElementException) as e:
                return {'success': False, 'error': f'Could not find phone input or send button: {str(e)}'}
            
            # Step 3: Handle OTP input
            print("🔐 Waiting for OTP...")
            try:
                otp_input = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"], input[placeholder*="OTP"], input[placeholder*="code"]'))
                )
                
                # Get OTP from user or callback
                otp = None
                if otp_callback:
                    otp = otp_callback()
                
                if not otp:
                    # If no callback provided, wait for manual input or prompt
                    print("⏰ Waiting for OTP to be entered manually or provide otp_callback function...")
                    # Wait for OTP to be filled (either manually or programmatically)
                    WebDriverWait(driver, 120).until(
                        lambda d: len(otp_input.get_attribute('value')) >= 4
                    )
                else:
                    # Enter OTP programmatically
                    otp_input.clear()
                    otp_input.send_keys(otp)
                    time.sleep(1)
                    
                    # Submit OTP
                    submit_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"], button:contains("Verify"), button:contains("Submit")')
                    submit_btn.click()
                
                print("✅ OTP submitted, waiting for login...")
                time.sleep(5)
                
            except TimeoutException:
                return {'success': False, 'error': 'OTP input timeout - could not find OTP field or submit button'}
            
            # Step 4: Check if login successful and extract session data
            print("🔍 Extracting session data...")
            session_data = self._extract_phonepe_session_data(driver)
            
            if session_data['success']:
                print("🎉 PhonePe automated login successful!")
                
                # Store session data in database
                self._store_phonepe_session_data(session_id, session_data)
                
                return {
                    'success': True,
                    'session_id': session_id,
                    'session_data': session_data,
                    'driver_available': True,
                    'message': 'PhonePe login completed successfully via browser automation'
                }
            else:
                return {'success': False, 'error': 'Login appears to have failed - could not extract session data'}
                
        except Exception as e:
            print(f"❌ PhonePe automation error: {e}")
            return {'success': False, 'error': f'Automation failed: {str(e)}'}
    
    def _create_phonepe_browser_session(self, session_id, headless=True):
        """Create optimized browser session for PhonePe"""
        try:
            print("🚀 Creating optimized PhonePe browser session...")
            
            # Chrome options optimized for PhonePe
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument("--headless=new")
            
            # Essential Chrome arguments for PhonePe compatibility
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1400,900")
            chrome_options.add_argument("--start-maximized")
            
            # Anti-detection measures
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Performance optimizations
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript-harmony-shipping")
            
            # User agent to mimic real browser
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
            
            # Network logging for session capture
            chrome_options.add_experimental_option('perfLoggingPrefs', {
                'enableNetwork': True,
                'enablePage': False,
                'enableTimeline': False
            })
            
            # Install and create driver
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Additional anti-detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ PhonePe browser session created successfully")
            
            # Store session
            self.active_sessions[session_id] = {
                'driver': driver,
                'session_id': session_id,
                'browser_type': 'chrome',
                'created_at': datetime.now(),
                'current_url': 'about:blank',
                'captured_data': [],
                'monitoring_thread': None,
                'purpose': 'phonepe_automation'
            }
            
            return {'success': True, 'session_id': session_id, 'driver': driver}
            
        except Exception as e:
            print(f"❌ Failed to create PhonePe browser session: {e}")
            return {'success': False, 'error': str(e)}
    
    def _extract_phonepe_session_data(self, driver):
        """Extract session data from authenticated PhonePe session"""
        try:
            print("🔍 Extracting PhonePe session data...")
            
            # Wait for dashboard to load
            time.sleep(3)
            
            # Check if we're logged in by looking for dashboard elements
            current_url = driver.current_url
            page_title = driver.title
            
            print(f"Current URL: {current_url}")
            print(f"Page title: {page_title}")
            
            # Extract cookies
            cookies = {}
            for cookie in driver.get_cookies():
                cookies[cookie['name']] = cookie['value']
            
            # Extract localStorage
            local_storage = {}
            try:
                local_storage = driver.execute_script("return window.localStorage;")
            except:
                print("Could not access localStorage")
            
            # Extract sessionStorage
            session_storage = {}
            try:
                session_storage = driver.execute_script("return window.sessionStorage;")
            except:
                print("Could not access sessionStorage")
            
            # Check for authentication tokens in cookies
            auth_indicators = ['token', 'auth', 'session', 'user', 'login', 'merchant']
            found_auth_data = False
            
            for key in cookies.keys():
                for indicator in auth_indicators:
                    if indicator.lower() in key.lower():
                        found_auth_data = True
                        break
                        
            # Look for dashboard/business indicators
            business_indicators = ['dashboard', 'business', 'merchant', 'transactions']
            is_business_page = any(indicator in current_url.lower() for indicator in business_indicators)
            
            success = found_auth_data or is_business_page or 'business.phonepe.com' in current_url
            
            session_data = {
                'success': success,
                'url': current_url,
                'title': page_title,
                'cookies': cookies,
                'localStorage': local_storage,
                'sessionStorage': session_storage,
                'timestamp': datetime.now().isoformat(),
                'authentication_detected': found_auth_data,
                'business_page_detected': is_business_page
            }
            
            if success:
                print("✅ Session data extracted successfully")
                print(f"Found {len(cookies)} cookies, {len(local_storage)} localStorage items")
            else:
                print("⚠️  Could not detect successful authentication")
            
            return session_data
            
        except Exception as e:
            print(f"❌ Error extracting session data: {e}")
            return {'success': False, 'error': str(e)}
    
    def _store_phonepe_session_data(self, session_id, session_data):
        """Store PhonePe session data in database"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # Store in captured_auth_data table
            c.execute('''
                INSERT INTO captured_auth_data 
                (session_id, site_domain, request_url, request_headers, response_headers, 
                 response_data, auth_type, captured_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                'business.phonepe.com',
                session_data.get('url', ''),
                json.dumps(session_data.get('cookies', {})),
                json.dumps({'localStorage': session_data.get('localStorage', {})}),
                json.dumps(session_data),
                'browser_automation',
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            print("📁 Session data stored in database")
            
        except Exception as e:
            print(f"❌ Error storing session data: {e}")
    
    def phonepe_get_dashboard_data(self, session_id):
        """Extract dashboard data from authenticated PhonePe session"""
        if session_id not in self.active_sessions:
            return {'success': False, 'error': 'Session not found'}
        
        try:
            driver = self.active_sessions[session_id]['driver']
            
            # Navigate to dashboard if not already there
            current_url = driver.current_url
            if 'dashboard' not in current_url:
                print("📊 Navigating to dashboard...")
                driver.get('https://business.phonepe.com/dashboard')
                time.sleep(3)
            
            # Extract dashboard data
            dashboard_data = {
                'url': driver.current_url,
                'title': driver.title,
                'timestamp': datetime.now().isoformat()
            }
            
            # Try to extract visible metrics/data
            try:
                # Look for common dashboard elements
                elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid], .metric, .stat, .total, .amount')
                
                extracted_data = {}
                for element in elements[:10]:  # Limit to first 10 elements
                    try:
                        text = element.text.strip()
                        if text and len(text) < 100:  # Only capture short text elements
                            key = element.get_attribute('data-testid') or element.tag_name
                            extracted_data[key] = text
                    except:
                        continue
                
                dashboard_data['extracted_elements'] = extracted_data
                
            except Exception as e:
                print(f"Could not extract dashboard elements: {e}")
            
            print("📊 Dashboard data extracted")
            return {'success': True, 'data': dashboard_data}
            
        except Exception as e:
            print(f"❌ Error getting dashboard data: {e}")
            return {'success': False, 'error': str(e)}

# Initialize clients
phonepe_client = PhonePeAPIClient()
browser_automation = BrowserAutomation()

# --- Routes ---
@app.route('/')
def index():
    """Main page with options to use wrapper or redirect to PhonePe"""
    return render_template('index.html')

@app.route('/wrapper')
def wrapper_login():
    """Wrapper login page"""
    return render_template('wrapper_login.html')

@app.route('/phonepe-redirect')
def phonepe_redirect():
    """Redirect to official PhonePe Business login"""
    return redirect('https://business.phonepe.com/login')

@app.route('/api/phonepe/test-connection')
def test_phonepe_connection():
    """Test connection to PhonePe API"""
    try:
        # Simple test to check if we can reach PhonePe
        response = requests.get(
            'https://web-api.phonepe.com', 
            timeout=10,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
            }
        )
        return jsonify({
            'success': True, 
            'message': 'Successfully connected to PhonePe servers',
            'status_code': response.status_code,
            'headers': dict(response.headers)
        })
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Connection failed: {str(e)}',
            'message': 'Unable to reach PhonePe servers'
        }), 500

@app.route('/api/phonepe/browser-login', methods=['POST'])
def phonepe_browser_login():
    """Initiate PhonePe login using browser automation"""
    data = request.get_json()
    phone = data.get('phone')
    headless = data.get('headless', True)
    
    if not phone:
        return jsonify({'success': False, 'error': 'Phone number required'}), 400
    
    # Validate phone number
    phone = re.sub(r'[^\d]', '', phone)
    if len(phone) == 10 and phone.startswith(('6', '7', '8', '9')):
        phone = phone
    elif len(phone) == 13 and phone.startswith('91'):
        phone = phone[2:]
    elif len(phone) == 12 and phone.startswith('+91'):
        phone = phone[3:]
    else:
        return jsonify({'success': False, 'error': 'Invalid phone number format. Please enter a valid Indian mobile number.'}), 400
    
    print(f"[BROWSER-LOGIN] Starting automated login for phone: {phone}")
    
    try:
        # Start browser automation
        result = browser_automation.phonepe_automated_login(
            phone_number=phone,
            headless=headless
        )
        
        if result['success']:
            session['phonepe_browser_session'] = result['session_id']
            session['phonepe_authenticated'] = True
            session['phonepe_session_data'] = result['session_data']
            
            return jsonify({
                'success': True,
                'message': 'Browser automation started successfully! Please enter OTP when prompted.',
                'session_id': result['session_id'],
                'method': 'browser_automation',
                'next_step': 'otp_required',
                'instructions': 'The browser will wait for OTP entry. Enter OTP in the automated browser window.'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Browser automation failed'),
                'method': 'browser_automation'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Browser automation error: {str(e)}',
            'method': 'browser_automation'
        }), 500

@app.route('/api/phonepe/login', methods=['POST'])
def phonepe_login():
    """Initiate PhonePe login with fallback options"""
    data = request.get_json()
    phone = data.get('phone')
    force_browser = data.get('force_browser', False)
    
    if not phone:
        return jsonify({'success': False, 'error': 'Phone number required'}), 400
    
    # Validate phone number
    phone = re.sub(r'[^\d]', '', phone)
    if len(phone) == 10 and phone.startswith(('6', '7', '8', '9')):
        phone = phone
    elif len(phone) == 13 and phone.startswith('91'):
        phone = phone[2:]
    elif len(phone) == 12 and phone.startswith('+91'):
        phone = phone[3:]
    else:
        return jsonify({'success': False, 'error': 'Invalid phone number format. Please enter a valid Indian mobile number.'}), 400
    
    print(f"[LOGIN] Attempting login for phone: {phone} (force_browser: {force_browser})")
    
    # Try direct API approach first (unless browser is forced)
    if not force_browser:
        result = phonepe_client.initiate_login(phone)
        print(f"[LOGIN] API Result: {result}")
        
        if result['success']:
            # Store temporary session data
            session['temp_phone'] = phone
            session['temp_csrf_token'] = result.get('csrf_token')
            session['temp_cookies'] = result.get('cookies', {})
            session['temp_token'] = result.get('token')  # Store the token for OTP verification
            
            print(f"[LOGIN] Success! Token stored: {result.get('token', 'No token')}")
            
            return jsonify({
                'success': True,
                'message': 'OTP request sent to PhonePe successfully! Please check your phone for the OTP.',
                'phone': phone,
                'requiresOTP': True,
                'method': 'api',
                'expiry': result.get('data', {}).get('expiry', 600),
                'debug_info': {
                    'has_token': bool(result.get('token')),
                    'has_csrf': bool(result.get('csrf_token')),
                    'cookies_count': len(result.get('cookies', {}))
                }
            })
        else:
            # Check if it's a bot detection error
            if result.get('status_code') in [401, 403] or 'csrf' in result.get('error', '').lower():
                print("[LOGIN] Bot detection suspected, suggesting browser method")
                return jsonify({
                    'success': False,
                    'error': 'PhonePe\'s anti-bot protection detected this request. Try the browser method instead.',
                    'suggest_browser': True,
                    'api_error': result.get('error'),
                    'debug_info': {
                        'status_code': result.get('status_code'),
                        'response_text': result.get('response_text', '').strip()[:200]
                    }
                }), 400
    
    # Fallback: Provide browser-based instructions
    print("[LOGIN] Using browser method fallback")
    return jsonify({
        'success': False,
        'error': 'Direct API approach failed due to anti-bot protection.',
        'browser_method': True,
        'instructions': {
            'step1': 'Open PhonePe Business in your browser',
            'step2': 'Login manually and capture the session',
            'step3': 'Use the captured session data',
            'url': 'https://business.phonepe.com/login'
        },
        'suggestion': 'Use a real browser session or wait for PhonePe to allow API access.'
    }), 400

@app.route('/api/phonepe/browser-status/<session_id>')
def phonepe_browser_status(session_id):
    """Check status of browser automation session"""
    if session_id not in browser_automation.active_sessions:
        return jsonify({'success': False, 'error': 'Session not found'}), 404
    
    session_info = browser_automation.active_sessions[session_id]
    driver = session_info['driver']
    
    try:
        current_url = driver.current_url
        title = driver.title
        
        # Check if login is complete
        authenticated = (
            'dashboard' in current_url or 
            'business.phonepe.com' in current_url and 'login' not in current_url
        )
        
        status = {
            'success': True,
            'session_id': session_id,
            'current_url': current_url,
            'title': title,
            'authenticated': authenticated,
            'created_at': session_info['created_at'].isoformat()
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/phonepe/browser-dashboard/<session_id>')
def phonepe_browser_dashboard(session_id):
    """Get dashboard data from browser automation session"""
    try:
        result = browser_automation.phonepe_get_dashboard_data(session_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/phonepe/browser-close/<session_id>', methods=['POST'])
def phonepe_browser_close(session_id):
    """Close browser automation session"""
    try:
        if session_id in browser_automation.active_sessions:
            driver = browser_automation.active_sessions[session_id]['driver']
            driver.quit()
            del browser_automation.active_sessions[session_id]
            
            return jsonify({'success': True, 'message': 'Browser session closed'})
        else:
            return jsonify({'success': False, 'error': 'Session not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/phonepe/verify-otp', methods=['POST'])
def phonepe_verify_otp():
    """Verify OTP with PhonePe"""
    data = request.get_json()
    otp = data.get('otp')
    
    phone = session.get('temp_phone')
    token = session.get('temp_token')
    
    if not all([otp, phone, token]):
        return jsonify({'success': False, 'error': 'Missing required data'}), 400
    
    # Verify OTP with PhonePe
    result = phonepe_client.verify_otp(phone, otp, token)
    
    if result['success']:
        response_data = result['data']
        
        # Store session in database
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            INSERT OR REPLACE INTO phonepe_sessions 
            (phone, user_id, access_token, refresh_token, csrf_token, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            phone,
            response_data.get('userId'),
            result.get('access_token'),
            result.get('refresh_token'),
            result.get('csrf_token'),
            datetime.now() + timedelta(hours=1)  # Token expires in 1 hour
        ))
        conn.commit()
        conn.close()
        
        # Store in Flask session
        session['phonepe_authenticated'] = True
        session['phonepe_user_id'] = response_data.get('userId')
        session['phonepe_phone'] = phone
        session['phonepe_access_token'] = result.get('access_token')
        session['phonepe_csrf_token'] = result.get('csrf_token')
        
        # Check if merchant group selection is required
        if response_data.get('groupSelection'):
            # Get merchant groups
            groups_result = phonepe_client.get_merchant_groups(
                result.get('access_token'), 
                result.get('csrf_token')
            )
            
            if groups_result['success']:
                merchant_groups = groups_result['data']
                session['merchant_groups'] = merchant_groups
                
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'user': response_data,
                    'merchantGroups': merchant_groups,
                    'requiresMerchantSelection': len(merchant_groups) > 1
                })
            else:
                return jsonify({
                    'success': True,
                    'message': 'Login successful but could not fetch merchant groups',
                    'user': response_data,
                    'requiresMerchantSelection': False
                })
        else:
            # Direct to dashboard if no group selection needed
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': response_data,
                'requiresMerchantSelection': False,
                'redirectTo': '/dashboard'
            })
    else:
        return jsonify(result), 400

@app.route('/api/phonepe/select-merchant', methods=['POST'])
def phonepe_select_merchant():
    """Select merchant and update session"""
    if not session.get('phonepe_authenticated'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    group_id = data.get('groupId') or data.get('merchantId')  # Support both for compatibility
    
    if not group_id:
        return jsonify({'success': False, 'error': 'Group ID required'}), 400
    
    access_token = session.get('phonepe_access_token')
    csrf_token = session.get('phonepe_csrf_token')
    
    result = phonepe_client.select_merchant(group_id, access_token, csrf_token)
    
    if result['success']:
        # Update session with new tokens
        session['phonepe_access_token'] = result.get('new_access_token', access_token)
        session['phonepe_csrf_token'] = result.get('new_csrf_token', csrf_token)
        session['selected_merchant'] = group_id
        
        return jsonify({
            'success': True,
            'message': 'Merchant selected successfully',
            'redirectTo': '/dashboard'
        })
    else:
        return jsonify(result), 400

@app.route('/dashboard')
def dashboard():
    """Dashboard showing PhonePe merchant data and captured authentication data"""
    # Initialize data variables
    user_profile = None
    merchant_profile = None
    transaction_stats = None
    user_permissions = None
    
    # If authenticated, fetch PhonePe data
    if session.get('phonepe_authenticated'):
        access_token = session.get('phonepe_access_token')
        csrf_token = session.get('phonepe_csrf_token')
        
        if access_token and csrf_token:
            # Get user profile
            try:
                user_result = phonepe_client.get_user_profile(access_token, csrf_token)
                if user_result['success']:
                    user_profile = user_result['data']
            except Exception as e:
                print(f"Error fetching user profile: {e}")
            
            # Get merchant profile
            try:
                merchant_result = phonepe_client.get_merchant_profile(access_token, csrf_token)
                if merchant_result['success']:
                    merchant_profile = merchant_result['data']
            except Exception as e:
                print(f"Error fetching merchant profile: {e}")
            
            # Get transaction stats (last 7 days)
            try:
                stats_result = phonepe_client.get_transaction_stats(access_token, csrf_token)
                if stats_result['success']:
                    transaction_stats = stats_result['data']
            except Exception as e:
                print(f"Error fetching transaction stats: {e}")
            
            # Get user permissions
            try:
                permissions_result = phonepe_client.get_user_permissions(access_token, csrf_token)
                if permissions_result['success']:
                    user_permissions = permissions_result['data']
            except Exception as e:
                print(f"Error fetching user permissions: {e}")
    
    # Get captured authentication data
    captured_data = browser_automation.get_captured_data()
    
    # Group data by domain for better organization
    grouped_data = {}
    for item in captured_data:
        domain = item['site_domain']
        if domain not in grouped_data:
            grouped_data[domain] = []
        grouped_data[domain].append(item)
    
    # Get browser sessions
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT session_id, status, current_url, created_at, updated_at
        FROM browser_sessions 
        ORDER BY created_at DESC
        LIMIT 10
    ''')
    browser_sessions = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return render_template('dashboard.html',
                         user_id=session.get('phonepe_user_id'),
                         phone=session.get('phonepe_phone'),
                         merchant_groups=session.get('merchant_groups', []),
                         selected_merchant=session.get('selected_merchant'),
                         user_profile=user_profile,
                         merchant_profile=merchant_profile,
                         transaction_stats=transaction_stats,
                         user_permissions=user_permissions,
                         captured_data=captured_data,
                         grouped_data=grouped_data,
                         browser_sessions=browser_sessions,
                         is_phonepe_authenticated=session.get('phonepe_authenticated', False))

@app.route('/api/phonepe/user-profile')
def get_phonepe_user_profile():
    """Get user profile from PhonePe API"""
    if not session.get('phonepe_authenticated'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    access_token = session.get('phonepe_access_token')
    csrf_token = session.get('phonepe_csrf_token')
    
    result = phonepe_client.get_user_profile(access_token, csrf_token)
    return jsonify(result)

@app.route('/api/phonepe/user-permissions')
def get_phonepe_user_permissions():
    """Get user permissions from PhonePe API"""
    if not session.get('phonepe_authenticated'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    access_token = session.get('phonepe_access_token')
    csrf_token = session.get('phonepe_csrf_token')
    
    result = phonepe_client.get_user_permissions(access_token, csrf_token)
    return jsonify(result)

@app.route('/api/phonepe/merchant-profile')
def get_phonepe_merchant_profile():
    """Get merchant profile from PhonePe API"""
    if not session.get('phonepe_authenticated'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    access_token = session.get('phonepe_access_token')
    csrf_token = session.get('phonepe_csrf_token')
    
    result = phonepe_client.get_merchant_profile(access_token, csrf_token)
    return jsonify(result)

@app.route('/api/phonepe/transaction-stats', methods=['GET', 'POST'])
def get_phonepe_transaction_stats():
    """Get transaction statistics from PhonePe API"""
    if not session.get('phonepe_authenticated'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    access_token = session.get('phonepe_access_token')
    csrf_token = session.get('phonepe_csrf_token')
    
    # Get date range from request if provided
    date_range_payload = None
    if request.method == 'POST':
        data = request.get_json()
        if data:
            date_range_payload = data
    
    result = phonepe_client.get_transaction_stats(access_token, csrf_token, date_range_payload)
    return jsonify(result)

@app.route('/api/phonepe/transactions')
def get_phonepe_transactions():
    """Get transactions from PhonePe API (Legacy endpoint - redirects to transaction stats)"""
    if not session.get('phonepe_authenticated'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    # Redirect to the new transaction stats endpoint
    return get_phonepe_transaction_stats()

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# --- Browser Routes ---
@app.route('/browser')
def browser_interface():
    """Browser interface for authentication capture"""
    return render_template('browser.html')

@app.route('/api/browser/test-dependencies')
def test_browser_dependencies():
    """Test if browser automation dependencies are working"""
    try:
        import selenium
        dependencies_status = {
            'selenium_version': selenium.__version__,
            'browsers': {}
        }
        
        # Test Firefox (primary choice)
        print("Testing Firefox...")
        try:
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            from webdriver_manager.firefox import GeckoDriverManager
            
            firefox_options = FirefoxOptions()
            firefox_options.add_argument("--headless")
            
            # Test GeckoDriver installation
            driver_path = GeckoDriverManager().install()
            dependencies_status['browsers']['firefox'] = {
                'status': 'available',
                'driver_path': driver_path,
                'recommended': True
            }
            print("✅ Firefox test passed")
            
        except Exception as e:
            dependencies_status['browsers']['firefox'] = {
                'status': 'failed',
                'error': str(e),
                'recommended': True
            }
            print(f"❌ Firefox test failed: {e}")
        
        # Test Chrome (fallback)
        print("Testing Chrome...")
        try:
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Test ChromeDriver installation
            driver_path = ChromeDriverManager().install()
            dependencies_status['browsers']['chrome'] = {
                'status': 'available',
                'driver_path': driver_path,
                'recommended': False
            }
            print("✅ Chrome test passed")
            
        except Exception as e:
            dependencies_status['browsers']['chrome'] = {
                'status': 'failed',
                'error': str(e),
                'recommended': False
            }
            print(f"❌ Chrome test failed: {e}")
        
        # Determine best available browser
        if dependencies_status['browsers'].get('firefox', {}).get('status') == 'available':
            dependencies_status['recommended_browser'] = 'firefox'
            dependencies_status['status'] = 'ready'
        elif dependencies_status['browsers'].get('chrome', {}).get('status') == 'available':
            dependencies_status['recommended_browser'] = 'chrome'
            dependencies_status['status'] = 'ready'
        else:
            dependencies_status['recommended_browser'] = 'none'
            dependencies_status['status'] = 'no_browsers_available'
        
        return jsonify({
            'success': True,
            'dependencies': dependencies_status,
            'message': 'Dependency check completed'
        })
        
    except ImportError as e:
        return jsonify({
            'success': False,
            'error': f'Missing dependency: {str(e)}',
            'message': 'Please install required packages'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Dependency check failed'
        }), 500

@app.route('/api/browser/create-session', methods=['POST'])
def create_browser_session():
    """Create a new browser session"""
    try:
        session_id = str(uuid.uuid4())
        print(f"API: Creating session {session_id}")
        
        result = browser_automation.create_browser_session(session_id)
        
        if result['success']:
            session['browser_session_id'] = session_id
            return jsonify({
                'success': True,
                'session_id': session_id,
                'message': 'Browser session created successfully'
            })
        else:
            print(f"API: Session creation failed: {result}")
            return jsonify(result), 500
            
    except Exception as e:
        error_msg = f"Unexpected error creating browser session: {str(e)}"
        print(f"API: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route('/api/browser/navigate', methods=['POST'])
def navigate_browser():
    """Navigate browser to a URL"""
    data = request.get_json()
    url = data.get('url')
    session_id = session.get('browser_session_id')
    
    if not session_id:
        return jsonify({'success': False, 'error': 'No active browser session'}), 400
    
    if not url:
        return jsonify({'success': False, 'error': 'URL required'}), 400
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    result = browser_automation.navigate_to_url(session_id, url)
    return jsonify(result)

@app.route('/api/browser/session-info')
def get_browser_session_info():
    """Get current browser session information"""
    session_id = session.get('browser_session_id')
    
    if not session_id:
        return jsonify({'success': False, 'error': 'No active browser session'}), 400
    
    result = browser_automation.get_session_info(session_id)
    return jsonify(result)

@app.route('/api/browser/captured-data')
def get_captured_data():
    """Get captured authentication data"""
    session_id = request.args.get('session_id')
    item_id = request.args.get('item_id')
    
    if item_id:
        # Get specific item by ID
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM captured_auth_data WHERE id = ?', (item_id,))
        item = c.fetchone()
        conn.close()
        
        if item:
            data = [dict(item)]
        else:
            data = []
    else:
        # Get data by session or all data
        if not session_id:
            session_id = session.get('browser_session_id')
        
        data = browser_automation.get_captured_data(session_id)
    
    return jsonify({
        'success': True,
        'data': data,
        'count': len(data)
    })

@app.route('/api/browser/close-session', methods=['POST'])
def close_browser_session():
    """Close the current browser session"""
    session_id = session.get('browser_session_id')
    
    if not session_id:
        return jsonify({'success': False, 'error': 'No active browser session'}), 400
    
    result = browser_automation.close_session(session_id)
    
    if result['success']:
        session.pop('browser_session_id', None)
    
    return jsonify(result)

@app.route('/api/browser/all-sessions')
def get_all_browser_sessions():
    """Get all browser sessions"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT session_id, status, current_url, created_at, updated_at
        FROM browser_sessions 
        ORDER BY created_at DESC
        LIMIT 20
    ''')
    sessions = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify({
        'success': True,
        'sessions': sessions
    })

@app.route('/api/browser/all-captured-data')
def get_all_captured_data():
    """Get all captured authentication data"""
    data = browser_automation.get_captured_data()
    
    # Group by domain for better organization
    grouped_data = {}
    for item in data:
        domain = item['site_domain']
        if domain not in grouped_data:
            grouped_data[domain] = []
        grouped_data[domain].append(item)
    
    return jsonify({
        'success': True,
        'data': data,
        'grouped_data': grouped_data,
        'total_count': len(data),
        'domains_count': len(grouped_data)
    })

if __name__ == '__main__':
    # Initialize database
    init_db()
    app.run(debug=True, port=5000)
