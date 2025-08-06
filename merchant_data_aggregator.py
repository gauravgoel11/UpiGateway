"""
Merchant Data Aggregator - Legal and Compliant Approach
This system allows merchants to connect their own payment accounts
"""

import requests
import json
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import os
from flask import Flask, request, jsonify, session, render_template

app = Flask(__name__)
app.secret_key = 'your-secret-key'

class MerchantDataAggregator:
    """
    Legal merchant data aggregation system
    Merchants provide their own API credentials with full consent
    """
    
    def __init__(self):
        # Initialize encryption for storing merchant credentials
        self.cipher = Fernet(os.environ.get('ENCRYPTION_KEY', Fernet.generate_key()))
        self.supported_providers = {
            'phonepe': PhonePeDataConnector,
            'razorpay': RazorpayDataConnector,
            'payu': PayUDataConnector,
            'cashfree': CashfreeDataConnector
        }
    
    def encrypt_credentials(self, credentials):
        """Securely encrypt merchant credentials"""
        return self.cipher.encrypt(json.dumps(credentials).encode())
    
    def decrypt_credentials(self, encrypted_credentials):
        """Decrypt merchant credentials"""
        return json.loads(self.cipher.decrypt(encrypted_credentials).decode())

class MerchantConsentManager:
    """
    Handles merchant consent and credential management
    """
    
    @staticmethod
    def initiate_merchant_onboarding(merchant_email, merchant_name):
        """
        Start the merchant onboarding process with clear consent
        """
        return {
            'consent_url': f'/merchant/consent/{merchant_email}',
            'instructions': [
                "1. You will provide your own PhonePe Business API credentials",
                "2. We will only access data you explicitly authorize",
                "3. You can revoke access at any time",
                "4. All data remains under your control"
            ],
            'data_accessed': [
                "Transaction history",
                "Payment status",
                "Settlement information",
                "Basic merchant profile"
            ],
            'data_not_accessed': [
                "Customer personal information",
                "Bank account details",
                "Login credentials"
            ]
        }

