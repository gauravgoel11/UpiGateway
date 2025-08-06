#!/usr/bin/env python3
"""
Kamlai Multi Service - Complete Merchant Solution (2025)
Similar to UPIGateway.com - Merchant Transaction Tracking System
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import hashlib
import hmac
import base64
import requests
import uuid
import json
import os
from urllib.parse import urlencode
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///upi_gateway.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ================================
# Database Models
# ================================

class Merchant(UserMixin, db.Model):
    """Merchant account model"""
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    business_name = db.Column(db.String(200), nullable=False)
    api_key = db.Column(db.String(100), unique=True, nullable=False)
    api_secret = db.Column(db.String(100), unique=True, nullable=False)
    webhook_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='merchant', lazy=True)

class Transaction(db.Model):
    """Transaction model for tracking all payments"""
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id'), nullable=False)
    customer_name = db.Column(db.String(200))
    customer_email = db.Column(db.String(120))
    customer_phone = db.Column(db.String(15))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='INR')
    status = db.Column(db.String(20), default='PENDING')  # PENDING, SUCCESS, FAILED, CANCELLED
    payment_method = db.Column(db.String(50))  # UPI, CARD, NETBANKING
    upi_id = db.Column(db.String(100))
    payment_gateway_txn_id = db.Column(db.String(200))
    qr_code_data = db.Column(db.Text)
    webhook_sent = db.Column(db.Boolean, default=False)
    failure_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional tracking fields
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    redirect_url = db.Column(db.String(500))

class APILog(db.Model):
    """API request logging for debugging"""
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id'))
    endpoint = db.Column(db.String(200), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    request_data = db.Column(db.Text)
    response_data = db.Column(db.Text)
    status_code = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return Merchant.query.get(int(user_id))

# ================================
# UPI Gateway Service Classes
# ================================

class UPIGatewayService:
    """Main UPI Gateway service for processing payments"""
    
    def __init__(self):
        self.base_url = "https://api.phonepe.com/apis"
        self.sandbox_url = "https://api-preprod.phonepe.com/apis/pg-sandbox"
        self.use_sandbox = True  # Set to False for production
        
    def generate_dynamic_qr(self, amount, merchant_vpa, transaction_id, customer_name=None):
        """Generate dynamic QR code for UPI payments"""
        try:
            # UPI payment URL format
            upi_url = f"upi://pay?pa={merchant_vpa}&pn={customer_name or 'Customer'}&am={amount}&cu=INR&tn={transaction_id}"
            
            # You can integrate with QR code generation library here
            # For now, returning the UPI URL
            return {
                'success': True,
                'qr_data': upi_url,
                'qr_string': upi_url
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment_status(self, transaction_id):
        """Verify payment status with actual payment gateway"""
        try:
            # This would integrate with actual UPI payment verification APIs
            # For demo purposes, simulating random status
            import random
            statuses = ['SUCCESS', 'PENDING', 'FAILED']
            
            return {
                'success': True,
                'status': random.choice(statuses),
                'transaction_id': transaction_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_payment_request(self, merchant, amount, customer_info, redirect_url):
        """Create a new payment request"""
        try:
            transaction_id = f"TXN_{int(datetime.utcnow().timestamp())}_{secrets.token_hex(4)}"
            
            # Create transaction record
            transaction = Transaction(
                transaction_id=transaction_id,
                merchant_id=merchant.id,
                customer_name=customer_info.get('name'),
                customer_email=customer_info.get('email'), 
                customer_phone=customer_info.get('phone'),
                amount=float(amount),
                redirect_url=redirect_url,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            # Generate QR code
            qr_result = self.generate_dynamic_qr(
                amount=amount,
                merchant_vpa=f"{merchant.merchant_id}@paytm",  # Default VPA
                transaction_id=transaction_id,
                customer_name=customer_info.get('name')
            )
            
            if qr_result['success']:
                transaction.qr_code_data = qr_result['qr_data']
                db.session.commit()
                
                return {
                    'success': True,
                    'transaction_id': transaction_id,
                    'qr_data': qr_result['qr_data'],
                    'payment_url': f"{request.host_url}payment/{transaction_id}"
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to generate QR code'
                }
                
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }

# ================================
# Authentication Utilities
# ================================

def verify_api_signature(api_key, api_secret, data, signature):
    """Verify API request signature"""
    try:
        payload = json.dumps(data, sort_keys=True) if isinstance(data, dict) else str(data)
        expected_signature = hmac.new(
            api_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception:
        return False

def authenticate_api_request():
    """Decorator for API authentication"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            signature = request.headers.get('X-Signature')
            
            if not api_key or not signature:
                return jsonify({'error': 'Missing API credentials'}), 401
            
            merchant = Merchant.query.filter_by(api_key=api_key, is_active=True).first()
            if not merchant:
                return jsonify({'error': 'Invalid API key'}), 401
            
            # Verify signature
            request_data = request.get_json() or {}
            if not verify_api_signature(api_key, merchant.api_secret, request_data, signature):
                return jsonify({'error': 'Invalid signature'}), 401
            
            # Log API request
            log_entry = APILog(
                merchant_id=merchant.id,
                endpoint=request.endpoint,
                method=request.method,
                request_data=json.dumps(request_data),
                status_code=200
            )
            db.session.add(log_entry)
            db.session.commit()
            
            return f(merchant, *args, **kwargs)
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

