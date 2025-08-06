# 🚀 Kamlai Multi Service - Complete Merchant Solution

A production-ready merchant payment solution similar to [UPIGateway.com](https://upigateway.com/) that enables merchants to accept UPI payments directly to their accounts with dynamic QR code generation and comprehensive transaction tracking.

## 🎯 Features

### ✅ **Core Functionality**
- **Dynamic QR Code Generation** - Unique QR codes for each transaction
- **Real-time Transaction Tracking** - Monitor all payments in real-time
- **Merchant Dashboard** - Complete web interface for merchants
- **REST API** - Developer-friendly API for integration
- **Webhook Support** - Real-time payment notifications
- **Multi-UPI App Support** - Works with PhonePe, GPay, Paytm, BHIM, etc.

### ✅ **Merchant Features**
- User registration and authentication
- Transaction history and analytics
- API key management
- Payment status monitoring
- Customer information tracking
- Success rate analytics

### ✅ **Developer Features**
- RESTful API endpoints
- HMAC signature authentication
- Comprehensive integration examples
- Python SDK included
- Webhook implementation
- Rate limiting and security

## 🔧 Quick Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager

### 1. **Automated Setup (Recommended)**

```bash
# Clone or download the files to a directory
cd your-upi-gateway-directory

# Run the automated setup script
python start_gateway.py
```

The script will:
- ✅ Check Python version compatibility
- ✅ Install all required dependencies
- ✅ Initialize the database
- ✅ Create a sample merchant account
- ✅ Start the development server

### 2. **Manual Setup**

```bash
# Install dependencies
pip install -r requirements_gateway.txt

# Initialize database
python -c "from upi_gateway_app import app, db; app.app_context().push(); db.create_all()"

# Start the server
python upi_gateway_app.py
```

## 🌐 Access Your Gateway

After setup, your Kamlai Multi Service will be available at:

- **🏠 Home Page**: http://localhost:5000
- **📊 Merchant Dashboard**: http://localhost:5000/dashboard
- **🔑 Login Page**: http://localhost:5000/login

### 🧪 **Demo Credentials**
- **Email**: `demo@upigateway.com`
- **Password**: `demo123`

## 📱 How It Works

### For Merchants:
1. **Register** → Create merchant account
2. **Get API Keys** → Access dashboard for credentials
3. **Integrate** → Use API to create payment requests
4. **Track** → Monitor transactions in real-time

### For Customers:
1. **Checkout** → Customer proceeds to payment
2. **QR Code** → Dynamic QR displayed
3. **Pay** → Scan with any UPI app
4. **Confirm** → Payment verified automatically

## 🔌 API Integration

### Authentication
All API requests require:
- `X-API-Key`: Your merchant API key
- `X-Signature`: HMAC-SHA256 signature of request body

### Create Payment
```python
import requests
import json
import hmac
import hashlib

# Your credentials (get from dashboard)
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"
BASE_URL = "http://localhost:5000/api"

def create_payment(amount, customer_name, customer_email, redirect_url):
    data = {
        'amount': amount,
        'customer_name': customer_name,
        'customer_email': customer_email,
        'redirect_url': redirect_url
    }
    
    # Generate signature
    payload = json.dumps(data, sort_keys=True)
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
        'X-Signature': signature
    }
    
    response = requests.post(f"{BASE_URL}/payment/create", json=data, headers=headers)
    return response.json()

# Example usage
result = create_payment(
    amount=100.0,
    customer_name="John Doe",
    customer_email="john@example.com",
    redirect_url="https://yoursite.com/success"
)

if result['success']:
    print(f"Payment URL: {result['payment_url']}")
    print(f"Transaction ID: {result['transaction_id']}")
```

### Check Payment Status
```python
def check_payment_status(transaction_id):
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
        'X-Signature': hmac.new(
            API_SECRET.encode('utf-8'),
            b'',
            hashlib.sha256
        ).hexdigest()
    }
    
    response = requests.get(f"{BASE_URL}/payment/status/{transaction_id}", headers=headers)
    return response.json()

# Check status
status = check_payment_status("TXN_1234567890")
print(f"Status: {status['status']}")
```

## 🔗 Integration Examples

### E-commerce Checkout
```python
# Complete e-commerce integration example
from integration_examples import UPIGatewayClient

client = UPIGatewayClient(
    api_key="your_api_key",
    api_secret="your_api_secret"
)

# Create payment for checkout
result = client.create_payment(
    amount=299.99,
    customer_name="Customer Name",
    customer_email="customer@example.com",
    redirect_url="https://yourstore.com/order-confirmation"
)

# Redirect customer to payment URL
print(f"Redirect to: {result['payment_url']}")
```

### Webhook Handler
```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook/payment', methods=['POST'])
def handle_payment_webhook():
    data = request.get_json()
    
    transaction_id = data.get('transaction_id')
    status = data.get('status')
    amount = data.get('amount')
    
    if status == 'SUCCESS':
        # Payment successful - update order status
        update_order_status(transaction_id, 'PAID')
        send_confirmation_email(data.get('customer_email'))
    
    elif status == 'FAILED':
        # Payment failed - handle accordingly
        update_order_status(transaction_id, 'FAILED')
    
    return jsonify({'status': 'success'})
```

## 📊 Dashboard Features

### Merchant Dashboard
- **Real-time Statistics** - Transaction counts, success rates, total amounts
- **Transaction History** - Detailed transaction listing with filters
- **API Management** - View and manage API keys
- **Integration Guide** - Code examples for multiple languages
- **Payment Monitoring** - Real-time payment status updates

### Transaction Management
- **Search & Filter** - Find transactions by date, status, amount
- **Export Data** - Download transaction reports
- **Webhook Configuration** - Set up payment notifications
- **Customer Information** - Track customer payment history

## 🔒 Security Features

### API Security
- **HMAC Authentication** - Request signature verification
- **Rate Limiting** - Prevent API abuse
- **Input Validation** - Comprehensive request validation
- **SQL Injection Protection** - Parameterized queries

### Payment Security
- **Transaction Integrity** - Each payment has unique identifiers
- **Status Verification** - Real-time payment verification
- **Secure Webhooks** - Signed webhook notifications
- **Data Encryption** - Sensitive data protection

## 📈 Production Deployment

### Using Gunicorn (Recommended)
```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 upi_gateway_app:app
```

### Environment Variables
```bash
# Create .env file
export FLASK_ENV=production
export SECRET_KEY=your_secret_key_here
export DATABASE_URL=postgresql://user:pass@localhost/upigateway
export WEBHOOK_SECRET=your_webhook_secret
```

### Database Migration (PostgreSQL)
```python
# For production, use PostgreSQL
pip install psycopg2-binary

# Update app.py database URL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/upigateway'
```

## 🔧 Customization

### Adding Payment Gateways
```python
# Extend UPIGatewayService class
class CustomUPIGatewayService(UPIGatewayService):
    def integrate_razorpay(self):
        # Add Razorpay integration
        pass
    
    def integrate_payu(self):
        # Add PayU integration
        pass
```

### Custom Webhooks
```python
# Add custom webhook endpoints
@app.route('/api/webhook/custom', methods=['POST'])
def custom_webhook():
    # Handle custom notifications
    pass
```

## 📞 Support

### Documentation
- **API Reference**: Available at `/api/docs` (when server is running)
- **Integration Examples**: See `integration_examples.py`
- **Code Samples**: Available in dashboard

### Troubleshooting

#### Common Issues:

1. **Dependencies Error**
   ```bash
   # Solution: Update pip and install dependencies
   pip install --upgrade pip
   pip install -r requirements_gateway.txt
   ```

2. **Database Error**
   ```bash
   # Solution: Reinitialize database
   python -c "from upi_gateway_app import app, db; app.app_context().push(); db.drop_all(); db.create_all()"
   ```

3. **Port Already in Use**
   ```bash
   # Solution: Use different port
   python upi_gateway_app.py --port 5001
   ```

4. **API Authentication Failed**
   - Check API key and secret in dashboard
   - Verify signature generation
   - Ensure Content-Type is 'application/json'

## 🚀 Advanced Features

### Batch Payments
```python
# Process multiple payments
payments = [
    {'amount': 100, 'customer_name': 'Customer 1', 'customer_email': 'c1@example.com'},
    {'amount': 200, 'customer_name': 'Customer 2', 'customer_email': 'c2@example.com'},
]

for payment_data in payments:
    result = client.create_payment(**payment_data)
    print(f"Created: {result['transaction_id']}")
```

### Real-time Monitoring
```python
# Monitor payment status with polling
final_status = client.wait_for_payment(
    transaction_id="TXN_123",
    timeout=300,  # 5 minutes
    poll_interval=5  # Check every 5 seconds
)
```

## 📄 License

This project is open source and available under the MIT License.

## 🎉 Get Started Now!

```bash
# Quick start command
python start_gateway.py
```

Your UPI Gateway wrapper is now ready to process payments! 🚀

---

**📧 Need help?** Contact support or check the documentation at http://localhost:5000/api/docs

**🌟 Like this project?** Star it and share with other developers!

**🐛 Found a bug?** Create an issue and we'll fix it!