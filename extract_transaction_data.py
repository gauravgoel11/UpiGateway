#!/usr/bin/env python3
"""
Kamlai Multi Service - Transaction Data Extraction Tool
Complete methods to extract transaction data from merchant accounts
"""

import requests
import json
import hmac
import hashlib
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import csv

class TransactionDataExtractor:
    """
    Complete transaction data extraction tool for Kamlai Multi Service
    """
    
    def __init__(self, api_key=None, api_secret=None, base_url="http://localhost:5000"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api"
        
    def _generate_signature(self, data=""):
        """Generate HMAC signature for API authentication"""
        payload = json.dumps(data, sort_keys=True) if isinstance(data, dict) else str(data)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_authenticated_request(self, method, endpoint, data=None):
        """Make authenticated API request"""
        url = f"{self.api_base}{endpoint}"
        
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        }
        
        if data:
            headers['X-Signature'] = self._generate_signature(data)
        else:
            headers['X-Signature'] = self._generate_signature("")
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            
            return response
        except requests.RequestException as e:
            raise Exception(f"API request failed: {e}")

# ================================
# METHOD 1: Direct Database Access
# ================================

def extract_from_database(db_path="upi_gateway.db"):
    """
    Method 1: Extract transaction data directly from SQLite database
    This is the fastest method for local access
    """
    try:
        conn = sqlite3.connect(db_path)
        
        # Get all transactions with merchant details
        query = """
        SELECT 
            t.id,
            t.transaction_id,
            t.merchant_id,
            m.business_name,
            m.email as merchant_email,
            t.customer_name,
            t.customer_email,
            t.customer_phone,
            t.amount,
            t.currency,
            t.status,
            t.payment_method,
            t.upi_id,
            t.payment_gateway_txn_id,
            t.webhook_sent,
            t.failure_reason,
            t.created_at,
            t.updated_at,
            t.ip_address,
            t.redirect_url
        FROM transaction t
        JOIN merchant m ON t.merchant_id = m.id
        ORDER BY t.created_at DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"✅ Extracted {len(df)} transactions from database")
        return df
        
    except Exception as e:
        print(f"❌ Database extraction failed: {e}")
        return None

def get_merchant_transactions(merchant_id, db_path="upi_gateway.db"):
    """
    Get transactions for a specific merchant
    """
    try:
        conn = sqlite3.connect(db_path)
        
        query = """
        SELECT * FROM transaction 
        WHERE merchant_id = ? 
        ORDER BY created_at DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(merchant_id,))
        conn.close()
        
        print(f"✅ Found {len(df)} transactions for merchant {merchant_id}")
        return df
        
    except Exception as e:
        print(f"❌ Failed to get merchant transactions: {e}")
        return None

def get_transactions_by_status(status, db_path="upi_gateway.db"):
    """
    Get transactions filtered by status (SUCCESS, PENDING, FAILED)
    """
    try:
        conn = sqlite3.connect(db_path)
        
        query = """
        SELECT t.*, m.business_name, m.email as merchant_email
        FROM transaction t
        JOIN merchant m ON t.merchant_id = m.id
        WHERE t.status = ?
        ORDER BY t.created_at DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(status,))
        conn.close()
        
        print(f"✅ Found {len(df)} {status} transactions")
        return df
        
    except Exception as e:
        print(f"❌ Failed to get transactions by status: {e}")
        return None

def get_transactions_by_date_range(start_date, end_date, db_path="upi_gateway.db"):
    """
    Get transactions within a date range
    """
    try:
        conn = sqlite3.connect(db_path)
        
        query = """
        SELECT t.*, m.business_name, m.email as merchant_email
        FROM transaction t
        JOIN merchant m ON t.merchant_id = m.id
        WHERE DATE(t.created_at) BETWEEN ? AND ?
        ORDER BY t.created_at DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        
        print(f"✅ Found {len(df)} transactions between {start_date} and {end_date}")
        return df
        
    except Exception as e:
        print(f"❌ Failed to get transactions by date range: {e}")
        return None

# ================================
# METHOD 2: API-based Extraction
# ================================

def extract_via_api(api_key, api_secret, base_url="http://localhost:5000"):
    """
    Method 2: Extract transaction data via API
    This method works remotely and respects authentication
    """
    try:
        extractor = TransactionDataExtractor(api_key, api_secret, base_url)
        
        # Note: You would need to add a transactions list endpoint to your API
        # For now, this shows the structure
        
        print("📡 API-based extraction would require additional endpoints")
        print("💡 Consider adding these endpoints to upi_gateway_app.py:")
        print("   - GET /api/transactions")
        print("   - GET /api/transactions/merchant/{merchant_id}")
        print("   - GET /api/transactions/status/{status}")
        
        return None
        
    except Exception as e:
        print(f"❌ API extraction failed: {e}")
        return None

# ================================
# METHOD 3: Export Functions
# ================================

