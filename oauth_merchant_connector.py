"""
OAuth-Based Merchant Data Connector
This approach uses OAuth-like flow for maximum security and compliance
"""

import requests
import json
import hashlib
import hmac
import base64
import urllib.parse
from datetime import datetime, timedelta
import uuid
import jwt
from flask import Flask, request, jsonify, redirect, session

class MerchantOAuthConnector:
    """
    OAuth-like connector for merchant payment data
    This is the most secure and compliant approach
    """
    
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.base_url = "https://api.your-gateway.com"  # Your OAuth server
    
    def generate_authorization_url(self, merchant_id, scopes):
        """
        Generate authorization URL for merchant to approve data access
        
        Scopes could be:
        - read:transactions
        - read:settlements  
        - read:profile
        - read:analytics
        """
        state = str(uuid.uuid4())  # CSRF protection
        
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(scopes),
            'state': state,
            'merchant_id': merchant_id
        }
        
        # Store state for verification
        session['oauth_state'] = state
        session['oauth_merchant_id'] = merchant_id
        
        auth_url = f"{self.base_url}/oauth/authorize?" + urllib.parse.urlencode(params)
        
        return {
            'authorization_url': auth_url,
            'state': state,
            'instructions': [
                "1. Click the authorization URL",
                "2. Log into your payment provider account", 
                "3. Review and approve the data access request",
                "4. You'll be redirected back to our platform",
                "5. Your transaction data will be available immediately"
            ]
        }
    
    def exchange_code_for_token(self, authorization_code, state):
        """
        Exchange authorization code for access token
        """
        # Verify state for CSRF protection
        if state != session.get('oauth_state'):
            raise ValueError("Invalid state parameter - possible CSRF attack")
        
        token_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = requests.post(
            f"{self.base_url}/oauth/token",
            data=token_data
        )
        
        if response.status_code == 200:
            token_info = response.json()
            
            # Store tokens securely
            encrypted_tokens = self.encrypt_tokens(token_info)
            
            return {
                'success': True,
                'access_token': token_info['access_token'],
                'refresh_token': token_info['refresh_token'],
                'expires_in': token_info['expires_in'],
                'scope': token_info['scope'],
                'encrypted_tokens': encrypted_tokens
            }
        else:
            return {
                'success': False,
                'error': f"Token exchange failed: {response.status_code}"
            }
    
    def refresh_access_token(self, refresh_token):
        """
        Refresh expired access token
        """
        refresh_data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = requests.post(
            f"{self.base_url}/oauth/token",
            data=refresh_data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Token refresh failed: {response.status_code}")

class ConsentManager:
    """
    Manages explicit merchant consent for data access
    """
    
    @staticmethod
    def create_consent_request(merchant_email, requested_scopes, purpose):
        """
        Create a formal consent request
        """
        consent_id = str(uuid.uuid4())
        
        consent_request = {
            'consent_id': consent_id,
            'merchant_email': merchant_email,
            'requested_scopes': requested_scopes,
            'purpose': purpose,
            'requested_at': datetime.now().isoformat(),
            'status': 'pending',
            'data_categories': {
                'read:transactions': {
                    'description': 'Access your transaction history',
                    'data_included': [
                        'Transaction amounts',
                        'Transaction dates', 
                        'Payment status',
                        'Reference numbers'
                    ],
                    'data_excluded': [
                        'Customer personal details',
                        'Customer contact information'
                    ]
                },
                'read:settlements': {
                    'description': 'Access settlement information',
                    'data_included': [
                        'Settlement amounts',
                        'Settlement dates',
                        'Bank reference numbers'
                    ]
                },
                'read:profile': {
                    'description': 'Access basic merchant profile',
                    'data_included': [
                        'Business name',
                        'Merchant ID',
                        'Account status'
                    ]
                }
            },
            'retention_policy': {
                'data_retention_days': 90,
                'deletion_method': 'Secure deletion with verification',
                'access_logs': 'Maintained for audit purposes'
            },
            'rights': {
                'revoke_access': 'You can revoke access at any time',
                'data_portability': 'Request your data in standard format',
                'data_correction': 'Request correction of inaccurate data',
                'transparency': 'View all access logs and usage'
            }
        }
        
        return consent_request
    
    @staticmethod
    def send_consent_email(merchant_email, consent_request):
        """
        Send consent request email to merchant
        """
        email_template = f"""
        Subject: Data Access Consent Request - Transaction Dashboard
        
        Dear Merchant,
        
        We've received a request to access your payment transaction data for dashboard analytics.
        
        WHAT DATA WE'RE REQUESTING ACCESS TO:
        {json.dumps(consent_request['data_categories'], indent=2)}
        
        PURPOSE:
        {consent_request['purpose']}
        
        YOUR RIGHTS:
        - You can approve or deny this request
        - You can revoke access at any time
        - You can request data deletion
        - You maintain full control over your data
        
        TO APPROVE THIS REQUEST:
        Click here: https://your-platform.com/consent/{consent_request['consent_id']}
        
        TO DENY THIS REQUEST:
        Simply ignore this email or click: https://your-platform.com/consent/{consent_request['consent_id']}/deny
        
        If you have questions, reply to this email or contact our support team.
        
        Best regards,
        Your Transaction Dashboard Team
        """
        
        # Send email using your preferred email service
        send_email(merchant_email, email_template)
        
        return True

class SecureDataHandler:
    """
    Handles secure storage and transmission of merchant data
    """
    
    def __init__(self):
        self.encryption_key = os.environ.get('DATA_ENCRYPTION_KEY')
        self.signing_key = os.environ.get('JWT_SIGNING_KEY')
    
    def create_data_access_token(self, merchant_id, scopes, expires_in_hours=24):
        """
        Create a short-lived token for data access
        """
        payload = {
            'merchant_id': merchant_id,
            'scopes': scopes,
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours),
            'iat': datetime.utcnow(),
            'iss': 'transaction-dashboard'
        }
        
        token = jwt.encode(payload, self.signing_key, algorithm='HS256')
        return token
    
    def verify_data_access_token(self, token):
        """
        Verify and decode data access token
        """
        try:
            payload = jwt.decode(token, self.signing_key, algorithms=['HS256'])
            return {'valid': True, 'payload': payload}
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'valid': False, 'error': 'Invalid token'}
    
    def log_data_access(self, merchant_id, data_type, accessor, timestamp=None):
        """
        Log all data access for transparency and auditing
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        access_log = {
            'merchant_id': merchant_id,
            'data_type': data_type,
            'accessor': accessor,
            'timestamp': timestamp.isoformat(),
            'ip_address': request.remote_addr if request else 'system',
            'user_agent': request.headers.get('User-Agent') if request else 'system'
        }
        
        # Store in audit log database
        store_access_log(access_log)
        
        return access_log

# Flask routes for OAuth flow

app = Flask(__name__)

@app.route('/oauth/connect/<provider>')
def initiate_oauth_flow(provider):
    """
    Start OAuth flow for payment provider
    """
    merchant_id = session.get('merchant_id')
    if not merchant_id:
        return redirect('/login')
    
    # Define scopes based on what user wants to access
    scopes = request.args.getlist('scope') or [
        'read:transactions',
        'read:settlements', 
        'read:profile'
    ]
    
    connector = MerchantOAuthConnector(
        client_id=get_oauth_client_id(provider),
        client_secret=get_oauth_client_secret(provider), 
        redirect_uri=f"{request.host_url}oauth/callback/{provider}"
    )
    
    auth_info = connector.generate_authorization_url(merchant_id, scopes)
    
    return render_template('oauth_authorization.html', {
        'provider': provider,
        'authorization_url': auth_info['authorization_url'],
        'instructions': auth_info['instructions'],
        'scopes': scopes,
        'merchant_id': merchant_id
    })

@app.route('/oauth/callback/<provider>')
def oauth_callback(provider):
    """
    Handle OAuth callback from payment provider
    """
    authorization_code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return render_template('oauth_error.html', {
            'error': error,
            'description': request.args.get('error_description')
        })
    
    if not authorization_code:
        return render_template('oauth_error.html', {
            'error': 'missing_code',
            'description': 'Authorization code not received'
        })
    
    try:
        connector = MerchantOAuthConnector(
            client_id=get_oauth_client_id(provider),
            client_secret=get_oauth_client_secret(provider),
            redirect_uri=f"{request.host_url}oauth/callback/{provider}"
        )
        
        token_result = connector.exchange_code_for_token(authorization_code, state)
        
        if token_result['success']:
            # Store encrypted tokens for merchant
            store_merchant_oauth_tokens(
                session['merchant_id'], 
                provider, 
                token_result['encrypted_tokens']
            )
            
            return render_template('oauth_success.html', {
                'provider': provider,
                'scopes': token_result['scope'],
                'expires_in': token_result['expires_in']
            })
        else:
            return render_template('oauth_error.html', {
                'error': 'token_exchange_failed',
                'description': token_result['error']
            })
            
    except Exception as e:
        return render_template('oauth_error.html', {
            'error': 'unexpected_error',
            'description': str(e)
        })

@app.route('/consent/<consent_id>')
def handle_consent(consent_id):
    """
    Handle merchant consent approval/denial
    """
    consent_request = get_consent_request(consent_id)
    
    if not consent_request:
        return render_template('consent_error.html', {
            'error': 'Consent request not found'
        })
    
    return render_template('consent_approval.html', {
        'consent_request': consent_request
    })

@app.route('/consent/<consent_id>/approve', methods=['POST'])
def approve_consent(consent_id):
    """
    Approve data access consent
    """
    consent_request = get_consent_request(consent_id)
    
    if not consent_request:
        return jsonify({'error': 'Consent request not found'}), 404
    
    # Record consent approval
    approve_consent_request(consent_id, {
        'approved_at': datetime.now().isoformat(),
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent')
    })
    
    return render_template('consent_approved.html', {
        'consent_id': consent_id,
        'next_steps': [
            "Your consent has been recorded",
            "You can now connect your payment accounts",
            "Access your transaction dashboard",
            "Revoke access anytime from settings"
        ]
    })

@app.route('/api/merchant/revoke-access', methods=['POST'])
def revoke_data_access():
    """
    Allow merchant to revoke data access
    """
    merchant_id = session.get('merchant_id')
    provider = request.json.get('provider')
    
    if not merchant_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Remove OAuth tokens
    revoke_merchant_oauth_tokens(merchant_id, provider)
    
    # Log the revocation
    log_data_access_revocation(merchant_id, provider)
    
    return jsonify({
        'success': True,
        'message': f'Access to {provider} data has been revoked'
    })

# Helper functions (implement these based on your database setup)
def get_oauth_client_id(provider):
    # Return OAuth client ID for provider
    pass

def get_oauth_client_secret(provider):
    # Return OAuth client secret for provider  
    pass

def store_merchant_oauth_tokens(merchant_id, provider, encrypted_tokens):
    # Store encrypted OAuth tokens in database
    pass

def get_consent_request(consent_id):
    # Fetch consent request from database
    pass

def approve_consent_request(consent_id, approval_info):
    # Mark consent as approved in database
    pass

def revoke_merchant_oauth_tokens(merchant_id, provider):
    # Remove OAuth tokens from database
    pass

def log_data_access_revocation(merchant_id, provider):
    # Log access revocation for audit
    pass

def send_email(recipient, content):
    # Send email using your email service
    pass

def store_access_log(access_log):
    # Store access log in database
    pass

if __name__ == '__main__':
    app.run(debug=True, port=5002)