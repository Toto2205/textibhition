from flask import Flask, request, jsonify, render_template, url_for, session, redirect, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json
from flask_cors import CORS
import logging
import os
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the absolute path to the static folder
static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
logger.info(f"Static folder path: {static_folder}")

# Initialize SQLAlchemy without a Flask app yet
db = SQLAlchemy()

def create_app():
    app = Flask(__name__, 
                static_folder=static_folder,
                static_url_path='/static')
    
    # Configure app
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///canteen.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Enable CORS
    CORS(app, 
         supports_credentials=True,
         resources={
             r"/api/*": {"origins": "*"},
             r"/static/*": {"origins": "*"}
         })
    
    # Initialize the SQLAlchemy app
    db.init_app(app)
    
    return app

app = create_app()

# Push an application context
app.app_context().push()

# Ensure static folders exist
os.makedirs(os.path.join(static_folder, 'images'), exist_ok=True)

# Add error handlers
@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"404 error: {error}")
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# Add request logging
@app.before_request
def log_request_info():
    if not request.path.startswith('/static/'):
        logger.info('Headers: %s', request.headers)
        logger.info('Body: %s', request.get_data())

@app.after_request
def log_response_info(response):
    if not request.path.startswith('/static/'):
        try:
            logger.info('Response: %s', response.get_data())
        except:
            pass
    return response

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    orders = db.relationship('Order', backref='customer', lazy=True)
    cart = db.relationship('CartItem', backref='customer', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Menu Model
class Menu(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    calories = db.Column(db.Integer)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    category = db.Column(db.String(50))
    image_url = db.Column(db.String(200))
    cart_items = db.relationship('CartItem', backref='menu_item', lazy=True)
    order_items = db.relationship('OrderItem', backref='menu_item', lazy=True)

    def is_available(self):
        return self.quantity > 0

# CartItem Model
class CartItem(db.Model):
    cart_item_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('menu.item_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

# Order Model
class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    payment_id = db.Column(db.String(100))
    items = db.relationship('OrderItem', backref='order', lazy=True)

# OrderItem Model
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('menu.item_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

# Favorites Model
class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('menu.item_id'), nullable=False)
    menu_item = db.relationship('Menu', backref='favorites')

def get_image_url(image_filename):
    """Generate full URL for image"""
    if not image_filename:
        return None
    
    # Get the base URL from environment variable or use request.host_url
    base_url = os.getenv('BASE_URL')
    if not base_url and request:
        base_url = request.host_url.rstrip('/')
    
    # If no base URL is available, use a relative path
    if not base_url:
        return f"/static/images/{image_filename}"
    
    return f"{base_url}/static/images/{image_filename}"

# Authentication routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.check_password(data['password']):
        session['user_id'] = user.id
        return jsonify({
            'message': 'Logged in successfully',
            'user': {
                'id': user.id, 
                'username': user.username,
                'is_admin': user.is_admin
            }
        })
    
    return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/api/logout')
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'})

# Cart routes
@app.route('/api/cart', methods=['GET', 'POST'])
def cart():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Check if item already exists in cart
        existing_item = CartItem.query.filter_by(
            user_id=session['user_id'],
            item_id=data['item_id']
        ).first()
        
        if existing_item:
            # Update quantity
            existing_item.quantity += data.get('quantity', 1)
            db.session.commit()
        else:
            # Add new item
            cart_item = CartItem(
                user_id=session['user_id'],
                item_id=data['item_id'],
                quantity=data.get('quantity', 1)
            )
            db.session.add(cart_item)
            db.session.commit()
        
        return jsonify({'message': 'Item added to cart', 'success': True})
    
    # GET request - return cart items
    cart_items = CartItem.query.filter_by(user_id=session['user_id']).all()
    return jsonify([{
        'id': item.cart_item_id,
        'item_id': item.item_id,
        'item_name': item.menu_item.item_name,
        'price': item.menu_item.price,
        'quantity': item.quantity,
        'total': item.menu_item.price * item.quantity
    } for item in cart_items])

@app.route('/api/cart/<int:item_id>', methods=['DELETE'])
def remove_from_cart(item_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    CartItem.query.filter_by(user_id=session['user_id'], cart_item_id=item_id).delete()
    db.session.commit()
    return jsonify({'message': 'Item removed from cart'})

# Admin middleware
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Please login first'}), 401
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# Admin routes for inventory management
@app.route('/api/admin/inventory', methods=['GET'])
@admin_required
def get_inventory():
    items = Menu.query.all()
    return jsonify([{
        'item_id': item.item_id,
        'item_name': item.item_name,
        'quantity': item.quantity,
        'is_available': item.is_available(),
        'category': item.category,
        'price': item.price
    } for item in items])

@app.route('/api/admin/inventory/<int:item_id>', methods=['PUT'])
@admin_required
def update_inventory(item_id):
    data = request.get_json()
    item = Menu.query.get_or_404(item_id)
    
    if 'quantity' in data:
        item.quantity = data['quantity']
    
    if 'price' in data:
        item.price = data['price']
    
    db.session.commit()
    return jsonify({
        'message': 'Inventory updated successfully',
        'item': {
            'item_id': item.item_id,
            'item_name': item.item_name,
            'quantity': item.quantity,
            'is_available': item.is_available(),
            'price': item.price
        }
    })

@app.route('/api/admin/low-stock', methods=['GET'])
@admin_required
def get_low_stock():
    # Items with quantity less than 10
    low_stock_threshold = 10
    items = Menu.query.filter(Menu.quantity < low_stock_threshold).all()
    
    return jsonify([{
        'item_id': item.item_id,
        'item_name': item.item_name,
        'quantity': item.quantity,
        'category': item.category,
        'price': item.price
    } for item in items])

@app.route('/api/admin/bulk-update', methods=['POST'])
@admin_required
def bulk_update_inventory():
    data = request.get_json()
    if not isinstance(data, list):
        return jsonify({'error': 'Expected a list of items'}), 400
    
    updated_items = []
    for item_data in data:
        item = Menu.query.get(item_data.get('item_id'))
        if item:
            if 'quantity' in item_data:
                item.quantity = item_data['quantity']
            if 'price' in item_data:
                item.price = item_data['price']
            updated_items.append(item)
    
    db.session.commit()
    return jsonify({
        'message': f'Successfully updated {len(updated_items)} items',
        'updated_items': [{
            'item_id': item.item_id,
            'item_name': item.item_name,
            'quantity': item.quantity,
            'price': item.price
        } for item in updated_items]
    })

# Add reorder notification system
class ReorderNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('menu.item_id'), nullable=False)
    threshold = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_processed = db.Column(db.Boolean, default=False)
    menu_item = db.relationship('Menu', backref='reorder_notifications')

@app.route('/api/admin/reorder-notifications', methods=['GET'])
@admin_required
def get_reorder_notifications():
    notifications = ReorderNotification.query.filter_by(is_processed=False).all()
    return jsonify([{
        'id': n.id,
        'item_id': n.item_id,
        'item_name': n.menu_item.item_name,
        'current_quantity': n.menu_item.quantity,
        'threshold': n.threshold,
        'created_at': n.created_at.isoformat()
    } for n in notifications])

@app.route('/api/admin/reorder-notifications/<int:notification_id>', methods=['PUT'])
@admin_required
def process_reorder_notification(notification_id):
    notification = ReorderNotification.query.get_or_404(notification_id)
    notification.is_processed = True
    db.session.commit()
    return jsonify({'message': 'Notification marked as processed'})

# Add automatic reorder notification creation
def create_reorder_notification(item):
    if item.quantity < 10:  # Threshold for low stock
        notification = ReorderNotification(
            item_id=item.item_id,
            threshold=10
        )
        db.session.add(notification)
        db.session.commit()

# Update the create_order function to check for low stock
@app.route('/api/orders', methods=['POST'])
def create_order():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    cart_items = CartItem.query.filter_by(user_id=session['user_id']).all()
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400
    
    # Check if all items are available in sufficient quantity
    for cart_item in cart_items:
        menu_item = Menu.query.get(cart_item.item_id)
        if not menu_item:
            return jsonify({'error': f'Item not found'}), 400
        if menu_item.quantity < cart_item.quantity:
            return jsonify({
                'error': f'Not enough quantity available for {menu_item.item_name}. Available: {menu_item.quantity}'
            }), 400
    
    total_amount = sum(item.menu_item.price * item.quantity for item in cart_items)
    
    try:
        # Create order first
        order = Order(user_id=session['user_id'], total_amount=total_amount)
        db.session.add(order)
        db.session.commit()  # Commit to get the order_id
        
        # Add order items and update quantities
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.order_id,
                item_id=cart_item.item_id,
                quantity=cart_item.quantity,
                price=cart_item.menu_item.price
            )
            db.session.add(order_item)
            
            # Update menu item quantity
            menu_item = Menu.query.get(cart_item.item_id)
            menu_item.quantity -= cart_item.quantity
            
            # Check if we need to create a reorder notification
            create_reorder_notification(menu_item)
        
        # Clear cart
        CartItem.query.filter_by(user_id=session['user_id']).delete()
        
        db.session.commit()
        return jsonify({
            'message': 'Order created successfully',
            'order_id': order.order_id,
            'total_amount': total_amount
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating order: {str(e)}")
        return jsonify({'error': 'Failed to create order: ' + str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    orders = Order.query.filter_by(user_id=session['user_id']).all()
    return jsonify([{
        'order_id': order.order_id,
        'total_amount': order.total_amount,
        'status': order.status,
        'order_date': order.order_date.isoformat(),
        'items': [{
            'item_name': item.menu_item.item_name,
            'quantity': item.quantity,
            'price': item.price
        } for item in order.items]
    } for order in orders])

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    data = request.get_json()
    order = Order.query.filter_by(order_id=order_id, user_id=session['user_id']).first()
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    if data.get('status') not in ['pending', 'paid', 'completed', 'cancelled']:
        return jsonify({'error': 'Invalid status'}), 400
    
    order.status = data['status']
    db.session.commit()
    
    return jsonify({
        'message': 'Order status updated successfully',
        'order_id': order.order_id,
        'status': order.status
    })

@app.route('/api/orders/track/<int:order_id>', methods=['GET'])
def track_order(order_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    order = Order.query.filter_by(order_id=order_id, user_id=session['user_id']).first()
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    return jsonify({
        'order_id': order.order_id,
        'status': order.status,
        'order_date': order.order_date.isoformat(),
        'total_amount': order.total_amount,
        'items': [{
            'item_name': item.menu_item.item_name,
            'quantity': item.quantity,
            'price': item.price
        } for item in order.items]
    })

# Menu routes
@app.route('/api/menu', methods=['GET'])
def get_menu():
    # Get availability filter from query params
    show_all = request.args.get('show_all', 'false').lower() == 'true'
    
    # Query items based on availability
    query = Menu.query
    if not show_all:
        query = query.filter(Menu.quantity > 0)
    
    items = query.all()
    output = [{
        'item_id': item.item_id,
        'item_name': item.item_name,
        'price': item.price,
        'calories': item.calories,
        'category': item.category,
        'image_url': get_image_url(item.image_url),
        'is_available': item.is_available(),
        'quantity': item.quantity
    } for item in items]
    return jsonify(output)

@app.route('/api/menu/<int:item_id>/availability', methods=['PUT'])
def update_item_availability(item_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    item = Menu.query.get_or_404(item_id)
    data = request.get_json()
    
    if 'quantity' not in data:
        return jsonify({'error': 'quantity field is required'}), 400
    
    item.quantity = data['quantity']
    db.session.commit()
    
    return jsonify({
        'message': f'Item {item.item_name} quantity updated to {item.quantity}',
        'item_id': item.item_id,
        'quantity': item.quantity,
        'is_available': item.is_available()
    })

# Favorites routes
@app.route('/api/favorites', methods=['GET'])
def get_favorites():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    try:
        favorites = Favorite.query.filter_by(user_id=session['user_id']).all()
        favorites_data = []
        
        for fav in favorites:
            item = fav.menu_item
            item_data = {
                'item_id': item.item_id,
                'item_name': item.item_name,
                'price': item.price,
                'calories': item.calories,
                'category': item.category,
                'is_available': item.is_available(),
                'image_url': get_image_url(item.image_url) if item.image_url else None
            }
            favorites_data.append(item_data)
        
        return jsonify(favorites_data)
    except Exception as e:
        logger.error(f"Error getting favorites: {str(e)}")
        return jsonify({'error': 'Failed to get favorites'}), 500

@app.route('/api/favorites', methods=['POST'])
def add_favorite():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    data = request.get_json()
    
    # Check if already favorited
    existing = Favorite.query.filter_by(
        user_id=session['user_id'],
        item_id=data['item_id']
    ).first()
    
    if existing:
        return jsonify({'error': 'Item already in favorites'}), 400
    
    favorite = Favorite(
        user_id=session['user_id'],
        item_id=data['item_id']
    )
    db.session.add(favorite)
    db.session.commit()
    
    return jsonify({'message': 'Added to favorites'})

@app.route('/api/favorites/<int:item_id>', methods=['DELETE'])
def remove_favorite(item_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    Favorite.query.filter_by(
        user_id=session['user_id'],
        item_id=item_id
    ).delete()
    db.session.commit()
    
    return jsonify({'message': 'Removed from favorites'})

# Add CORS headers for static files
@app.after_request
def add_cors_headers(response):
    if request.path.startswith('/static/'):
        response.headers.update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600',
            'Cache-Control': 'public, max-age=31536000',
            'Vary': 'Origin'
        })
        
        # Set the correct content type for images
        if request.path.endswith('.jpg') or request.path.endswith('.jpeg'):
            response.headers['Content-Type'] = 'image/jpeg'
        elif request.path.endswith('.png'):
            response.headers['Content-Type'] = 'image/png'
        elif request.path.endswith('.gif'):
            response.headers['Content-Type'] = 'image/gif'
            
    return response

# Add a route to serve static files
@app.route('/static/images/<path:filename>')
def serve_image(filename):
    """Serve images with proper content type and error handling"""
    try:
        # Validate filename to prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            logger.error(f"Invalid image path requested: {filename}")
            return jsonify({'error': 'Invalid image path'}), 400
            
        image_path = os.path.join(static_folder, 'images')
        logger.info(f"Attempting to serve image from: {image_path}/{filename}")
        
        if not os.path.exists(os.path.join(image_path, filename)):
            logger.error(f"Image file not found: {filename}")
            return jsonify({'error': 'Image not found'}), 404
            
        # Determine content type
        content_type = 'image/jpeg'  # Default to JPEG
        if filename.lower().endswith('.png'):
            content_type = 'image/png'
        elif filename.lower().endswith('.gif'):
            content_type = 'image/gif'
            
        response = send_from_directory(
            image_path,
            filename,
            mimetype=content_type,
            as_attachment=False,
            max_age=31536000
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error serving image {filename}: {str(e)}")
        return jsonify({'error': 'Error serving image'}), 500

# Add new models for feedback and waste tracking
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('menu.item_id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='feedbacks')
    menu_item = db.relationship('Menu', backref='feedbacks')

class WasteTracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('menu.item_id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # Amount of food wasted in grams
    reason = db.Column(db.String(200))  # Reason for waste
    date = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    menu_item = db.relationship('Menu', backref='waste_records')
    user = db.relationship('User', backref='waste_records')

# Add new routes for feedback and waste tracking
@app.route('/api/feedback', methods=['POST'])
def add_feedback():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    data = request.get_json()
    feedback = Feedback(
        user_id=session['user_id'],
        item_id=data['item_id'],
        rating=data['rating'],
        comment=data.get('comment', '')
    )
    db.session.add(feedback)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Feedback submitted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/feedback/<int:item_id>', methods=['GET'])
def get_feedback(item_id):
    feedbacks = Feedback.query.filter_by(item_id=item_id).order_by(Feedback.created_at.desc()).all()
    return jsonify([{
        'id': f.id,
        'user': f.user.username,
        'rating': f.rating,
        'comment': f.comment,
        'created_at': f.created_at.isoformat()
    } for f in feedbacks])

@app.route('/api/waste/track', methods=['POST'])
def track_waste():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    waste = WasteTracking(
        item_id=data['item_id'],
        quantity=data['quantity'],
        reason=data.get('reason', ''),
        recorded_by=session['user_id']
    )
    db.session.add(waste)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Waste record added successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/waste/stats', methods=['GET'])
def get_waste_stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    # Get waste statistics by item
    stats = db.session.query(
        WasteTracking.item_id,
        Menu.item_name,
        db.func.sum(WasteTracking.quantity).label('total_waste'),
        db.func.count(WasteTracking.id).label('waste_count')
    ).join(Menu).group_by(WasteTracking.item_id).all()
    
    return jsonify([{
        'item_id': s.item_id,
        'item_name': s.item_name,
        'total_waste': float(s.total_waste),
        'waste_count': s.waste_count
    } for s in stats])

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 