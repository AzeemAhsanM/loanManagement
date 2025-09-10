Loan Management System

A web-based Loan Management System built with Django and PostgreSQL.
This project helps manage borrowers, loans, repayments, and repayment schedules in a structured and efficient way.

🚀 Features

👤 Borrower Management – Add, update, and manage borrower details

💳 Loan Management – Create loans with principal, interest rate, and tenure

📅 Repayment Schedule – Automatically generate repayment schedules

💰 Repayments – Track repayments and pending amounts

🛠️ Tech Stack

Backend: Django (Python)
Database: PostgreSQL
Frontend: HTML, CSS, JavaScript (with AJAX)

⚙️ Installation

Clone the repository: git clone https://github.com/your-username/loan-management-system.git

Create and activate virtual environment:

Install dependencies:

pip install -r requirements.txt

Configure PostgreSQL database in settings.py:

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'loan_db',
        'USER': 'loan_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


Run migrations:

python manage.py migrate

Create superuser (admin):
python manage.py createsuperuser


Start development server:

python manage.py runserver
Visit http://127.0.0.1:8000 to access the application.


🤝 Contribution

Contributions are welcome! Feel free to open issues or submit PRs.