# ================================
# Web Routes (Merchant Dashboard)
# ================================

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Merchant registration"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        email = data.get('email')
        password = data.get('password')
        business_name = data.get('business_name')
        
        if Merchant.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Generate merchant credentials
        merchant_id = f"MERCHANT_{int(datetime.utcnow().timestamp())}"
        api_key = secrets.token_urlsafe(32)
        api_secret = secrets.token_urlsafe(64)
        
        merchant = Merchant(
            merchant_id=merchant_id,
            email=email,
            password_hash=generate_password_hash(password),
            business_name=business_name,
            api_key=api_key,
            api_secret=api_secret
        )
        
        db.session.add(merchant)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'merchant_id': merchant_id,
            'api_key': api_key,
            'api_secret': api_secret
        })
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Merchant login"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        email = data.get('email')
        password = data.get('password')
        
        merchant = Merchant.query.filter_by(email=email).first()
        
        if merchant and check_password_hash(merchant.password_hash, password):
            login_user(merchant)
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('dashboard')})
            return redirect(url_for('dashboard'))
        
        error = 'Invalid email or password'
        if request.is_json:
            return jsonify({'error': error}), 401
        flash(error, 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Merchant logout"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Merchant dashboard"""
    # Get recent transactions
    recent_transactions = Transaction.query.filter_by(
        merchant_id=current_user.id
    ).order_by(Transaction.created_at.desc()).limit(10).all()
    
    # Calculate stats
    total_transactions = Transaction.query.filter_by(merchant_id=current_user.id).count()
    successful_transactions = Transaction.query.filter_by(
        merchant_id=current_user.id, 
        status='SUCCESS'
    ).count()
    
    total_amount = db.session.query(db.func.sum(Transaction.amount)).filter_by(
        merchant_id=current_user.id,
        status='SUCCESS'
    ).scalar() or 0
    
    stats = {
        'total_transactions': total_transactions,
        'successful_transactions': successful_transactions,
        'success_rate': (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0,
        'total_amount': total_amount
    }
    
    return render_template('dashboard.html', 
                         transactions=recent_transactions, 
                         stats=stats,
                         merchant=current_user)

@app.route('/transactions')
@login_required
def transactions():
    """Transaction history page"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Transaction.query.filter_by(merchant_id=current_user.id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    transactions = query.order_by(Transaction.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('transactions.html', transactions=transactions)

# ================================
# API Routes (for integration)
# ================================

@app.route('/api/payment/create', methods=['POST'])
@authenticate_api_request()
def create_payment(merchant):
    """API endpoint to create payment request"""
    try:
        data = request.get_json()
        
        required_fields = ['amount', 'customer_name', 'customer_email', 'redirect_url']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({'error': 'Amount must be greater than 0'}), 400
        
        customer_info = {
            'name': data['customer_name'],
            'email': data['customer_email'],
            'phone': data.get('customer_phone', '')
        }
        
        gateway_service = UPIGatewayService()
        result = gateway_service.create_payment_request(
            merchant=merchant,
            amount=amount,
            customer_info=customer_info,
            redirect_url=data['redirect_url']
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'transaction_id': result['transaction_id'],
                'payment_url': result['payment_url'],
                'qr_data': result['qr_data']
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payment/status/<transaction_id>', methods=['GET'])
@authenticate_api_request()
def payment_status(merchant, transaction_id):
    """API endpoint to check payment status"""
    try:
        transaction = Transaction.query.filter_by(
            transaction_id=transaction_id,
            merchant_id=merchant.id
        ).first()
        
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        # Verify with gateway if status is still pending
        if transaction.status == 'PENDING':
            gateway_service = UPIGatewayService()
            status_result = gateway_service.verify_payment_status(transaction_id)
            
            if status_result['success'] and status_result['status'] != 'PENDING':
                transaction.status = status_result['status']
                transaction.updated_at = datetime.utcnow()
                db.session.commit()
        
        return jsonify({
            'success': True,
            'transaction_id': transaction.transaction_id,
            'status': transaction.status,
            'amount': transaction.amount,
            'created_at': transaction.created_at.isoformat(),
            'updated_at': transaction.updated_at.isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/payment/<transaction_id>')
def payment_page(transaction_id):
    """Customer payment page"""
    transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
    
    if not transaction:
        return render_template('error.html', error='Transaction not found'), 404
    
    if transaction.status != 'PENDING':
        return render_template('payment_complete.html', transaction=transaction)
    
    return render_template('payment_page.html', transaction=transaction)

@app.route('/api/transactions', methods=['GET'])
@authenticate_api_request()
def get_transactions(merchant):
    """API endpoint to get all transactions for authenticated merchant"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status', '')
        
        query = Transaction.query.filter_by(merchant_id=merchant.id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        transactions = query.order_by(Transaction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Convert to JSON serializable format
        transaction_list = []
        for txn in transactions.items:
            transaction_list.append({
                'transaction_id': txn.transaction_id,
                'customer_name': txn.customer_name,
                'customer_email': txn.customer_email,
                'customer_phone': txn.customer_phone,
                'amount': txn.amount,
                'currency': txn.currency,
                'status': txn.status,
                'payment_method': txn.payment_method,
                'upi_id': txn.upi_id,
                'payment_gateway_txn_id': txn.payment_gateway_txn_id,
                'webhook_sent': txn.webhook_sent,
                'failure_reason': txn.failure_reason,
                'created_at': txn.created_at.isoformat(),
                'updated_at': txn.updated_at.isoformat(),
                'ip_address': txn.ip_address,
                'redirect_url': txn.redirect_url
            })
        
        return jsonify({
            'success': True,
            'transactions': transaction_list,
            'pagination': {
                'page': transactions.page,
                'pages': transactions.pages,
                'per_page': transactions.per_page,
                'total': transactions.total,
                'has_next': transactions.has_next,
                'has_prev': transactions.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions/export', methods=['GET'])
@authenticate_api_request()
def export_transactions(merchant):
    """API endpoint to export transactions as CSV"""
    try:
        format_type = request.args.get('format', 'csv')  # csv or json
        status_filter = request.args.get('status', '')
        
        query = Transaction.query.filter_by(merchant_id=merchant.id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        transactions = query.order_by(Transaction.created_at.desc()).all()
        
        if format_type == 'csv':
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Transaction ID', 'Customer Name', 'Customer Email', 'Customer Phone',
                'Amount', 'Currency', 'Status', 'Payment Method', 'UPI ID',
                'Gateway Transaction ID', 'Webhook Sent', 'Failure Reason',
                'Created At', 'Updated At', 'IP Address', 'Redirect URL'
            ])
            
            # Write data
            for txn in transactions:
                writer.writerow([
                    txn.transaction_id, txn.customer_name, txn.customer_email, txn.customer_phone,
                    txn.amount, txn.currency, txn.status, txn.payment_method, txn.upi_id,
                    txn.payment_gateway_txn_id, txn.webhook_sent, txn.failure_reason,
                    txn.created_at.isoformat(), txn.updated_at.isoformat(), txn.ip_address, txn.redirect_url
                ])
            
            csv_data = output.getvalue()
            output.close()
            
            from flask import Response
            return Response(
                csv_data,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=transactions_export_{merchant.merchant_id}.csv'}
            )
        
        else:  # JSON format
            transaction_list = []
            for txn in transactions:
                transaction_list.append({
                    'transaction_id': txn.transaction_id,
                    'customer_name': txn.customer_name,
                    'customer_email': txn.customer_email,
                    'customer_phone': txn.customer_phone,
                    'amount': txn.amount,
                    'currency': txn.currency,
                    'status': txn.status,
                    'payment_method': txn.payment_method,
                    'upi_id': txn.upi_id,
                    'payment_gateway_txn_id': txn.payment_gateway_txn_id,
                    'webhook_sent': txn.webhook_sent,
                    'failure_reason': txn.failure_reason,
                    'created_at': txn.created_at.isoformat(),
                    'updated_at': txn.updated_at.isoformat(),
                    'ip_address': txn.ip_address,
                    'redirect_url': txn.redirect_url
                })
            
            return jsonify({
                'success': True,
                'transactions': transaction_list,
                'total_count': len(transaction_list)
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions/stats', methods=['GET'])
@authenticate_api_request()
def get_transaction_stats(merchant):
    """API endpoint to get transaction statistics"""
    try:
        # Get date filter
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Basic counts
        total_transactions = Transaction.query.filter_by(merchant_id=merchant.id).count()
        successful_transactions = Transaction.query.filter_by(
            merchant_id=merchant.id, 
            status='SUCCESS'
        ).count()
        
        # Amount calculations
        total_amount = db.session.query(db.func.sum(Transaction.amount)).filter_by(
            merchant_id=merchant.id,
            status='SUCCESS'
        ).scalar() or 0
        
        # Recent transactions
        recent_transactions = Transaction.query.filter(
            Transaction.merchant_id == merchant.id,
            Transaction.created_at >= start_date
        ).count()
        
        # Status breakdown
        status_breakdown = db.session.query(
            Transaction.status,
            db.func.count(Transaction.id).label('count')
        ).filter_by(merchant_id=merchant.id).group_by(Transaction.status).all()
        
        status_dict = {status: count for status, count in status_breakdown}
        
        return jsonify({
            'success': True,
            'stats': {
                'total_transactions': total_transactions,
                'successful_transactions': successful_transactions,
                'success_rate': (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0,
                'total_amount': total_amount,
                'recent_transactions': recent_transactions,
                'status_breakdown': status_dict
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/webhook', methods=['POST'])
def webhook_handler():
    """Webhook endpoint for payment gateway notifications"""
    try:
        data = request.get_json()
        transaction_id = data.get('transaction_id')
        status = data.get('status')
        
        transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
        if transaction:
            transaction.status = status
            transaction.payment_gateway_txn_id = data.get('gateway_txn_id')
            transaction.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Send webhook to merchant if configured
            if transaction.merchant.webhook_url and not transaction.webhook_sent:
                try:
                    webhook_data = {
                        'transaction_id': transaction.transaction_id,
                        'status': transaction.status,
                        'amount': transaction.amount,
                        'customer_email': transaction.customer_email,
                        'timestamp': transaction.updated_at.isoformat()
                    }
                    
                    response = requests.post(
                        transaction.merchant.webhook_url,
                        json=webhook_data,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        transaction.webhook_sent = True
                        db.session.commit()
                        
                except Exception as webhook_error:
                    print(f"Webhook error: {webhook_error}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ================================
# Error Handlers
# ================================

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='Internal server error'), 500

# ================================
# Initialize Database
# ================================

def init_db():
    """Initialize database tables"""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
    print("🚀 Kamlai Multi Service Server Starting...")
    print("📊 Merchant Dashboard: http://localhost:5000/dashboard")
    print("🔗 API Documentation: http://localhost:5000/api/docs")
    print("💳 Payment Testing: http://localhost:5000/payment/test")
    
    app.run(debug=True, host='0.0.0.0', port=5000)