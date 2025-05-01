import streamlit as st
import requests
from PIL import Image
import os
import json
from datetime import datetime
import logging
from functools import lru_cache
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cache for image responses
@lru_cache(maxsize=100)
def get_image_content(image_url):
    try:
        response = requests.get(image_url, timeout=5)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        logger.error(f"Error loading image from {image_url}: {str(e)}")
        return None

# Page config
st.set_page_config(
    page_title="Smart Canteen",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
        background-color: #f5f7fa;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF6B6B;
        color: white;
        border: none;
        padding: 0.5rem;
        border-radius: 5px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #FF5252;
        transform: translateY(-2px);
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .menu-item {
        padding: 1.5rem;
        border-radius: 15px;
        background-color: white;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        transition: all 0.3s;
    }
    .menu-item:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .cart-item {
        padding: 1rem;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        margin: 0.5rem 0;
        background-color: white;
        box-shadow: 0 1px 5px rgba(0,0,0,0.05);
    }
    .title-container {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #FF6B6B 0%, #FFE66D 100%);
        color: white;
        border-radius: 0 0 30px 30px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .title-text {
        font-size: 3.5rem;
        font-weight: bold;
        margin: 0;
        padding: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .subtitle-text {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-top: 0.5rem;
        color: #fff;
    }
    .category-header {
        background: linear-gradient(135deg, #4ECDC4 0%, #556270 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1.5rem 0;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    .price-tag {
        background-color: #4ECDC4;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    .calories-tag {
        background-color: #FFE66D;
        color: #333;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        display: inline-block;
        font-size: 0.9rem;
        font-weight: bold;
    }
    .feedback-item {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #4ECDC4;
    }
    .waste-stat-item {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .waste-stat-item h4 {
        color: #4ECDC4;
        margin-bottom: 0.5rem;
    }
    hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: #e0e0e0;
    }
    </style>
""", unsafe_allow_html=True)

# Remove the old title and use only the new styled header
st.markdown("""
    <div class="title-container">
        <h1 class="title-text">🍽️ Smart Canteen</h1>
        <p class="subtitle-text">Experience the Future of Dining</p>
    </div>
""", unsafe_allow_html=True)

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'cart' not in st.session_state:
    st.session_state.cart = []

# Get API base URL from config
API_BASE_URL = st.secrets.get("api", {}).get("base_url", "https://textibhition.onrender.com")

def make_request(method, endpoint, data=None):
    """Make HTTP request to API"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return None

def login(username, password):
    response = make_request("POST", "login", {
        "username": username,
        "password": password
    })
    if response and response.status_code == 200:
        st.session_state.user = response.json()['user']
        return True
    return False

def register(username, email, password):
    response = make_request("POST", "register", {
        "username": username,
        "email": email,
        "password": password
    })
    return response and response.status_code == 201

def load_menu():
    response = make_request("GET", "/api/menu")
    if response and response.status_code == 200:
        return response.json()
    st.error("Unable to load menu. Please try again later.")
    return []

def get_cart():
    response = make_request("GET", "cart")
    if response and response.status_code == 200:
        return response.json()
    return []

def add_to_cart(item_id, quantity=1):
    response = make_request("POST", "cart", {
        "item_id": item_id,
        "quantity": quantity
    })
    return response and response.json().get('success', False)

def remove_from_cart(item_id):
    response = make_request("DELETE", f"cart/{item_id}")
    return response and response.status_code == 200

def create_order(cart_items):
    response = make_request("POST", "orders")
    if response:
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json()
            st.error(error_data.get('error', 'Failed to create order'))
    return None

def get_orders():
    response = make_request("GET", "orders")
    if response and response.status_code == 200:
        return response.json()
    return []

def update_order_status(order_id, status):
    response = make_request("PUT", f"orders/{order_id}/status", {"status": status})
    return response and response.status_code == 200

def track_order(order_id):
    response = make_request("GET", f"orders/track/{order_id}")
    if response and response.status_code == 200:
        return response.json()
    return None

def get_favorites():
    response = make_request("GET", "favorites")
    if response and response.status_code == 200:
        return response.json()
    return []

def add_favorite(item_id):
    response = make_request("POST", "favorites", {"item_id": item_id})
    return response and response.status_code == 200

def remove_favorite(item_id):
    response = make_request("DELETE", f"favorites/{item_id}")
    return response and response.status_code == 200

def update_item_availability(item_id, is_available):
    response = make_request("PUT", f"menu/{item_id}/availability", {"is_available": is_available})
    return response and response.status_code == 200

# Add admin functions
def get_inventory():
    response = make_request("GET", "admin/inventory")
    if response and response.status_code == 200:
        return response.json()
    return []

def update_inventory(item_id, data):
    response = make_request("PUT", f"admin/inventory/{item_id}", data)
    return response and response.status_code == 200

def get_low_stock():
    response = make_request("GET", "admin/low-stock")
    if response and response.status_code == 200:
        return response.json()
    return []

def bulk_update_inventory(items):
    response = make_request("POST", "admin/bulk-update", items)
    return response and response.status_code == 200

def get_reorder_notifications():
    response = make_request("GET", "admin/reorder-notifications")
    if response and response.status_code == 200:
        return response.json()
    return []

def process_reorder_notification(notification_id):
    response = make_request("PUT", f"admin/reorder-notifications/{notification_id}")
    return response and response.status_code == 200

def submit_feedback(item_id, rating, comment):
    response = make_request("POST", "feedback", {
        "item_id": item_id,
        "rating": rating,
        "comment": comment
    })
    return response and response.status_code == 200

def get_item_feedback(item_id):
    response = make_request("GET", f"feedback/{item_id}")
    if response and response.status_code == 200:
        return response.json()
    return []

def track_waste(item_id, quantity, reason):
    response = make_request("POST", "waste/track", {
        "item_id": item_id,
        "quantity": quantity,
        "reason": reason
    })
    return response and response.status_code == 200

def get_waste_stats():
    response = make_request("GET", "waste/stats")
    if response and response.status_code == 200:
        return response.json()
    return []

def display_menu():
    st.title("Menu")
    
    # Get menu items from API
    response = make_request("GET", "/api/menu")
    if response and response.status_code == 200:
        menu_items = response.json()
        
        # Group items by category
        categories = {}
        for item in menu_items:
            if item['is_available']:  # Only show available items
                if item['category'] not in categories:
                    categories[item['category']] = []
                categories[item['category']].append(item)
        
        # Display items by category
        for category, items in categories.items():
            st.markdown(f'<div class="category-header"><h2>{category}</h2></div>', unsafe_allow_html=True)
            
            for item in items:
                with st.container():
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        try:
                            # Load and display image
                            image_url = f"{API_BASE_URL}{item['image_url']}"
                            response = requests.get(image_url)
                            if response.status_code == 200:
                                image = Image.open(BytesIO(response.content))
                                st.image(image, width=300)
                        except Exception as e:
                            st.error(f"Error loading image: {str(e)}")
                        
                        st.markdown(f"""
                            <div class="menu-item">
                                <h3>{item['item_name']}</h3>
                                <div class="price-tag">₹{item['price']:.2f}</div>
                                <div class="calories-tag">{item['calories']} cal</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Add to cart button
                        if st.button(f"Add to Cart", key=f"add_{item['item_id']}"):
                            if st.session_state.user:
                                if add_to_cart(item['item_id']):
                                    st.success(f"Added {item['item_name']} to cart!")
                            else:
                                st.warning("Please login to add items to cart")
                    
                    with col2:
                        if st.session_state.user:
                            st.subheader("Your Feedback")
                            rating = st.slider("Rating", 1, 5, 5, key=f"rating_{item['item_id']}")
                            comment = st.text_area("Comment", key=f"comment_{item['item_id']}", height=100)
                            if st.button("Submit Feedback", key=f"feedback_{item['item_id']}"):
                                if submit_feedback(item['item_id'], rating, comment):
                                    st.success("Thank you for your feedback!")
                            
                            # Show existing feedback
                            st.markdown("### Previous Feedback")
                            feedbacks = get_item_feedback(item['item_id'])
                            if feedbacks:
                                for feedback in feedbacks[:3]:  # Show last 3 feedbacks
                                    st.markdown(f"""
                                        <div class="feedback-item">
                                            <p>{'⭐' * feedback['rating']}</p>
                                            <p><i>"{feedback['comment']}"</i></p>
                                            <small>- {feedback['user']}</small>
                                        </div>
                                    """, unsafe_allow_html=True)
                                if len(feedbacks) > 3:
                                    with st.expander("View all feedback"):
                                        for feedback in feedbacks[3:]:
                                            st.markdown(f"""
                                                <div class="feedback-item">
                                                    <p>{'⭐' * feedback['rating']}</p>
                                                    <p><i>"{feedback['comment']}"</i></p>
                                                    <small>- {feedback['user']}</small>
                                                </div>
                                            """, unsafe_allow_html=True)
                            else:
                                st.info("No feedback yet. Be the first to review!")
                        else:
                            st.info("Please login to give feedback")
                    
                    st.markdown("<hr>", unsafe_allow_html=True)

# Title and header
st.title("🍽️ Canteen Management System")
st.markdown("---")

# Sidebar - Login/Register
st.sidebar.title("Account")
if st.session_state.user is None:
    tab1, tab2 = st.sidebar.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            if submit:
                if login(username, password):
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Username")
            email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Register")
            if submit:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif register(new_username, email, new_password):
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Registration failed")
else:
    st.sidebar.write(f"Welcome, {st.session_state.user['username']}!")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

# Navigation
if st.session_state.user is not None:
    if st.session_state.user.get('is_admin'):
        page = st.sidebar.radio("Go to", ["Menu", "Favorites", "Cart", "Orders", "Admin Dashboard"])
    else:
        page = st.sidebar.radio("Go to", ["Menu", "Favorites", "Cart", "Orders"])
else:
    page = "Menu"

# Main content
if page == "Menu":
    display_menu()

elif page == "Favorites":
    st.header("My Favorites")
    
    favorites = get_favorites()
    if not favorites:
        st.info("You haven't added any favorites yet")
    else:
        # Group favorites by category
        categories = {}
        for item in favorites:
            category = item.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        # Display items by category
        for category, items in categories.items():
            st.subheader(category)
            cols = st.columns(3)
            
            for idx, item in enumerate(items):
                with cols[idx % 3]:
                    if item.get('image_url'):
                        image_url = f"{API_BASE_URL}{item['image_url']}"
                        logger.info(f"Attempting to load image from: {image_url}")
                        image_content = get_image_content(image_url)
                        
                        if image_content:
                            try:
                                st.image(image_content, caption=item['item_name'], use_column_width=True)
                            except Exception as e:
                                logger.error(f"Error displaying image for {item['item_name']}: {str(e)}")
                                st.warning(f"Error displaying image for {item['item_name']}")
                        else:
                            st.warning(f"Could not load image for {item['item_name']}")
                    
                    st.markdown(f"""
                        <div class="menu-item">
                            <h3>{item['item_name']}</h3>
                            <p>Price: ₹{item['price']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Add to Cart", key=f"fav_cart_{item['item_id']}"):
                            if add_to_cart(item['item_id'], 1):
                                st.success("Added to cart!")
                            else:
                                st.error("Failed to add to cart")
                    with col2:
                        if st.button("Remove", key=f"remove_fav_{item['item_id']}"):
                            if remove_favorite(item['item_id']):
                                st.success("Removed from favorites!")
                                st.rerun()

elif page == "Cart":
    st.header("Shopping Cart")
    cart_items = get_cart()
    
    if not cart_items:
        st.info("Your cart is empty")
    else:
        total = 0
        for item in cart_items:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{item['item_name']}** (₹{item['price']} × {item['quantity']})")
            with col2:
                st.write(f"₹{item['total']}")
            with col3:
                if st.button("Remove", key=f"remove_{item['id']}"):
                    if remove_from_cart(item['id']):
                        st.rerun()
            total += item['total']
        
        st.markdown("---")
        st.subheader(f"Total: ₹{total:.2f}")
        
        # Payment section
        st.markdown("### Payment")
        payment_method = st.radio("Select Payment Method", ["Credit Card", "UPI", "Cash"])
        
        if st.button("Place Order"):
            with st.spinner("Processing your order..."):
                order = create_order(cart_items)
                if order:
                    st.success(f"Order placed successfully! Order ID: {order['order_id']}")
                    st.balloons()
                    # Clear cart from session state
                    st.session_state.cart = []
                    # Rerun to update the UI
                    st.rerun()

elif page == "Orders":
    st.header("My Orders")
    
    orders = get_orders()
    if not orders:
        st.info("You haven't placed any orders yet")
    else:
        for order in orders:
            with st.expander(f"Order #{order['order_id']} - {order['status'].title()}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Order Date:** {datetime.fromisoformat(order['order_date']).strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**Total Amount:** ₹{order['total_amount']:.2f}")
                    
                    st.write("**Items:**")
                    for item in order['items']:
                        st.write(f"- {item['item_name']} (₹{item['price']} × {item['quantity']})")
                
                with col2:
                    if order['status'] == 'pending':
                        if st.button("Cancel Order", key=f"cancel_{order['order_id']}"):
                            if update_order_status(order['order_id'], 'cancelled'):
                                st.success("Order cancelled successfully!")
                                st.rerun()
                    
                    # Track order button
                    if st.button("Track Order", key=f"track_{order['order_id']}"):
                        order_details = track_order(order['order_id'])
                        if order_details:
                            st.write("**Order Status:**", order_details['status'].title())
                            st.write("**Last Updated:**", datetime.fromisoformat(order_details['order_date']).strftime('%Y-%m-%d %H:%M'))

# Add Admin Dashboard
if page == "Admin Dashboard" and st.session_state.user.get('is_admin'):
    st.header("Admin Dashboard")
    
    # Tabs for different admin functions
    tab1, tab2, tab3, tab4 = st.tabs(["Inventory Management", "Low Stock Alerts", "Reorder Notifications", "Waste Tracking"])
    
    with tab1:
        st.subheader("Inventory Management")
        
        # Bulk update section
        st.write("### Bulk Update Inventory")
        uploaded_file = st.file_uploader("Upload CSV file for bulk update", type=['csv'])
        if uploaded_file:
            import pandas as pd
            df = pd.read_csv(uploaded_file)
            if st.button("Update Inventory"):
                items = df.to_dict('records')
                if bulk_update_inventory(items):
                    st.success("Inventory updated successfully!")
                else:
                    st.error("Failed to update inventory")
        
        # Individual item updates
        st.write("### Individual Item Updates")
        inventory = get_inventory()
        if inventory:
            for item in inventory:
                with st.expander(f"{item['item_name']} ({item['category']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_quantity = st.number_input(
                            "Quantity",
                            min_value=0,
                            value=item['quantity'],
                            key=f"qty_{item['item_id']}"
                        )
                    with col2:
                        new_price = st.number_input(
                            "Price",
                            min_value=0.0,
                            value=float(item['price']),
                            step=0.5,
                            key=f"price_{item['item_id']}"
                        )
                    if st.button("Update", key=f"update_{item['item_id']}"):
                        if update_inventory(item['item_id'], {
                            'quantity': new_quantity,
                            'price': new_price
                        }):
                            st.success("Item updated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to update item")
    
    with tab2:
        st.subheader("Low Stock Alerts")
        low_stock_items = get_low_stock()
        if low_stock_items:
            for item in low_stock_items:
                st.warning(f"⚠️ {item['item_name']} is running low! Current quantity: {item['quantity']}")
                col1, col2 = st.columns(2)
                with col1:
                    new_quantity = st.number_input(
                        "New Quantity",
                        min_value=0,
                        value=item['quantity'],
                        key=f"low_stock_qty_{item['item_id']}"
                    )
                with col2:
                    if st.button("Update Quantity", key=f"low_stock_update_{item['item_id']}"):
                        if update_inventory(item['item_id'], {'quantity': new_quantity}):
                            st.success("Quantity updated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to update quantity")
        else:
            st.success("No low stock items!")
    
    with tab3:
        st.subheader("Reorder Notifications")
        notifications = get_reorder_notifications()
        if notifications:
            for notification in notifications:
                st.warning(
                    f"⚠️ Reorder needed for {notification['item_name']}!\n"
                    f"Current quantity: {notification['current_quantity']}\n"
                    f"Threshold: {notification['threshold']}\n"
                    f"Created: {notification['created_at']}"
                )
                if st.button("Mark as Processed", key=f"process_{notification['id']}"):
                    if process_reorder_notification(notification['id']):
                        st.success("Notification marked as processed!")
                        st.rerun()
                    else:
                        st.error("Failed to process notification")
        else:
            st.success("No pending reorder notifications!")
    
    with tab4:
        st.subheader("Waste Tracking")
        
        # Form to record waste
        with st.form("waste_tracking_form"):
            menu_items = load_menu()
            item_options = {item['item_name']: item['item_id'] for item in menu_items}
            
            selected_item = st.selectbox("Select Item", options=list(item_options.keys()))
            quantity = st.number_input("Waste Quantity (grams)", min_value=0.0, step=10.0)
            reason = st.text_area("Reason for Waste")
            
            if st.form_submit_button("Record Waste"):
                if track_waste(item_options[selected_item], quantity, reason):
                    st.success("Waste record added successfully!")
        
        # Display waste statistics
        st.subheader("Waste Statistics")
        stats = get_waste_stats()
        if stats:
            # Create a bar chart of waste by item
            import plotly.graph_objects as go
            
            fig = go.Figure(data=[
                go.Bar(
                    x=[s['item_name'] for s in stats],
                    y=[s['total_waste'] for s in stats],
                    text=[f"{s['total_waste']}g" for s in stats],
                    textposition='auto',
                )
            ])
            
            fig.update_layout(
                title="Total Waste by Item",
                xaxis_title="Item Name",
                yaxis_title="Total Waste (grams)",
                showlegend=False
            )
            
            st.plotly_chart(fig)
            
            # Display detailed statistics
            for stat in stats:
                st.markdown(f"""
                    <div class="waste-stat-item">
                        <h4>{stat['item_name']}</h4>
                        <p>Total Waste: {stat['total_waste']}g</p>
                        <p>Number of Records: {stat['waste_count']}</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No waste records available")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>Smart Canteen - Built with ❤️ using Flask and Streamlit</p>
        <p style='font-size: 0.8rem;'>© 2024 Smart Canteen. All rights reserved.</p>
    </div>
""", unsafe_allow_html=True) 