from app import app, db, User, Menu

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@canteen.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists.")

        # Initialize menu items
        if not Menu.query.first():  # Only initialize if no menu items exist
            menu_items = [
                # Beverages
                {'item_name': 'Masala Chai', 'price': 25.00, 'calories': 100, 'quantity': 100, 'category': 'Beverages', 'image_url': 'masala-chai.jpg'},
                {'item_name': 'Green Tea', 'price': 20.00, 'calories': 5, 'quantity': 100, 'category': 'Beverages', 'image_url': 'green-tea.jpg'},
                {'item_name': 'Lemon Tea', 'price': 20.00, 'calories': 25, 'quantity': 100, 'category': 'Beverages', 'image_url': 'lemon-tea.jpg'},
                {'item_name': 'Coffee', 'price': 30.00, 'calories': 120, 'quantity': 100, 'category': 'Beverages', 'image_url': 'coffee.jpg'},
                
                # Snacks
                {'item_name': 'Masala Samosa', 'price': 35.00, 'calories': 250, 'quantity': 50, 'category': 'Snacks', 'image_url': 'masala-samosa.jpg'},
                {'item_name': 'Chilli Samosa', 'price': 35.00, 'calories': 260, 'quantity': 50, 'category': 'Snacks', 'image_url': 'chilli-samosa.jpg'},
                {'item_name': 'Misal Pav', 'price': 50.00, 'calories': 400, 'quantity': 30, 'category': 'Snacks', 'image_url': 'misal-pav.jpg'},
                
                # Rice & Biryani
                {'item_name': 'Chicken Biryani', 'price': 180.00, 'calories': 800, 'quantity': 30, 'category': 'Rice & Biryani', 'image_url': 'chicken-biryani.jpg'},
                {'item_name': 'Mutton Biryani', 'price': 220.00, 'calories': 850, 'quantity': 25, 'category': 'Rice & Biryani', 'image_url': 'mutton-biryani.jpg'},
                {'item_name': 'Chicken Fried Rice', 'price': 160.00, 'calories': 700, 'quantity': 40, 'category': 'Rice & Biryani', 'image_url': 'chicken-fried-rice.jpg'},
                {'item_name': 'Veg Fried Rice', 'price': 140.00, 'calories': 600, 'quantity': 40, 'category': 'Rice & Biryani', 'image_url': 'veg-fried-rice.jpg'},
                
                # Pizza
                {'item_name': 'Chicken Pizza', 'price': 280.00, 'calories': 900, 'quantity': 20, 'category': 'Pizza', 'image_url': 'chicken-pizza.jpg'},
                {'item_name': 'Veg Pizza', 'price': 240.00, 'calories': 800, 'quantity': 20, 'category': 'Pizza', 'image_url': 'veg-pizza.jpg'},
                
                # Meals
                {'item_name': 'Chicken Meal', 'price': 180.00, 'calories': 1200, 'quantity': 15, 'category': 'Meals', 'image_url': 'chicken-meal.jpg'},
                {'item_name': 'Veg Meal', 'price': 150.00, 'calories': 1000, 'quantity': 15, 'category': 'Meals', 'image_url': 'veg-meal.jpg'},
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
        else:
            print("Menu items already exist.")

if __name__ == "__main__":
    init_db() 