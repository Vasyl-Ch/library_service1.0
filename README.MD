# 📚 Library Service API

A comprehensive RESTful API service for library management built with Django REST Framework. This system enables complete management of books, authors, borrowings, and payments with JWT authentication, Stripe integration, and Telegram notifications.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python Version](https://img.shields.io/badge/python-3.13-blue)
![Django Version](https://img.shields.io/badge/django-6.0-green)
![DRF](https://img.shields.io/badge/DRF-3.16-red)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
  - [Installing using GitHub](#installing-using-github)
  - [Run with Docker](#run-with-docker)
- [Getting Access](#-getting-access)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

- **🔐 JWT Authentication**: Secure token-based authentication system
- **👤 User Management**: User registration, login, and profile management
- **📖 Book Management**: Create and manage books with author information
- **✍️ Author Management**: Track book authors and their works
- **📚 Borrowing System**: Borrow books with automatic inventory management
- **💳 Payment Integration**: Stripe payment processing for borrowings and fines
- **📱 Telegram Notifications**: Real-time notifications for borrowings, returns, and payments
- **⏰ Automated Tasks**: Celery-based scheduled tasks for daily reports
- **🔍 Advanced Filtering**: Filter borrowings by status and books by availability
- **📊 Admin Panel**: Full-featured Django admin interface at `/admin/`
- **📖 Interactive API Documentation**: 
  - Swagger UI available at `/api/swagger/`
  - ReDoc available at `/api/redoc/`
- **🔄 Database Optimization**: Efficient queries with prefetch and select_related
- **⚡ Background Processing**: Redis-backed Celery for asynchronous tasks

---

## 🛠️ Tech Stack

**Backend Framework:**
- Django 6.0
- Django REST Framework
- Django REST Framework SimpleJWT

**Database:**
- PostgreSQL 15

**Payment Processing:**
- Stripe API

**Task Queue:**
- Celery
- Redis

**Notifications:**
- python-telegram-bot

**API Documentation:**
- drf-spectacular (OpenAPI 3.0)
- Swagger UI
- ReDoc

**Development Tools:**
- Django Debug Toolbar
- Python dotenv

**Containerization:**
- Docker
- Docker Compose

**Programming Language:**
- Python 3.13

---

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.13+** - [Download Python](https://www.python.org/downloads/)
- **PostgreSQL 15+** - [Download PostgreSQL](https://www.postgresql.org/download/)
- **Redis** - [Download Redis](https://redis.io/download)
- **Docker & Docker Compose** (optional, for containerized deployment) - [Download Docker](https://www.docker.com/get-started)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **Stripe Account** - [Sign up for Stripe](https://stripe.com/)
- **Telegram Bot** - [Create a Bot via BotFather](https://core.telegram.org/bots#6-botfather)

---

## 🚀 Installation

### Installing using GitHub

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Vasyl-Ch/library_service1.0.git
   cd library_service1.0
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   ```
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   
   Create a `.env` file in the root directory based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file and configure your settings:
   ```env
   # Django
   SECRET_KEY=your-secret-key-here
   
   # Database
   POSTGRES_DB=library_db
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   
   # Stripe
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   
   # Telegram
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   
   # Redis
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   ```

5. **Install and configure PostgreSQL:**
   
   Create a new PostgreSQL database with the credentials from your `.env` file.

6. **Install and start Redis:**
   
   Ensure Redis is running on your system.

7. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

8. **Create a superuser for admin access:**
   ```bash
   python manage.py createsuperuser
   ```

9. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

10. **In separate terminals, start Celery worker and beat:**
    ```bash
    # Terminal 2: Celery worker
    celery -A config worker -l info
    
    # Terminal 3: Celery beat scheduler
    celery -A config beat -l info
    ```

The API will be available at `http://localhost:8000/`

---

### Run with Docker

Docker provides the easiest way to get the application up and running.

1. **Ensure Docker is installed:**
   ```bash
   docker --version
   docker-compose --version
   ```

2. **Clone the repository:**
   ```bash
   git clone https://github.com/Vasyl-Ch/.git
   cd library_service1.0
   ```

3. **Create environment file:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your settings (for Docker, use `POSTGRES_HOST=db` and `REDIS_HOST=redis`):
   ```env
   # Django
   SECRET_KEY=your-secret-key-here
   
   # Database
   POSTGRES_DB=library_db
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_HOST=db
   POSTGRES_PORT=5432
   
   # Stripe
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   
   # Telegram
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   
   # Redis
   REDIS_HOST=redis
   REDIS_PORT=6379
   REDIS_DB=0
   ```

4. **Build and start containers:**
   ```bash
   docker-compose build
   docker-compose up
   ```

The API will be available at `http://localhost:8000/`

**Docker Commands:**
- Stop containers: `docker-compose down`
- View logs: `docker-compose logs -f`
- Rebuild containers: `docker-compose up --build`
- Run migrations: `docker-compose exec web python manage.py migrate`
- Create superuser: `docker-compose exec web python manage.py createsuperuser`
- Access Django shell: `docker-compose exec web python manage.py shell`

---

## 🔑 Getting Access

To access the API functionality, you need to authenticate:

### 1. Register a new user

**Endpoint:** `POST /api/users/`

**Request Body:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "securepassword123",
  "password_confirm": "securepassword123"
}
```

### 2. Obtain access token

**Endpoint:** `POST /api/token/`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 3. Use the access token

Include the token in the Authorization header for all subsequent requests:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4. Access admin panel (for staff users)

Navigate to `http://localhost:8000/admin/` and login with superuser credentials.

**Note:** Some endpoints require admin privileges. Regular authenticated users have read-only access to books and authors, can manage their own borrowings and payments, while creating books, authors, and managing other users' data requires admin rights.

---

## 📖 API Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI:** [http://localhost:8000/api/swagger/](http://localhost:8000/api/swagger/)
- **ReDoc:** [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)
- **OpenAPI Schema:** [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)

### Main API Endpoints

**Authentication:**
- `POST /api/token/` - Obtain JWT token
- `POST /api/token/refresh/` - Refresh JWT token
- `POST /api/users/` - Register new user
- `GET/PUT/PATCH /api/users/me/` - Manage current user profile

**Authors:**
- `GET /api/authors/` - List all authors
- `POST /api/authors/` - Create author (admin only)
- `GET /api/authors/{id}/` - Retrieve author details
- `PUT/PATCH /api/authors/{id}/` - Update author (admin only)
- `DELETE /api/authors/{id}/` - Delete author (admin only)

**Books:**
- `GET /api/books/` - List all books
- `POST /api/books/` - Create book (admin only)
- `GET /api/books/{id}/` - Retrieve book details
- `PUT/PATCH /api/books/{id}/` - Update book (admin only)
- `DELETE /api/books/{id}/` - Delete book (admin only)

**Query Parameters for Books:**
- Search by title or author name

**Borrowings:**
- `GET /api/borrowings/` - List borrowings (user sees only their own, admin sees all)
- `POST /api/borrowings/` - Create borrowing (automatically decreases book inventory)
- `GET /api/borrowings/{id}/` - Retrieve borrowing details
- `POST /api/borrowings/{id}/return/` - Return book (automatically increases inventory)

**Query Parameters for Borrowings:**
- `?is_active=true` - Filter active borrowings (not returned)
- `?is_active=false` - Filter returned borrowings

**Payments:**
- `GET /api/payments/` - List user's payments
- `POST /api/payments/` - Create payment with Stripe session
- `GET /api/payments/{id}/` - Retrieve payment details with payment link
- `GET /api/payments/pending/` - List all pending payments
- `GET /api/payments/success/` - Payment success callback (Stripe redirect)
- `GET /api/payments/cancel/` - Payment cancellation callback

---

## 📁 Project Structure

```
library-api/
│
├── config/                # Project configuration
│   ├── settings.py       # Django settings
│   ├── urls.py           # Main URL configuration
│   ├── celery.py         # Celery configuration
│   ├── wsgi.py           # WSGI configuration
│   └── asgi.py           # ASGI configuration
│
├── library/              # Main library app
│   ├── models.py         # Author, Book, Borrowing, Payment models
│   ├── serializers.py    # API serializers
│   ├── views.py          # ViewSets for all resources
│   ├── permissions.py    # Custom permissions
│   ├── tasks.py          # Celery tasks
│   ├── telegram_service.py  # Telegram notifications
│   ├── stripe_system.py  # Stripe payment integration
│   ├── tests.py          # Unit tests
│   ├── admin.py          # Admin configuration
│   └── management/       # Custom management commands
│       └── commands/
│           └── wait_for_db.py  # Database readiness checker
│
├── user/                 # User management app
│   ├── models.py         # Custom User model
│   ├── serializers.py    # User serializers
│   ├── views.py          # User views
│   └── admin.py          # User admin
│
├── manage.py             # Django management script
├── requirements.txt      # Project dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yaml   # Docker Compose configuration
├── .env.example          # Environment variables template
├── .dockerignore         # Docker ignore file
└── .gitignore           # Git ignore file
```

---

## 🧪 Testing

The project includes comprehensive unit tests for critical functionality:

**Run tests:**
```bash
python manage.py test
```

**Test Coverage Includes:**
- Borrowing model properties (`is_active`)
- Borrowing creation and inventory management
- Book return functionality
- Validation rules (duplicate borrowings, zero inventory, past dates)
- User permissions and filtering
- Active/inactive borrowing filters

---

## 🔔 Key Features Explained

### Inventory Management
- When a book is borrowed, inventory automatically decreases by 1
- When a book is returned, inventory automatically increases by 1
- Cannot borrow books with zero inventory
- Cannot delete books with active borrowings

### Payment System
- Automatic payment creation upon book return
- Stripe integration for secure payment processing
- Fine calculation for overdue returns (2x daily fee)
- Payment links expire and can be regenerated

### Telegram Notifications
The system sends notifications for:
- New borrowings
- Book returns
- Successful payments
- Daily reports (scheduled at 16:22 UTC)

### Celery Tasks
- `send_borrowing_notification` - Triggered on new borrowing
- `send_return_notification` - Triggered on book return
- `send_payment_notification` - Triggered on successful payment
- `send_daily_report` - Scheduled daily report with statistics

---

## 🤝 Contributing

Contributions are welcome! If you'd like to contribute to this project:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is distributed under the **MIT License**. See `LICENSE` file for more information.

---

## 📧 Contact

For questions or support, please open an issue on GitHub or contact the maintainer.

**Project Link:** [https://github.com/Vasyl-Ch/library_service1.0.git](https://github.com/Vasyl-Ch/library_service1.0.git)

---

**Made with ❤️ using Django REST Framework, Celery, Stripe, and Telegram Bot API**