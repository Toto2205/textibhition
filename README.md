# Canteen Management System

A modern canteen management system built with Flask backend and Streamlit frontend.

## Features

- User Authentication (Admin and Customer)
- Menu Management with Categories
  - Beverages
  - Snacks
  - Rice & Biryani
  - Pizza
  - Meals
- Shopping Cart System
- Order Management
- Image-based Menu Display
- Modern UI Interface

## Directory Structure

```
.
├── app.py              # Flask backend application
├── streamlit_app.py    # Streamlit frontend application
├── init_admin.py       # Admin user initialization
├── init_menu.py        # Menu items initialization
├── setup.py           # Setup script
├── requirements.txt    # Project dependencies
├── static/            # Static files
│   └── images/        # Menu item images
├── templates/         # HTML templates
├── instance/          # Database directory
└── ml_model/         # Machine learning model directory
```

## Setup Instructions

1. Clone the repository
2. Create a Python virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Run the setup script:
   ```bash
   python setup.py
   ```

   This will:
   - Install all required dependencies
   - Initialize the database
   - Create admin user
   - Set up menu items

## Running the Application

1. Start the Flask backend:
   ```bash
   python app.py
   ```
   The backend will be available at http://localhost:5000

2. In a new terminal, start the Streamlit frontend:
   ```bash
   streamlit run streamlit_app.py
   ```
   The frontend will be available at http://localhost:8501

## Default Admin Credentials

- Username: admin
- Password: admin123

## Technologies Used

- Backend: Flask 3.0.2
- Frontend: Streamlit 1.32.0
- Database: SQLite with Flask-SQLAlchemy
- Image Processing: Pillow
- Additional: scikit-learn, pandas (for future ML features)

## Note

Make sure both the backend and frontend servers are running simultaneously for the application to work properly. The backend serves the API and static files, while the frontend provides the user interface. 