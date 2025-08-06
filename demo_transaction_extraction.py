#!/usr/bin/env python3
"""
Demo: How to Extract Transaction Data from Kamlai Multi Service
Complete examples for accessing merchant transaction data
"""

import requests
import json
import hmac
import hashlib
import sqlite3
import pandas as pd
from datetime import datetime

def demo_dashboard_access():
    """
    Demo 1: How to access transaction data via Web Dashboard
    """
    print("🌐 DEMO 1: Web Dashboard Access")
    print("=" * 50)
    print("1. Open browser: http://localhost:5000")
    print("2. Click 'Get Started' to register a merchant account")
    print("3. Fill registration form with your business details")
    print("4. Login with your credentials")
    print("5. Go to Dashboard to see transaction overview")
    print("6. Click 'View All Transactions' for detailed list")
    print("7. Use filters to search by status, date, amount")
    print("8. Export data as CSV from the dashboard")
    print()

def demo_direct_database_access():
    """
    Demo 2: Direct database access for transaction data
    """
    print("🗄️ DEMO 2: Direct Database Access")
    print("=" * 50)
    
    try:
        # Check if database exists
        conn = sqlite3.connect('upi_gateway.db')
        
        # Get merchant information
        merchants_query = "SELECT id, merchant_id, business_name, email FROM merchant"
        merchants_df = pd.read_sql_query(merchants_query, conn)
        
        print(f"📊 Found {len(merchants_df)} merchants:")
        print(merchants_df.to_string(index=False))
        print()
        
        # Get transaction data
        transactions_query = """
        SELECT 
            t.transaction_id,
            m.business_name,
            t.customer_name,
            t.amount,
            t.status,
            t.created_at
        FROM transaction t
        JOIN merchant m ON t.merchant_id = m.id
        ORDER BY t.created_at DESC
        LIMIT 10
        """
        
        transactions_df = pd.read_sql_query(transactions_query, conn)
        
        if len(transactions_df) > 0:
            print(f"💳 Recent {len(transactions_df)} transactions:")
            print(transactions_df.to_string(index=False))
        else:
            print("📝 No transactions found. Create some test transactions first!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database access failed: {e}")
        print("💡 Make sure the server has been started at least once to create the database")
    print()

def demo_api_access():
    """
    Demo 3: API access for transaction data
    """
    print("🔌 DEMO 3: API Access")
    print("=" * 50)
    
    # You need to get these from your merchant dashboard
    print("🔑 To use API access, you need:")
    print("1. Register/Login to get API credentials from dashboard")
    print("2. Copy API Key and API Secret from 'API Keys' section")
    print("3. Use the credentials in your API calls")
    print()
    
    # Example API calls (you need to replace with actual credentials)
    api_key = "your_api_key_here"
    api_secret = "your_api_secret_here"
    
    print("📡 Available API endpoints:")
    print("• GET /api/transactions - Get all transactions")
    print("• GET /api/transactions?status=SUCCESS - Filter by status")
    print("• GET /api/transactions/export?format=csv - Export as CSV")
    print("• GET /api/transactions/stats - Get statistics")
    print()
    
    print("💻 Example API call code:")
    example_code = '''
import requests
import json
import hmac
import hashlib

def get_transactions(api_key, api_secret):
    url = "http://localhost:5000/api/transactions"
    
    # Generate signature
    signature = hmac.new(
        api_secret.encode('utf-8'),
        b'',
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        'X-API-Key': api_key,
        'X-Signature': signature,
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    return response.json()

# Usage
# result = get_transactions("your_api_key", "your_api_secret")
# print(result)
    '''
    print(example_code)

def demo_using_extraction_tool():
    """
    Demo 4: Using the extraction tool we created
    """
    print("🛠️ DEMO 4: Using Extract Transaction Data Tool")
    print("=" * 50)
    
    print("1. Run the extraction tool:")
    print("   python extract_transaction_data.py")
    print()
    
    print("2. Or use it programmatically:")
    
    try:
        # Import our extraction functions
        import sys
        sys.path.append('.')
        from extract_transaction_data import extract_all_transaction_data, get_merchant_transactions
        
        print("📊 Extracting all transaction data...")
        df = extract_all_transaction_data()
        
        if df is not None and len(df) > 0:
            print(f"✅ Successfully extracted {len(df)} transactions")
            print("\n📈 Sample data:")
            print(df[['transaction_id', 'customer_name', 'amount', 'status', 'created_at']].head())
        else:
            print("📝 No transaction data found")
            
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        print("💡 Make sure extract_transaction_data.py is in the same directory")
    print()

def demo_create_sample_transaction():
    """
    Demo 5: Create sample transaction for testing
    """
    print("🧪 DEMO 5: Create Sample Transaction for Testing")
    print("=" * 50)
    
    print("To create sample transactions for testing:")
    print()
    print("1. Go to dashboard: http://localhost:5000/dashboard")
    print("2. Click 'Create Test Payment' button")
    print("3. Fill in test customer details:")
    print("   - Amount: 100.00")
    print("   - Customer Name: Test Customer")
    print("   - Email: test@example.com")
    print("   - Redirect URL: http://localhost:5000/dashboard")
    print("4. Click 'Create Payment'")
    print("5. This will create a test transaction in PENDING status")
    print("6. You can then extract this data using any of the above methods")
    print()

def main():
    """
    Main demo function
    """
    print("🎯 KAMLAI MULTI SERVICE - Transaction Data Extraction Demo")
    print("=" * 60)
    print("This demo shows you all the ways to access transaction data from merchant accounts")
    print("=" * 60)
    print()
    
    # Run all demos
    demo_dashboard_access()
    demo_direct_database_access()
    demo_api_access()
    demo_using_extraction_tool()
    demo_create_sample_transaction()
    
    print("🎉 DEMO COMPLETED!")
    print("=" * 60)
    print("Next Steps:")
    print("1. Start the server: python upi_gateway_app.py")
    print("2. Register a merchant account")
    print("3. Create some test transactions")
    print("4. Use any of the extraction methods shown above")
    print("5. Export your data as CSV/Excel for analysis")
    print()
    print("💡 For production use, remember to:")
    print("• Set up proper database backups")
    print("• Use environment variables for API keys")
    print("• Implement proper authentication and authorization")
    print("• Add rate limiting for API endpoints")

if __name__ == '__main__':
    main()