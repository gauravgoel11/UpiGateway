# PhonePe Merchant Dashboard

A Flask web application that simulates a PhonePe merchant portal with authentication, transaction management, and a beautiful dashboard interface.

## Features

### 🔐 Authentication & Mini Chromium Window
- **Simulated Login Experience**: Authentic mini Chrome-like pop-up window design
- **Auth Token Generation**: Automatic generation of simulated PhonePe API tokens
- **Session Management**: Secure session handling with merchant data persistence

### 📊 Transaction Management
- **API Simulation**: Simulates PhonePe API calls to fetch transaction data
- **Bulk Transaction Fetching**: Fetches 10-20 random transactions from the past 30 days
- **Real-time Statistics**: Live transaction counts, amounts, and status breakdowns
- **Data Persistence**: SQLite database storage with easy migration to PostgreSQL

### 🎨 Dashboard Features
- **Modern UI**: Clean, responsive design with PhonePe branding
- **Advanced Filtering**: Filter by date, status, and payment method
- **Transaction Table**: Detailed view with customer info, amounts, and status badges
- **Statistics Cards**: Visual representation of key metrics
- **Copy Auth Token**: One-click token copying for API integration

### 🔧 Technical Features
- **Modular Architecture**: Clean separation of routes and business logic
- **API Endpoints**: RESTful API for transaction fetching and statistics
- **Extensible Design**: Ready for real PhonePe API integration
- **Responsive Design**: Works on desktop and mobile devices

## Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Quick Start

1. **Clone or navigate to the project directory**
   ```bash
   cd your_flask_app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   - Navigate to `http://localhost:5000`
   - You'll see the mini Chromium window login interface

## Usage Guide

### 1. Login Process
- Enter your merchant name (and optional email)
- Click "Login & Fetch Transactions"
- The system generates a simulated auth token
- You're redirected to the dashboard

### 2. Dashboard Features
- **View Statistics**: See total transactions, amounts, and status breakdowns
- **Fetch Transactions**: Click "Fetch from PhonePe API" to simulate API calls
- **Filter Data**: Use date, status, and payment method filters
- **Add Test Data**: Use "Add Test Transaction" for development testing

### 3. API Integration Points
- **Auth Token**: Displayed prominently for easy copying
- **API Endpoints**: 
  - `POST /api/fetch_transactions` - Simulates PhonePe transaction fetching
  - `GET /api/transaction_stats` - Returns transaction statistics

## Database Schema

### Transactions Table
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT UNIQUE,
    date TEXT,
    amount REAL,
    merchant TEXT,
    status TEXT,
    customer_name TEXT,
    payment_method TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Merchants Table
```sql
CREATE TABLE merchants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_id TEXT UNIQUE,
    name TEXT,
    email TEXT,
    auth_token TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Future Enhancements

### Real PhonePe Integration
1. **Replace simulation functions** with actual PhonePe API calls
2. **Implement OAuth flow** for real authentication
3. **Add webhook support** for real-time transaction updates
4. **Enhance security** with proper token management

### Database Migration
1. **PostgreSQL Support**: Easy migration path with SQLAlchemy ORM
2. **Connection Pooling**: For better performance with real APIs
3. **Data Archiving**: For historical transaction management

### Additional Features
1. **Export Functionality**: CSV/PDF export of transaction data
2. **Advanced Analytics**: Charts and graphs for business insights
3. **Multi-merchant Support**: Admin panel for managing multiple merchants
4. **Real-time Notifications**: WebSocket support for live updates

## API Documentation

### Authentication
All API endpoints require a valid session. The auth token is automatically generated during login.

### Endpoints

#### Fetch Transactions
```http
POST /api/fetch_transactions
```
Simulates fetching transactions from PhonePe API.

**Response:**
```json
{
  "success": true,
  "message": "Fetched 15 transactions from PhonePe API",
  "transactions_count": 15
}
```

#### Get Statistics
```http
GET /api/transaction_stats
```
Returns transaction statistics for the authenticated merchant.

**Response:**
```json
{
  "total_transactions": 25,
  "total_amount": 12500.50,
  "status_breakdown": {
    "SUCCESS": 20,
    "PENDING": 3,
    "FAILED": 2
  }
}
```

## Security Notes

- **Development Mode**: This is a simulation for development purposes
- **Production Ready**: Add proper authentication, HTTPS, and security headers
- **Token Management**: Implement proper token refresh and validation
- **Data Validation**: Add input validation and sanitization

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Change port in app.py
   app.run(debug=True, port=5001)
   ```

2. **Database Issues**
   ```bash
   # Delete transactions.db and restart
   rm transactions.db
   python app.py
   ```

3. **Dependencies Issues**
   ```bash
   # Reinstall dependencies
   pip install --force-reinstall -r requirements.txt
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational and development purposes. For production use with PhonePe APIs, ensure compliance with PhonePe's terms of service and API documentation. 