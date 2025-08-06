#!/usr/bin/env python3
"""
UPI Gateway Wrapper - Complete Setup & Launch Script
Production-ready merchant transaction tracking system
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements_gateway.txt'])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def setup_database():
    """Initialize the database"""
    print("🗄️  Setting up database...")
    try:
        from upi_gateway_app import app, db
        with app.app_context():
            db.create_all()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_sample_merchant():
    """Create a sample merchant account for testing"""
    print("👤 Creating sample merchant account...")
    try:
        from upi_gateway_app import app, db, Merchant
        from werkzeug.security import generate_password_hash
        import secrets
        from datetime import datetime
        
        with app.app_context():
            # Check if sample merchant already exists
            existing = Merchant.query.filter_by(email='demo@upigateway.com').first()
            if existing:
                print("✅ Sample merchant already exists")
                print(f"   Email: demo@upigateway.com")
                print(f"   Password: demo123")
                return True
            
            # Create sample merchant
            merchant = Merchant(
                merchant_id=f"DEMO_MERCHANT_{int(datetime.utcnow().timestamp())}",
                email='demo@upigateway.com',
                password_hash=generate_password_hash('demo123'),
                business_name='Demo Business',
                api_key=secrets.token_urlsafe(32),
                api_secret=secrets.token_urlsafe(64)
            )
            
            db.session.add(merchant)
            db.session.commit()
            
            print("✅ Sample merchant created successfully")
            print(f"   Email: demo@upigateway.com")
            print(f"   Password: demo123")
            print(f"   API Key: {merchant.api_key}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create sample merchant: {e}")
        return False

def check_templates():
    """Check if template files exist"""
    print("📄 Checking template files...")
    templates_dir = 'templates'
    required_templates = [
        'base.html',
        'index.html', 
        'login.html',
        'dashboard.html',
        'payment_page.html'
    ]
    
    if not os.path.exists(templates_dir):
        print(f"❌ Templates directory '{templates_dir}' not found")
        return False
    
    missing_templates = []
    for template in required_templates:
        template_path = os.path.join(templates_dir, template)
        if not os.path.exists(template_path):
            missing_templates.append(template)
    
    if missing_templates:
        print(f"❌ Missing templates: {', '.join(missing_templates)}")
        return False
    
    print("✅ All template files found")
    return True

def start_server():
    """Start the UPI Gateway server"""
    print("🚀 Starting UPI Gateway server...")
    try:
        from upi_gateway_app import app
        print("\n" + "="*60)
        print("🎉 UPI Gateway Wrapper is now running!")
        print("="*60)
        print("📊 Merchant Dashboard: http://localhost:5000")
        print("🔑 Sample Login:")
        print("   Email: demo@upigateway.com")
        print("   Password: demo123")
        print("📚 API Documentation: http://localhost:5000/api/docs")
        print("💳 Test Payment: http://localhost:5000/payment/test")
        print("="*60)
        print("Press Ctrl+C to stop the server")
        print("="*60)
        
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False

def main():
    """Main setup and launch function"""
    print("🚀 UPI Gateway Wrapper - Setup & Launch")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Install dependencies
    if not install_dependencies():
        print("💡 Try: pip install -r requirements_gateway.txt")
        return
    
    # Check templates
    if not check_templates():
        print("💡 Make sure all template files are in the 'templates' directory")
        return
    
    # Setup database
    if not setup_database():
        return
    
    # Create sample merchant
    if not create_sample_merchant():
        return
    
    print("\n✅ Setup completed successfully!")
    print("🎯 Your UPI Gateway is ready to process payments!")
    
    # Start server
    start_server()

if __name__ == '__main__':
    main()