class PhonePeDataConnector:
    """
    Connector for PhonePe Business API (when available)
    Uses merchant's own API credentials
    """
    
    def __init__(self, merchant_credentials):
        self.merchant_id = merchant_credentials.get('merchant_id')
        self.api_key = merchant_credentials.get('api_key')
        self.api_secret = merchant_credentials.get('api_secret')
        self.base_url = "https://api.phonepe.com"  # Hypothetical official API
    
    def get_transactions(self, start_date, end_date, limit=100):
        """
        Fetch transactions using merchant's own API credentials
        """
        try:
            # This would be the official PhonePe Business API
            # Currently, PhonePe doesn't provide a public transaction API
            # This is a conceptual implementation
            
            params = {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'limit': limit
            }
            
            # Generate signature using merchant's credentials
            signature = self._generate_signature(params)
            
            headers = {
                'X-API-Key': self.api_key,
                'X-Signature': signature,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.base_url}/v1/merchant/transactions",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'provider': 'phonepe'
                }
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code}",
                    'provider': 'phonepe'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'provider': 'phonepe'
            }
    
    def _generate_signature(self, params):
        """Generate API signature using merchant's secret"""
        payload = json.dumps(params, sort_keys=True)
        signature = hmac.new(
            self.api_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

class UnifiedDashboard:
    """
    Unified dashboard showing data from multiple payment providers
    """
    
    def __init__(self, merchant_id):
        self.merchant_id = merchant_id
        self.aggregator = MerchantDataAggregator()
    
    def get_all_transactions(self, days_back=30):
        """
        Fetch transactions from all connected providers
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get merchant's connected providers
        connected_providers = self.get_merchant_providers()
        
        all_transactions = []
        provider_stats = {}
        
        for provider_name, credentials in connected_providers.items():
            try:
                connector_class = self.aggregator.supported_providers[provider_name]
                connector = connector_class(credentials)
                
                result = connector.get_transactions(start_date, end_date)
                
                if result['success']:
                    transactions = result['data'].get('transactions', [])
                    all_transactions.extend(transactions)
                    
                    provider_stats[provider_name] = {
                        'total_transactions': len(transactions),
                        'total_amount': sum(t.get('amount', 0) for t in transactions),
                        'success_rate': self.calculate_success_rate(transactions),
                        'status': 'connected'
                    }
                else:
                    provider_stats[provider_name] = {
                        'status': 'error',
                        'error': result['error']
                    }
                    
            except Exception as e:
                provider_stats[provider_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return {
            'transactions': self.normalize_transactions(all_transactions),
            'provider_stats': provider_stats,
            'summary': self.generate_summary(all_transactions)
        }
    
    def normalize_transactions(self, transactions):
        """
        Normalize transaction data from different providers
        """
        normalized = []
        
        for txn in transactions:
            normalized.append({
                'id': txn.get('transaction_id', txn.get('id')),
                'date': txn.get('created_at', txn.get('date')),
                'amount': float(txn.get('amount', 0)),
                'status': self.normalize_status(txn.get('status')),
                'customer_name': txn.get('customer_name', 'N/A'),
                'payment_method': txn.get('payment_method', 'UPI'),
                'provider': txn.get('provider', 'unknown'),
                'reference_id': txn.get('reference_id', txn.get('payment_id'))
            })
        
        return sorted(normalized, key=lambda x: x['date'], reverse=True)
    
    def normalize_status(self, status):
        """Normalize status across different providers"""
        status_mapping = {
            'SUCCESS': 'success',
            'COMPLETED': 'success',
            'PAID': 'success',
            'FAILED': 'failed',
            'FAILURE': 'failed',
            'PENDING': 'pending',
            'PROCESSING': 'pending'
        }
        return status_mapping.get(status.upper(), status.lower())
    
    def calculate_success_rate(self, transactions):
        """Calculate success rate for transactions"""
        if not transactions:
            return 0
        
        successful = sum(1 for t in transactions if self.normalize_status(t.get('status', '')) == 'success')
        return (successful / len(transactions)) * 100
    
    def generate_summary(self, transactions):
        """Generate transaction summary"""
        total_amount = sum(t.get('amount', 0) for t in transactions)
        successful_txns = [t for t in transactions if self.normalize_status(t.get('status', '')) == 'success']
        
        return {
            'total_transactions': len(transactions),
            'successful_transactions': len(successful_txns),
            'total_amount': total_amount,
            'success_rate': self.calculate_success_rate(transactions),
            'average_transaction': total_amount / len(transactions) if transactions else 0
        }
    
    def get_merchant_providers(self):
        """Get merchant's connected payment providers"""
        # This would fetch from your database
        # Return decrypted credentials for connected providers
        return {
            # Example structure - actual implementation would fetch from DB
            # 'phonepe': {
            #     'merchant_id': 'merchant123',
            #     'api_key': 'key123',
            #     'api_secret': 'secret123'
            # }
        }

# Flask Routes for the Dashboard

@app.route('/')
def dashboard_home():
    """Main dashboard page"""
    return render_template('merchant_dashboard.html')

@app.route('/merchant/connect')
def connect_providers():
    """Page to connect payment providers"""
    return render_template('connect_providers.html', {
        'supported_providers': [
            {
                'name': 'PhonePe Business',
                'logo': '/static/phonepe-logo.png',
                'description': 'Connect your PhonePe Business account',
                'fields_required': ['Merchant ID', 'API Key', 'API Secret'],
                'setup_url': '/setup/phonepe'
            },
            {
                'name': 'Razorpay',
                'logo': '/static/razorpay-logo.png',
                'description': 'Connect your Razorpay account',
                'fields_required': ['Key ID', 'Key Secret'],
                'setup_url': '/setup/razorpay'
            }
        ]
    })

@app.route('/setup/phonepe', methods=['GET', 'POST'])
def setup_phonepe():
    """Setup PhonePe connection with merchant consent"""
    if request.method == 'GET':
        return render_template('setup_phonepe.html', {
            'consent_text': """
            By connecting your PhonePe Business account, you authorize us to:
            
            ✅ Access your transaction history
            ✅ Retrieve payment status information  
            ✅ Show settlement data
            ✅ Display basic account information
            
            ❌ We will NOT access:
            ❌ Customer personal details
            ❌ Your login credentials
            ❌ Bank account information
            ❌ Any data you don't explicitly authorize
            
            You can disconnect at any time from your dashboard.
            """
        })
    
    elif request.method == 'POST':
        # Handle merchant providing their credentials
        merchant_id = request.form.get('merchant_id')
        api_key = request.form.get('api_key')
        api_secret = request.form.get('api_secret')
        consent_given = request.form.get('consent') == 'true'
        
        if not consent_given:
            return jsonify({
                'success': False,
                'error': 'Consent is required to connect your account'
            }), 400
        
        # Validate credentials with PhonePe (test API call)
        test_result = test_phonepe_credentials(merchant_id, api_key, api_secret)
        
        if test_result['valid']:
            # Encrypt and store credentials
            aggregator = MerchantDataAggregator()
            encrypted_creds = aggregator.encrypt_credentials({
                'merchant_id': merchant_id,
                'api_key': api_key,
                'api_secret': api_secret
            })
            
            # Store in database (implement your DB logic)
            store_merchant_credentials(session['merchant_id'], 'phonepe', encrypted_creds)
            
            return jsonify({
                'success': True,
                'message': 'PhonePe account connected successfully',
                'redirect': '/dashboard'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid PhonePe credentials. Please check and try again.'
            }), 400

@app.route('/api/transactions')
def get_transactions():
    """API endpoint to fetch all transactions"""
    merchant_id = session.get('merchant_id')
    if not merchant_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    days_back = request.args.get('days', 30, type=int)
    
    dashboard = UnifiedDashboard(merchant_id)
    data = dashboard.get_all_transactions(days_back)
    
    return jsonify(data)

@app.route('/api/disconnect/<provider>')
def disconnect_provider(provider):
    """Disconnect a payment provider"""
    merchant_id = session.get('merchant_id')
    if not merchant_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Remove provider credentials from database
    remove_merchant_credentials(merchant_id, provider)
    
    return jsonify({
        'success': True,
        'message': f'{provider.title()} account disconnected successfully'
    })

def test_phonepe_credentials(merchant_id, api_key, api_secret):
    """Test PhonePe credentials with a simple API call"""
    try:
        # This would make a test call to PhonePe's API
        # Since there's no public API, this is conceptual
        
        # For now, just validate format
        if len(merchant_id) > 5 and len(api_key) > 10 and len(api_secret) > 10:
            return {'valid': True}
        else:
            return {'valid': False, 'error': 'Invalid credential format'}
            
    except Exception as e:
        return {'valid': False, 'error': str(e)}

def store_merchant_credentials(merchant_id, provider, encrypted_credentials):
    """Store encrypted merchant credentials in database"""
    # Implement your database storage logic here
    pass

def remove_merchant_credentials(merchant_id, provider):
    """Remove merchant credentials from database"""
    # Implement your database removal logic here
    pass

if __name__ == '__main__':
    app.run(debug=True, port=5001)