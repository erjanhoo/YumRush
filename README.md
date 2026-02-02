# YumRush - Food Delivery Platform

A comprehensive food delivery system built with Django REST Framework, featuring real-time order tracking, live chat, multi-role management, and secure authentication.

## ✨ Main Features

### 🔐 **Advanced Authentication & Security**

- **Multi-role System**: Three distinct user roles (User, Manager, Courier) with role-based permissions
- **JWT Token Authentication**: Secure access and refresh tokens with blacklisting support
- **Email Authentication Backend**: Login with email instead of username
- **Account Management**:
  - Change password (with current password confirmation)
  - Change email (with password confirmation)
  - Change username (with password confirmation)
  - Delete account (with password confirmation)
- **Note**: Two-Factor Authentication and OTP email verification are currently disabled for Railway deployment compatibility

### 👥 **User Management**

- **User Profiles**: Customizable profiles with avatars, addresses, and contact information
- **Balance System**: Built-in wallet for quick payments
  - Top-up functionality
  - Transaction history tracking
  - Automatic refunds on order cancellation
- **Account Types**:
  - **Regular Users**: Browse, order, and track deliveries
  - **Managers**: Create and manage products, categories, and courier accounts
  - **Couriers**: Accept orders, update delivery status, view earnings

### 🍔 **Product Catalog & Management**

- **Multi-Company Support**: Multiple restaurants/companies in one platform
- **Category System**: Hierarchical categories with parent-child relationships
- **Product Features**:
  - Original and discounted pricing
  - Product images and detailed descriptions
  - Ingredient lists and nutritional information (grams)
  - Stock quantity tracking
  - Availability status (in-stock/out-of-stock)
  - Preparation time estimation
  - SEO tags and search keywords
- **Product Reviews**: User ratings and reviews with verified purchase badges
- **Inventory Management**:
  - Real-time stock tracking
  - Low-stock threshold alerts
  - Automatic availability updates
  - Stock increment/decrement operations

### 🛒 **Shopping Cart & Checkout**

- **Persistent Shopping Cart**: Cart saved per user account
- **Real-time Updates**: Dynamic cart total calculations
- **Quantity Management**: Add, update, or remove items with validation
- **Stock Validation**: Prevents over-ordering out-of-stock items

### 📦 **Order Management System**

- **Complete Order Lifecycle**:
  1. **New** - Order created and payment deducted
  2. **Assigned** - Courier assigned to order
  3. **Delivering** - Order in transit
  4. **Delivered** - Successfully completed
  5. **Cancelled** - Cancelled with automatic refund

- **Order Features**:
  - Delivery or pickup options
  - Receiver information management
  - Order history and tracking
  - Order rating system (1-5 stars)
  - Real-time status updates
  - Chat group creation per order

- **Delivery Management**:
  - Custom delivery addresses
  - Receiver name and phone number
  - Delivery instructions/notes
  - Free delivery options
  - Delivery type selection

### 🚚 **Courier System**

- **Order Dashboard**:
  - View all available orders (unassigned)
  - See active orders (assigned and delivering)
  - Track completed delivery history
- **Order Actions**:
  - Accept available orders
  - Update status to "delivering"
  - Mark orders as delivered
  - Automatic email notifications to customers
- **Performance Tracking**: View completed orders and earnings

### 💬 **Real-time Live Chat**

- **WebSocket-Based Communication**: Powered by Django Channels
- **Order-Specific Chats**: Automatic chat group creation for each order
- **Features**:
  - Message history retrieval
  - Real-time message delivery
  - Access control (only order participants)
  - Support for customer-courier communication
- **Security**: Authentication required, user access validation

### 🔍 **Advanced Search & Filtering**

- **Product Search**: Multi-field search across names, descriptions, and tags
- **Filter Options**:
  - By category
  - By company/restaurant
  - By price range
  - By availability
  - By rating
- **Sorting Options**: Price, rating, newest, popularity

### 📧 **Email Notifications**