def export_to_csv(df, filename=None):
    """
    Export transaction data to CSV file
    """
    if df is None or df.empty:
        print("❌ No data to export")
        return
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transactions_export_{timestamp}.csv"
    
    try:
        df.to_csv(filename, index=False)
        print(f"✅ Exported {len(df)} transactions to {filename}")
        return filename
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return None

def export_to_excel(df, filename=None):
    """
    Export transaction data to Excel file
    """
    if df is None or df.empty:
        print("❌ No data to export")
        return
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transactions_export_{timestamp}.xlsx"
    
    try:
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"✅ Exported {len(df)} transactions to {filename}")
        return filename
    except Exception as e:
        print(f"❌ Excel export failed: {e}")
        print("💡 Install openpyxl: pip install openpyxl")
        return None

def generate_transaction_report(df):
    """
    Generate summary report of transaction data
    """
    if df is None or df.empty:
        print("❌ No data for report")
        return
    
    print("\n" + "="*60)
    print("📊 TRANSACTION DATA REPORT")
    print("="*60)
    
    # Basic stats
    print(f"📈 Total Transactions: {len(df)}")
    print(f"💰 Total Amount: ₹{df['amount'].sum():,.2f}")
    print(f"📅 Date Range: {df['created_at'].min()} to {df['created_at'].max()}")
    
    # Status breakdown
    print("\n📊 Status Breakdown:")
    status_counts = df['status'].value_counts()
    for status, count in status_counts.items():
        percentage = (count / len(df)) * 100
        print(f"   {status}: {count} ({percentage:.1f}%)")
    
    # Top merchants
    if 'business_name' in df.columns:
        print("\n🏢 Top Merchants:")
        merchant_stats = df.groupby('business_name').agg({
            'transaction_id': 'count',
            'amount': 'sum'
        }).round(2)
        merchant_stats.columns = ['Transactions', 'Total Amount']
        print(merchant_stats.head())
    
    # Daily transaction volume
    print("\n📈 Recent Daily Volume:")
    df['date'] = pd.to_datetime(df['created_at']).dt.date
    daily_stats = df.groupby('date').agg({
        'transaction_id': 'count',
        'amount': 'sum'
    }).round(2)
    daily_stats.columns = ['Transactions', 'Amount']
    print(daily_stats.tail())

# ================================
# MAIN EXTRACTION FUNCTIONS
# ================================

def extract_all_transaction_data():
    """
    Main function to extract all transaction data using the best available method
    """
    print("🚀 Starting Transaction Data Extraction...")
    print("="*50)
    
    # Method 1: Try database extraction first (fastest)
    print("\n1️⃣ Trying database extraction...")
    df = extract_from_database()
    
    if df is not None and not df.empty:
        print(f"✅ Successfully extracted {len(df)} transactions")
        
        # Generate report
        generate_transaction_report(df)
        
        # Export options
        print("\n📤 Export Options:")
        csv_file = export_to_csv(df)
        
        try:
            excel_file = export_to_excel(df)
        except:
            print("💡 For Excel export, install: pip install openpyxl")
        
        return df
    else:
        print("❌ No transaction data found")
        return None

def extract_merchant_specific_data(merchant_id):
    """
    Extract data for a specific merchant
    """
    print(f"🔍 Extracting data for merchant ID: {merchant_id}")
    
    df = get_merchant_transactions(merchant_id)
    
    if df is not None and not df.empty:
        generate_transaction_report(df)
        return df
    else:
        print("❌ No transactions found for this merchant")
        return None

def extract_by_filters(status=None, start_date=None, end_date=None):
    """
    Extract data with specific filters
    """
    print("🔍 Extracting filtered transaction data...")
    
    if status:
        df = get_transactions_by_status(status)
    elif start_date and end_date:
        df = get_transactions_by_date_range(start_date, end_date)
    else:
        df = extract_from_database()
    
    if df is not None and not df.empty:
        generate_transaction_report(df)
        return df
    else:
        print("❌ No transactions found with specified filters")
        return None

# ================================
# EXAMPLE USAGE
# ================================

def main():
    """
    Example usage of transaction data extraction
    """
    print("🎯 Kamlai Multi Service - Transaction Data Extractor")
    print("="*60)
    
    # Example 1: Extract all transaction data
    print("\n📊 EXAMPLE 1: Extract All Transaction Data")
    all_transactions = extract_all_transaction_data()
    
    # Example 2: Extract for specific merchant
    print("\n📊 EXAMPLE 2: Extract for Specific Merchant")
    # Replace with actual merchant ID from your database
    merchant_data = extract_merchant_specific_data(1)
    
    # Example 3: Extract successful transactions only
    print("\n📊 EXAMPLE 3: Extract Successful Transactions")
    successful_transactions = extract_by_filters(status="SUCCESS")
    
    # Example 4: Extract transactions from last 7 days
    print("\n📊 EXAMPLE 4: Extract Recent Transactions")
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    recent_transactions = extract_by_filters(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    )
    
    print("\n✅ Transaction data extraction completed!")
    print("📁 Check your directory for exported CSV/Excel files")

if __name__ == '__main__':
    main()