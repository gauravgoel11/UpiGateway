#!/usr/bin/env python3
"""
UPI Gateway Integration Examples
Complete examples for integrating with the UPI Gateway API
"""

import requests
import json
import hmac
import hashlib
import time
from datetime import datetime
import secrets

class UPIGatewayClient:
    """
    Official UPI Gateway Python Client
    Use this class to integrate with your UPI Gateway instance
    """
    
    def __init__(self, api_key, api_secret, base_url="http://localhost:5000"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api"
    
    def _generate_signature(self, data):
        """Generate HMAC signature for API authentication"""
        payload = json.dumps(data, sort_keys=True) if isinstance(data, dict) else str(data)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, method, endpoint, data=None):
        """Make authenticated API request"""
        url = f"{self.api_base}{endpoint}"
        
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        }
        
        if data:
            headers['X-Signature'] = self._generate_signature(data)
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return response
        except requests.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    def create_payment(self, amount, customer_name, customer_email, 
                      redirect_url, customer_phone=None):
        """
        Create a new payment request
        
        Args:
            amount (float): Payment amount in INR
            customer_name (str): Customer's full name
            customer_email (str): Customer's email address
            redirect_url (str): URL to redirect after payment
            customer_phone (str, optional): Customer's phone number
        
        Returns:
            dict: Payment creation response
        """
        data = {
            'amount': float(amount),
            'customer_name': customer_name,
            'customer_email': customer_email,
            'redirect_url': redirect_url
        }
        
        if customer_phone:
            data['customer_phone'] = customer_phone
        
        response = self._make_request('POST', '/payment/create', data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Payment creation failed: {response.text}")
    
    def check_payment_status(self, transaction_id):
        """
        Check the status of a payment transaction
        
        Args:
            transaction_id (str): Transaction ID to check
        
        Returns:
            dict: Payment status response
        """
        response = self._make_request('GET', f'/payment/status/{transaction_id}')
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Status check failed: {response.text}")
    
    def wait_for_payment(self, transaction_id, timeout=300, poll_interval=5):
        """
        Wait for payment completion with polling
        
        Args:
            transaction_id (str): Transaction ID to monitor
            timeout (int): Maximum wait time in seconds (default: 5 minutes)
            poll_interval (int): Polling interval in seconds (default: 5 seconds)
        
        Returns:
            dict: Final payment status
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                status_response = self.check_payment_status(transaction_id)
                
                if status_response['success']:
                    payment_status = status_response['status']
                    
                    if payment_status in ['SUCCESS', 'FAILED', 'CANCELLED']:
                        return status_response
                    
                    print(f"Payment {transaction_id} is {payment_status}, waiting...")
                    time.sleep(poll_interval)
                else:
                    raise Exception(f"Status check failed: {status_response}")
                    
            except Exception as e:
                print(f"Error checking status: {e}")
                time.sleep(poll_interval)
        
        raise Exception(f"Payment timeout after {timeout} seconds")

# Example Usage Functions

def example_simple_payment():
    """Example 1: Simple payment creation"""
    print("🔹 Example 1: Simple Payment Creation")
    print("-" * 40)
    
    # Initialize client with your credentials
    client = UPIGatewayClient(
        api_key="your_api_key_here",
        api_secret="your_api_secret_here",
        base_url="http://localhost:5000"
    )
    
    try:
        # Create a payment request
        result = client.create_payment(
            amount=150.00,
            customer_name="John Doe",
            customer_email="john@example.com",
            redirect_url="https://yoursite.com/payment-success",
            customer_phone="+91-9876543210"
        )
        
        if result['success']:
            print(f"✅ Payment created successfully!")
            print(f"   Transaction ID: {result['transaction_id']}")
            print(f"   Payment URL: {result['payment_url']}")
            print(f"   QR Data: {result['qr_data']}")
        else:
            print(f"❌ Payment creation failed: {result['error']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def example_payment_with_monitoring():
    """Example 2: Payment with status monitoring"""
    print("\n🔹 Example 2: Payment with Status Monitoring")
    print("-" * 40)
    
    client = UPIGatewayClient(
        api_key="your_api_key_here",
        api_secret="your_api_secret_here"
    )
    
    try:
        # Create payment
        result = client.create_payment(
            amount=250.00,
            customer_name="Jane Smith",
            customer_email="jane@example.com",
            redirect_url="https://yoursite.com/success"
        )
        
        if result['success']:
            transaction_id = result['transaction_id']
            print(f"✅ Payment created: {transaction_id}")
            
            # Monitor payment status
            print("⏳ Waiting for payment completion...")
            final_status = client.wait_for_payment(
                transaction_id=transaction_id,
                timeout=300,  # 5 minutes
                poll_interval=10  # Check every 10 seconds
            )
            
            print(f"🎯 Final Status: {final_status['status']}")
            if final_status['status'] == 'SUCCESS':
                print("💚 Payment successful!")
            else:
                print("❌ Payment failed or cancelled")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def example_bulk_payments():
    """Example 3: Creating multiple payments"""
    print("\n🔹 Example 3: Bulk Payment Creation")
    print("-" * 40)
    
    client = UPIGatewayClient(
        api_key="your_api_key_here",
        api_secret="your_api_secret_here"
    )
    
    # Sample payment data
    payments = [
        {
            'amount': 100.00,
            'customer_name': 'Customer 1',
            'customer_email': 'customer1@example.com',
            'redirect_url': 'https://example.com/success'
        },
        {
            'amount': 200.00,
            'customer_name': 'Customer 2', 
            'customer_email': 'customer2@example.com',
            'redirect_url': 'https://example.com/success'
        },
        {
            'amount': 300.00,
            'customer_name': 'Customer 3',
            'customer_email': 'customer3@example.com',
            'redirect_url': 'https://example.com/success'
        }
    ]
    
    created_payments = []
    
    for i, payment_data in enumerate(payments, 1):
        try:
            result = client.create_payment(**payment_data)
            
            if result['success']:
                created_payments.append(result)
                print(f"✅ Payment {i} created: {result['transaction_id']}")
            else:
                print(f"❌ Payment {i} failed: {result['error']}")
                
        except Exception as e:
            print(f"❌ Payment {i} error: {e}")
    
    print(f"\n📊 Summary: {len(created_payments)}/{len(payments)} payments created successfully")
    
    # Monitor all payments
    if created_payments:
        print("\n⏳ Monitoring all payments...")
        for payment in created_payments:
            try:
                status = client.check_payment_status(payment['transaction_id'])
                print(f"   {payment['transaction_id']}: {status['status']}")
            except Exception as e:
                print(f"   {payment['transaction_id']}: Error - {e}")

def example_webhook_handler():
    """Example 4: Webhook handler for payment notifications"""
    print("\n🔹 Example 4: Webhook Handler")
    print("-" * 40)
    
    # This is how you would handle webhooks in your Flask/Django app
    webhook_example = '''
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

@app.route('/webhook/payment', methods=['POST'])
def handle_payment_webhook():
    """Handle payment status webhooks from UPI Gateway"""
    try:
        # Get webhook data
        data = request.get_json()
        
        # Verify webhook signature (if you implement webhook signing)
        # signature = request.headers.get('X-Webhook-Signature')
        # if not verify_webhook_signature(data, signature):
        #     return jsonify({'error': 'Invalid signature'}), 401
        
        transaction_id = data.get('transaction_id')
        status = data.get('status')
        amount = data.get('amount')
        customer_email = data.get('customer_email')
        
        print(f"Received webhook for {transaction_id}: {status}")
        
        # Update your database
        if status == 'SUCCESS':
            # Handle successful payment
            print(f"Payment successful: ₹{amount} from {customer_email}")
            # Send confirmation email, update order status, etc.
            
        elif status == 'FAILED':
            # Handle failed payment
            print(f"Payment failed: {transaction_id}")
            # Notify customer, retry payment, etc.
            
        elif status == 'CANCELLED':
            # Handle cancelled payment
            print(f"Payment cancelled: {transaction_id}")
            
        return jsonify({'status': 'success'})
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=8080)  # Your webhook endpoint
    '''
    
    print("Sample webhook handler code:")
    print(webhook_example)

def example_e_commerce_integration():
    """Example 5: E-commerce checkout integration"""
    print("\n🔹 Example 5: E-commerce Checkout Integration")
    print("-" * 40)
    
    # Simulate e-commerce checkout flow
    class ECommerceCheckout:
        def __init__(self, upi_client):
            self.upi_client = upi_client
        
        def process_checkout(self, cart_items, customer_info):
            """Process e-commerce checkout with UPI Gateway"""
            try:
                # Calculate total amount
                total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
                
                print(f"🛒 Processing checkout for {customer_info['name']}")
                print(f"   Total Amount: ₹{total_amount}")
                print(f"   Items: {len(cart_items)}")
                
                # Create payment request
                payment_result = self.upi_client.create_payment(
                    amount=total_amount,
                    customer_name=customer_info['name'],
                    customer_email=customer_info['email'],
                    redirect_url=f"https://mystore.com/order-confirmation",
                    customer_phone=customer_info.get('phone')
                )
                
                if payment_result['success']:
                    print(f"✅ Payment request created: {payment_result['transaction_id']}")
                    print(f"🔗 Payment URL: {payment_result['payment_url']}")
                    
                    # In a real app, you would:
                    # 1. Save order to database with PENDING status
                    # 2. Redirect customer to payment URL
                    # 3. Handle webhook to update order status
                    
                    return payment_result
                else:
                    raise Exception(f"Payment creation failed: {payment_result['error']}")
                    
            except Exception as e:
                print(f"❌ Checkout failed: {e}")
                return None
    
    # Example usage
    client = UPIGatewayClient(
        api_key="your_api_key_here",
        api_secret="your_api_secret_here"
    )
    
    checkout = ECommerceCheckout(client)
    
    # Sample cart and customer data
    cart_items = [
        {'name': 'Product 1', 'price': 100.00, 'quantity': 2},
        {'name': 'Product 2', 'price': 50.00, 'quantity': 1}
    ]
    
    customer_info = {
        'name': 'Alice Johnson',
        'email': 'alice@example.com',
        'phone': '+91-9876543210'
    }
    
    result = checkout.process_checkout(cart_items, customer_info)
    if result:
        print("🎯 Checkout completed successfully!")

def main():
    """Run all examples"""
    print("🚀 UPI Gateway Integration Examples")
    print("=" * 50)
    print("Note: Update API credentials before running examples")
    print("=" * 50)
    
    # Run examples
    example_simple_payment()
    example_payment_with_monitoring()
    example_bulk_payments()
    example_webhook_handler()
    example_e_commerce_integration()
    
    print("\n" + "=" * 50)
    print("✅ All examples completed!")
    print("📚 For more information, visit: http://localhost:5000/api/docs")

if __name__ == '__main__':
    main()