- **Automated Emails via Celery** (Currently Disabled for Railway):
  - Order confirmation
  - Courier assignment notifications
  - Order status updates
  - Delivery completion alerts
  - Cancellation confirmations
- **Note**: Email functionality is commented out to avoid issues with Railway's email restrictions

### 🎯 **Manager Features**

- **Product Management**:
  - Create, update, and delete products
  - Manage product inventory
  - Set pricing and discounts
  - Upload product images
- **Courier Management**:
  - Create courier accounts
  - Assign company affiliations
- **Company Control**: Products automatically linked to manager's company

### 🛡️ **Security & Performance**

- **Caching System**: Redis-based caching for improved performance
  - Order history caching
  - Frequently accessed data
  - Session storage
- **Rate Limiting**: Comprehensive throttling on sensitive endpoints
- **Background Tasks**: Celery for asynchronous email sending
- **Database Optimization**: Efficient queries with select_related and prefetch_related

### 📊 **API Features**

- **RESTful API**: Clean, well-documented REST endpoints
- **Swagger Documentation**: Interactive API documentation at `/swagger/`
- **CORS Support**: Configured for cross-origin requests
- **Pagination**: Efficient data retrieval for large datasets
- **Error Handling**: Consistent error responses with proper HTTP status codes

## 🏗️ Architecture

### Backend Stack

- **Django 5.2.5**: Web framework
- **Django REST Framework**: RESTful API development
- **PostgreSQL**: Primary database
- **Redis**: Caching and WebSocket channel layer
- **Celery**: Background task processing
- **Django Channels**: WebSocket support for real-time features
- **JWT (SimpleJWT)**: Token-based authentication

### Key Technologies

- **Email**: SMTP integration for notifications
- **File Storage**: Media file handling for images
- **WebSockets**: Real-time bidirectional communication
- **Background Workers**: Asynchronous task processing

## 📁 Project Structure

```
YumRush/
├── core/                    # Main Django project
│   ├── core/               # Project settings & configuration
│   │   ├── settings.py    # Django settings with Redis, Celery, JWT config
│   │   ├── urls.py        # Main URL routing
│   │   ├── celery.py      # Celery configuration
│   │   └── asgi.py        # ASGI config for WebSockets
│   │
│   ├── user/              # User management & authentication
│   │   ├── models.py      # User model, roles, transactions
│   │   ├── views.py       # Auth endpoints, profile management
│   │   ├── serializers.py # API serializers
│   │   ├── throttling.py  # OTP rate limiting
│   │   ├── tasks.py       # Celery tasks (email sending)
│   │   └── auth_backends.py # Email authentication backend
│   │
│   ├── product/           # Product catalog & categories
│   │   ├── models.py      # Product, Category, Company, Reviews
│   │   ├── views.py       # Product CRUD, search, filtering
│   │   └── serializers.py # Product data serializers
│   │
│   ├── order/             # Order processing & cart
│   │   ├── models.py      # Order, Cart, Delivery, OrderItem
│   │   ├── views.py       # Order creation, status updates
│   │   ├── serializers.py # Order data serializers
│   │   └── tasks.py       # Email notifications
│   │
│   ├── live_chat/         # Real-time chat system
│   │   ├── models.py      # Message, Group models
│   │   ├── consumers.py   # WebSocket consumer for chat
│   │   ├── routing.py     # WebSocket URL routing
│   │   └── views.py       # Chat history API
│   │
│   └── common/            # Shared utilities
│       └── permissions.py # Custom permission classes
│
└── media/                 # Uploaded files
    ├── categories/       # Category images
    ├── companies/        # Company logos
    └── products/         # Product images
```

## 🎯 Use Cases

### For Customers

1. Browse products by category or restaurant
2. Search for specific items
3. Add items to cart and checkout
4. Pay using account balance
5. Track order status in real-time
6. Chat with courier during delivery
7. Rate and review completed orders
8. View order history

### For Couriers

1. View available delivery orders
2. Accept orders for delivery
3. Update order status (delivering, delivered)
4. Chat with customers
5. Track completed deliveries
6. Manage active deliveries

