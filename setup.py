from setuptools import setup, find_packages
import os
import subprocess
import sys
from pathlib import Path
from app import db, create_app
from init_admin import create_admin
from init_menu import initialize_menu

def setup_environment():
    print("Setting up the Canteen Management System...")
    
    # Create instance directory if it doesn't exist
    Path("instance").mkdir(exist_ok=True)
    
    # Initialize Flask app and create database
    app = create_app()
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        print("Initializing admin user...")
        create_admin()
        
        print("Initializing menu items...")
        initialize_menu()
    
    print("\nSetup completed successfully!")
    print("\nTo run the application:")
    print("1. Start Flask backend:   python app.py")
    print("2. Start Streamlit frontend:   streamlit run streamlit_app.py")
    print("\nAccess the applications at:")
    print("- Backend: http://localhost:5000")
    print("- Frontend: http://localhost:8501")

def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths

# Get all static files
static_files = package_files('static')

setup(
    name="canteen-management",
    version="1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': static_files,
    },
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'flask-cors',
        'python-dotenv',
        'streamlit',
        'pillow',
        'requests',
    ],
)

if __name__ == "__main__":
    # Install requirements
    print("Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Run setup
    setup_environment() 