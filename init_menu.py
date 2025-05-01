from app import db, Menu, app, User
import os
import random

def initialize_menu():
    # Check if menu items already exist
    if Menu.query.first():
        print("Menu items already exist.")
        return

    # Initial menu items
    menu_items = [
        # Beverages
        {'item_name': 'Masala Chai', 'price': 2.50, 'calories': 100, 'quantity': 100, 'category': 'Beverages', 'image_url': 'masala-chai.jpg'},
        {'item_name': 'Green Tea', 'price': 2.00, 'calories': 5, 'quantity': 100, 'category': 'Beverages', 'image_url': 'green-tea.jpg'},
        {'item_name': 'Lemon Tea', 'price': 2.00, 'calories': 25, 'quantity': 100, 'category': 'Beverages', 'image_url': 'lemon-tea.jpg'},
        {'item_name': 'Coffee', 'price': 3.00, 'calories': 120, 'quantity': 100, 'category': 'Beverages', 'image_url': 'coffee.jpg'},
        
        # Snacks
        {'item_name': 'Masala Samosa', 'price': 3.50, 'calories': 250, 'quantity': 50, 'category': 'Snacks', 'image_url': 'masala-samosa.jpg'},
        {'item_name': 'Chilli Samosa', 'price': 3.50, 'calories': 260, 'quantity': 50, 'category': 'Snacks', 'image_url': 'chilli-samosa.jpg'},
        {'item_name': 'Misal Pav', 'price': 5.00, 'calories': 400, 'quantity': 30, 'category': 'Snacks', 'image_url': 'misal-pav.jpg'},
        
        # Rice & Biryani
        {'item_name': 'Chicken Biryani', 'price': 12.00, 'calories': 800, 'quantity': 30, 'category': 'Rice & Biryani', 'image_url': 'chicken-biryani.jpg'},
        {'item_name': 'Mutton Biryani', 'price': 14.00, 'calories': 850, 'quantity': 25, 'category': 'Rice & Biryani', 'image_url': 'mutton-biryani.jpg'},
        {'item_name': 'Chicken Fried Rice', 'price': 10.00, 'calories': 700, 'quantity': 40, 'category': 'Rice & Biryani', 'image_url': 'chicken-fried-rice.jpg'},
        {'item_name': 'Veg Fried Rice', 'price': 8.00, 'calories': 600, 'quantity': 40, 'category': 'Rice & Biryani', 'image_url': 'veg-fried-rice.jpg'},
        
        # Pizza
        {'item_name': 'Chicken Pizza', 'price': 15.00, 'calories': 900, 'quantity': 20, 'category': 'Pizza', 'image_url': 'chicken-pizza.jpg'},
        {'item_name': 'Veg Pizza', 'price': 12.00, 'calories': 800, 'quantity': 20, 'category': 'Pizza', 'image_url': 'veg-pizza.jpg'},
        
        # Meals
        {'item_name': 'Chicken Meal', 'price': 18.00, 'calories': 1200, 'quantity': 15, 'category': 'Meals', 'image_url': 'chicken-meal.jpg'},
        {'item_name': 'Veg Meal', 'price': 15.00, 'calories': 1000, 'quantity': 15, 'category': 'Meals', 'image_url': 'veg-meal.jpg'},
    ]

    # Add menu items to database
    for item in menu_items:
        menu_item = Menu(**item)
        db.session.add(menu_item)
    
    try:
        db.session.commit()
        print("Menu items initialized successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing menu items: {str(e)}")

if __name__ == '__main__':
    initialize_menu()

# Initialize the menu items within the application context
with app.app_context():
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()
    print("Created database tables.")

    # Create a test user
    test_user = User(username="test", email="test@example.com")
    test_user.set_password("test123")
    db.session.add(test_user)
    db.session.commit()
    print("Created test user (username: test, password: test123)")

    # Menu items data
    menu_items = [
        # Beverages
        {
            "item_name": "Masala Chai",
            "price": 15.00,
            "calories": 100,
            "category": "Beverages",
            "image_url": "masala-chai.jpg"
        },
        {
            "item_name": "Coffee",
            "price": 20.00,
            "calories": 120,
            "category": "Beverages",
            "image_url": "coffee.jpg"
        },
        {
            "item_name": "Masala Samosa",
            "price": 25.00,
            "calories": 250,
            "category": "Snacks",
            "image_url": "masala-samosa.jpg"
        },
        {
            "item_name": "Chilli Samosa",
            "price": 30.00,
            "calories": 280,
            "category": "Snacks",
            "image_url": "chilli-samosa.jpg"
        },
        {
            "item_name": "Veg Fried Rice",
            "price": 140.00,
            "calories": 650,
            "category": "Rice & Biryani",
            "image_url": "veg-fried-rice.jpg"
        },
        {
            "item_name": "Veg Pizza",
            "price": 200.00,
            "calories": 700,
            "category": "Pizza",
            "image_url": "veg-pizza.jpg"
        },
        {
            "item_name": "Chicken Meal",
            "price": 180.00,
            "calories": 850,
            "category": "Meals",
            "image_url": "chicken-meal.jpg"
        },
        {
            "item_name": "Veg Meal",
            "price": 150.00,
            "calories": 750,
            "category": "Meals",
            "image_url": "veg-meal.jpg"
        }
    ]

    # Add all menu items to the database with random availability
    for item_data in menu_items:
        # 70% chance of item being available
        item_data['is_available'] = random.random() < 0.7
        menu_item = Menu(**item_data)
        db.session.add(menu_item)

    # Commit all changes
    try:
        db.session.commit()
        print("Successfully added all menu items!")
        
        # Print availability status
        available_count = Menu.query.filter_by(is_available=True).count()
        total_count = Menu.query.count()
        print(f"Items available: {available_count}/{total_count}")
    except Exception as e:
        db.session.rollback()
        print(f"Error adding menu items: {str(e)}") 