### For Managers

1. Create and manage products
2. Set up categories and pricing
3. Manage inventory and stock
4. Create courier accounts
5. Monitor company performance

## 🔒 Security Features Implemented

- **OTP Throttling**: Prevents brute force attacks on verification codes
- **JWT Blacklisting**: Secure logout with token invalidation
- **Role-Based Access Control**: Endpoint protection by user role
- **CSRF Protection**: Django CSRF middleware enabled
- **Password Hashing**: Secure password storage with Django's password validators
- **Rate Limiting**: Multiple throttle layers for sensitive endpoints

## 🚀 Railway Deployment Guide

### Prerequisites

- GitHub repository with your code pushed
- Railway account (sign up at [railway.app](https://railway.app))

### Deployment Steps

#### 1. **Create New Project**

1. Log in to Railway
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your YumRush repository
5. Set **Root Directory** to `core`

#### 2. **Add Database Services**

1. Click "New" → "Database" → "Add PostgreSQL"
2. Click "New" → "Database" → "Add Redis"
3. Railway will auto-generate `DATABASE_URL` and `REDIS_URL`

#### 3. **Configure Environment Variables**

Add these variables to your web service:

**Required:**

```bash
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=.railway.app,yourdomain.com
DATABASE_URL=postgresql://...  # Auto-added by Railway Postgres
REDIS_URL=redis://...          # Auto-added by Railway Redis
```

**Optional (if using email later):**

```bash
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

#### 4. **Deploy Web Service**

- Railway automatically detects Dockerfile
- The entrypoint script will:
  - Run database migrations
  - Collect static files
  - Start Daphne server on Railway's dynamic PORT

#### 5. **Add Celery Worker (Optional)**

1. Click "New" → "Service from repo"
2. Select same repository
3. Set **Root Directory** to `core`
4. Override **Start Command** to:
   ```bash
   celery -A core worker -l info
   ```
5. Add same environment variables as web service

#### 6. **Configure Custom Domain (Optional)**

1. Go to your web service settings
2. Click "Settings" → "Domains"
3. Add your custom domain
4. Update `ALLOWED_HOSTS` with your domain

### Environment Variables Reference

| Variable              | Description                             | Example                    |
| --------------------- | --------------------------------------- | -------------------------- |
| `SECRET_KEY`          | Django secret key                       | `django-insecure-xyz...`   |
| `DEBUG`               | Debug mode (always False in production) | `False`                    |
| `ALLOWED_HOSTS`       | Allowed hostnames                       | `.railway.app,example.com` |
| `DATABASE_URL`        | PostgreSQL connection string            | Auto-added by Railway      |
| `REDIS_URL`           | Redis connection string                 | Auto-added by Railway      |
| `EMAIL_HOST_USER`     | Gmail account (optional)                | `your@gmail.com`           |
| `EMAIL_HOST_PASSWORD` | Gmail app password (optional)           | `your-app-password`        |

### Post-Deployment

1. **Verify deployment**: Check Railway logs for successful startup
2. **Test endpoints**: Visit `https://your-app.railway.app/swagger/`
3. **Create superuser** (via Railway CLI):
   ```bash
   railway run python manage.py createsuperuser
   ```

### Local Development

```bash
cd core
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Or use Docker Compose:

```bash
cd core
docker-compose up
```

## 📚 API Documentation

Interactive API documentation available at `/swagger/` when running the server.

### Key Endpoint Groups

- **Authentication**: `/api/user/` - Registration, login, logout
- **Profile Management**: `/api/user/profile/` - View and update profile
- **Account Management**:
  - `/api/user/change_password/` - Change password with confirmation
  - `/api/user/change_email/` - Change email with password confirmation
  - `/api/user/change_username/` - Change username with password confirmation
  - `/api/user/delete_account/` - Delete account with password confirmation
- **Products**: `/api/product/` - Product catalog, search, details
- **Orders**: `/api/order/` - Create, track, manage orders
- **Chat**: WebSocket connection for real-time messaging
