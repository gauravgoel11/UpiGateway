"""
OATS (Otomashen ATS) Job Management Chatbot - Rebuilt and Fixed Version
- Correctly implements dynamic search and specific ID lookups using URL templates.
- Replaces the simple endpoint selector with an intelligent query router.
- Built upon the user-provided stable base code to ensure core functionality remains.
"""

import json
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import google.generativeai as genai
from typing import Dict, List, Optional
from dataclasses import dataclass
import re # Import the regular expression module

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class APIEndpoint:
    """Data class to represent an API endpoint"""
    url: str
    description: str
    category: str = "general"

@dataclass
class APIResponse:
    """Data class to represent API response"""
    success: bool
    status_code: int
    data: Optional[Dict] = None
    error_message: Optional[str] = None
    endpoint_url: Optional[str] = None


class OATSChatbot:
    """Fixed OATS Chatbot with a new, intelligent query processing engine."""
    
    def __init__(self):
        # Configuration
        self.base_url = "https://dev.oats-backend.otomashen.com"
        self.email = "gaurav.int@otomashen.com"
        self.password = "462lx@wCX&&0!k"
        self.login_url = f"{self.base_url}/rbca/token/"
        self.logout_url = f"{self.base_url}/login-api/logout/"
        self.gemini_api_key = "AIzaSyAsVkN0ygVBsl2tVAN_Dq5E0AY5aabyrqA"
        
        # Session setup
        self.session = self._create_session()
        self.access_token = None
        self.available_tokens = {}
        
        # Setup Gemini AI
        try:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {e}")
            self.gemini_model = None
        
        # Define available endpoints (now with templates)
        self.endpoints = self._get_available_endpoints()
    
    def _create_session(self):
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        })
        return session
    '''C:\Users\GAURAV G\Desktop\New folder\backend\chatbotv5v1 copy 3.py'''
    def login(self):
        print("🔐 Logging in...")
        payload = {"email": self.email, "password": self.password}
        try:
            response = self.session.post(self.login_url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print("   ✅ Login successful (HTTP 200)")
                self.access_token = self._extract_token(data)
                if self.access_token:
                    print("   🔑 Token extracted successfully.")
                    return True
            print(f"   ❌ Login failed (HTTP {response.status_code})")
            return False
        except Exception as e:
            print(f"   ❌ Exception during login: {e}")
            return False

    def _extract_token(self, response_data):
        self.available_tokens = {}
        access_token = response_data.get("Tokens", {}).get("access")
        authtoken = response_data.get("Authtoken")
        if access_token: self.available_tokens['access'] = access_token
        if authtoken: self.available_tokens['authtoken'] = authtoken
        return access_token

    def logout(self):
        if not self.access_token: return
        print("🔓 Logging out...")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            self.session.post(self.logout_url, headers=headers, timeout=5)
        finally:
            self.access_token = None
            self.available_tokens = {}
            print("   ✅ Session cleaned up.")

    def _get_available_endpoints(self) -> Dict[str, APIEndpoint]:
        """Define available API endpoints, using placeholders for dynamic values."""
        return {
            "jobs": APIEndpoint(f"{self.base_url}/jobs/get-job-list-filter-with-Paginator/", "Get job listings", "job"),
            "job_status": APIEndpoint(f"{self.base_url}/jobs/job-status-count/", "Get job status counts", "dashboard"),
            # --- TEMPLATE ENDPOINTS ---
            "candidate_details": APIEndpoint(
                url=f"{self.base_url}/candidate/get/personal-detail-list/?CidId={{CidId}}",
                description="Get all details for a specific candidate by their ID.",
                category="candidate_specific"
            ),
            "candidate_search": APIEndpoint(
                url=f"{self.base_url}/candidate/get_candidate_list/filter_with_Paginator/?Page=1&PerPage=100&IncludeFields[]=cid_id,first_name,current_job_title,email,mobile_phone&Search={{search_term}}",
                description="Search for candidates using a filter term.",
                category="candidate_search"
            ),
            # --- STATIC ENDPOINTS ---
            "clients": APIEndpoint(f"{self.base_url}/client/get-client-list-filter-with-Paginator/", "Get client listings", "client"),
            "vendors": APIEndpoint(f"{self.base_url}/vendor/get-vendor-list-filter/", "Get vendor listings", "vendor"),
            "users": APIEndpoint(f"{self.base_url}/rbca/get-users/", "Get user listings", "user")
        }
    
    def fetch_data_from_endpoint(self, endpoint: APIEndpoint) -> APIResponse:
        """Fetch data from a single endpoint using working authentication."""
        if not self.access_token:
            return APIResponse(False, 401, error_message="No access token available", endpoint_url=endpoint.url)
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "authtoken": self.available_tokens.get("authtoken", ""),
            "Content-Type": "application/json"
        }
        
        try:
            method = "POST" if "/jobs/" in endpoint.url and "status-count" not in endpoint.url else "GET"
            print(f"   📞 Making {method} request to: {endpoint.url}")
            response = self.session.request(method, endpoint.url, headers=headers, timeout=30)  # Increased timeout
            print(f"   📬 Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   📊 Data received: {len(str(data))} characters")
                return APIResponse(True, 200, data=data, endpoint_url=endpoint.url)
            else:
                print(f"   ❌ HTTP Error {response.status_code}: {response.text[:200]}")
                return APIResponse(False, response.status_code, error_message=f"HTTP Error {response.status_code}", endpoint_url=endpoint.url)
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout for API call to {endpoint.url}: {e}")
            return APIResponse(False, 0, error_message="Request timed out", endpoint_url=endpoint.url)
        except requests.exceptions.RequestException as e:
            logger.error(f"API call to {endpoint.url} failed: {e}")
            return APIResponse(False, 0, error_message=str(e), endpoint_url=endpoint.url)
    
    def generate_ai_response(self, user_query: str, api_responses: List[APIResponse]) -> str:
        """Generate AI response based on fetched data."""
        if not self.gemini_model:
            return "AI model not available. Please check the Gemini API key."
        
        successful_data = [res.data for res in api_responses if res.success]
        if not successful_data:
            return "I apologize, but I couldn't retrieve any information for your request. The system might be unavailable or the query had no results."

        prompt = f"""
You are an expert AI assistant for the OATS recruitment system. Your task is to provide a clear, concise, and professional answer to the user's query based *only* on the JSON data provided.

User Query: "{user_query}"

API Data Provided:
{json.dumps(successful_data, indent=2)}

Guidelines:
1.  **Synthesize, Don't Just Repeat:** Combine the information from the data into a helpful, readable answer.
2.  **For Specific Candidate Data:** Summarize the key details you find, such as name, email, phone number, skills, and experience.
3.  **For Lists (Search Results):** State how many results were found. Then, list the key items (e.g., the names and job titles of the candidates).
4.  **Professional Tone:** Be conversational but direct. Do not mention JSON, API endpoints, or technical details.
5.  **If Data is Empty:** If the data is an empty list (`[]`), clearly state that no results were found for the search.
"""
        try:
            return self.gemini_model.generate_content(prompt).text.strip()
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I retrieved data but had trouble processing it. Please try again."
    
    def extract_search_term(self, query: str, search_keywords: List[str]) -> str:
        """Extract the actual search term from user query by removing search keywords."""
        query_lower = query.lower().strip()
        
        # Remove search keywords from the beginning or middle of the query
        for keyword in search_keywords:
            if query_lower.startswith(keyword):
                query_lower = query_lower[len(keyword):].strip()
                break
            elif keyword in query_lower:
                # Remove the keyword and everything before it
                parts = query_lower.split(keyword, 1)
                if len(parts) > 1:
                    query_lower = parts[1].strip()
                break
        
        # Remove common words that might interfere with search
        stop_words = ['me', 'for', 'about', 'that', 'is', 'are', 'the', 'a', 'an', 'please', 'can', 'you', 'person', 'who', 'live', 'in', 'all']
        words = query_lower.split()
        filtered_words = [word for word in words if word not in stop_words]
        
        # If we have location terms, simplify to just the city name
        if 'jaipur' in query_lower:
            return 'jaipur'
        elif 'delhi' in query_lower:
            return 'delhi'
        elif 'mumbai' in query_lower:
            return 'mumbai'
        elif 'bangalore' in query_lower or 'bengaluru' in query_lower:
            return 'bangalore'
        elif 'hyderabad' in query_lower:
            return 'hyderabad'
        
        # For profession searches, extract key terms
        if 'data engineer' in query_lower:
            return 'data engineer'
        elif 'software engineer' in query_lower:
            return 'software engineer'
        elif 'developer' in query_lower:
            return 'developer'
        elif 'analyst' in query_lower:
            return 'analyst'
        
        return ' '.join(filtered_words) if filtered_words else query_lower
    
    def process_query(self, user_query: str) -> str:
        """FIXED: Intelligent query router to handle different user intents."""
        query_lower = user_query.lower().strip()
        api_responses = []

        print(f"🔍 Processing query: '{user_query}'")

        # --- Priority 1: Check for a specific Candidate ID ---
        cid_match = re.search(r'(CID\d+)', query_lower, re.IGNORECASE)
        if cid_match:
            candidate_id = cid_match.group(1).upper()
            print(f"🎯 Intent Detected: Specific Candidate Details for ID: {candidate_id}")
            template = self.endpoints['candidate_details']
            # Format the URL from the template with the found ID
            specific_url = template.url.format(CidId=candidate_id)
            endpoint_to_call = APIEndpoint(url=specific_url, description=template.description, category=template.category)
            
            print(f"📡 Fetching from: {endpoint_to_call.url}")
            api_responses.append(self.fetch_data_from_endpoint(endpoint_to_call))
            return self.generate_ai_response(user_query, api_responses)

        # --- Priority 2: Check for specific endpoint keywords FIRST ---
        endpoint_keywords = {
            'job': ['job', 'jobs', 'position', 'positions', 'opening', 'openings'],
            'client': ['client', 'clients', 'company', 'companies'],
            'vendor': ['vendor', 'vendors', 'supplier', 'suppliers'],
            'user': ['user', 'users', 'employee', 'employees', 'staff'],
            'dashboard': ['dashboard', 'status', 'summary', 'overview', 'count']
        }
        
        # Check if query is asking for specific entity types (not candidate search)
        for endpoint_key, keywords in endpoint_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                print(f"🎯 Intent Detected: {endpoint_key.title()} Query")
                endpoint_to_call = None
                
                if endpoint_key == 'job':
                    endpoint_to_call = self.endpoints['jobs']
                elif endpoint_key == 'client':
                    endpoint_to_call = self.endpoints['clients']
                elif endpoint_key == 'vendor':
                    endpoint_to_call = self.endpoints['vendors']
                elif endpoint_key == 'user':
                    endpoint_to_call = self.endpoints['users']
                elif endpoint_key == 'dashboard':
                    endpoint_to_call = self.endpoints['job_status']
                
                if endpoint_to_call:
                    print(f"📡 Fetching from: {endpoint_to_call.url}")
                    api_responses.append(self.fetch_data_from_endpoint(endpoint_to_call))
                    return self.generate_ai_response(user_query, api_responses)

        # --- Priority 3: Check for candidate search/filter query ---
        search_keywords = ['find', 'search', 'search for', 'search me', 'list', 'show me', 'who are', 'tell me about', 'get me', 'look for']
        candidate_indicators = ['candidate', 'candidates', 'person', 'people', 'developer', 'engineer', 'analyst', 'manager']
        
        # Check if it's a candidate search query
        has_search_keyword = any(keyword in query_lower for keyword in search_keywords)
        has_candidate_indicator = any(indicator in query_lower for indicator in candidate_indicators)
        
        # Additional check for profession/skill based searches
        profession_keywords = ['data engineer', 'software engineer', 'developer', 'analyst', 'designer', 'manager', 'python', 'java', 'react', 'sql']
        has_profession = any(prof in query_lower for prof in profession_keywords)
        
        # Location-based search detection
        location_keywords = ['jaipur', 'delhi', 'mumbai', 'bangalore', 'bengaluru', 'hyderabad', 'chennai', 'pune', 'kolkata']
        has_location = any(loc in query_lower for loc in location_keywords)
        
        if has_search_keyword or has_candidate_indicator or has_profession or has_location:
            # Extract the actual term to search for
            search_term = self.extract_search_term(user_query, search_keywords)
            
            # If no meaningful search term extracted, try simpler approach
            if not search_term or len(search_term.strip()) < 2:
                # For "data engineers" queries, use just "data engineer"
                if 'data engineer' in query_lower:
                    search_term = 'data engineer'
                elif 'software engineer' in query_lower:
                    search_term = 'software engineer'
                else:
                    search_term = user_query
            
            print(f"🎯 Intent Detected: Candidate Search/Filter. Term: '{search_term}'")
            template = self.endpoints['candidate_search']
            # Format the URL from the template with the search term
            specific_url = template.url.format(search_term=requests.utils.quote(search_term))
            endpoint_to_call = APIEndpoint(url=specific_url, description=template.description, category=template.category)
            
            print(f"📡 Fetching candidate search results...")
            api_responses.append(self.fetch_data_from_endpoint(endpoint_to_call))
            return self.generate_ai_response(user_query, api_responses)

        # --- Fallback: Default to dashboard status ---
        print("🤔 Intent Detected: General Query - showing dashboard status.")
        api_responses.append(self.fetch_data_from_endpoint(self.endpoints['job_status']))
        return self.generate_ai_response(user_query, api_responses)
    
    def run_interactive_session(self):
        """Run interactive chatbot session."""
        print("\n" + "="*60 + "\n🤖 OATS Job Management Chatbot (Fixed & Upgraded)\n" + "="*60)
        print("I can now handle specific searches! Try asking:")
        print("  • `tell me about CID8175898`")
        print("  • `search for data engineer`")
        print("  • `find python developers`")
        print("  • `search for candidates in jaipur`")
        print("  • `list jobs`")
        print("  • `show me vendors`")
        print("  • `tell me about clients`")
        print("\nCommands: `login`, `exit`\n" + "="*60)
        
        if not self.login():
            print("❌ Critical: Login failed. Chatbot cannot operate.")
            return
        
        print("\n🤖 Chatbot is ready! How can I help you today?")
        
        while True:
            try:
                user_input = input("💬 You: ").strip()
                if user_input.lower() in ['exit', 'quit']:
                    break
                if not user_input:
                    continue
                if user_input.lower() == 'login':
                    self.login()
                    continue

                print("\n🤖 Processing your request...")
                try:
                    response = self.process_query(user_input)
                    print(f"\n🤖 Assistant: {response}\n\n" + "-" * 60)
                except Exception as query_error:
                    logger.error(f"Error processing query '{user_input}': {query_error}")
                    print(f"\n🤖 Assistant: I encountered an error processing your request. Please try rephrasing or try again.\n\n" + "-" * 60)
                    
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted by user.")
                break
            except Exception as e:
                logger.error(f"A critical error occurred in the session loop: {e}", exc_info=True)
                print("🤖 Apologies, a critical error occurred. Please restart the session.")
        
        print("\n👋 Goodbye!")
        self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        self.logout()
        if self.session:
            self.session.close()

def main():
    """Main application entry point"""
    print("🚀 Starting OATS Job Management Chatbot...")
    chatbot = OATSChatbot()
    try:
        chatbot.run_interactive_session()
    finally:
        print("🔚 Chatbot session ended")

if __name__ == "__main__":
    main()