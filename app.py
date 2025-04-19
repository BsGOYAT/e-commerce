from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aapki_apni_dukan.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Context processors
@app.context_processor
def inject_cart_count():
    if current_user.is_authenticated:
        cart_items_count = Cart.query.filter_by(user_id=current_user.id).count()
    else:
        cart_items_count = 0
    return dict(cart_items_count=cart_items_count)

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    cart = db.relationship('Cart', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Seller(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    business_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    products = db.relationship('Product', backref='seller', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    category = db.Column(db.String(50))
    stock = db.Column(db.Integer, default=10)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'))

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    product = db.relationship('Product')

class Order(db.Model):
    __tablename__ = 'orders'  # Explicitly set table name to avoid SQLite issues
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='Placed')
    email = db.Column(db.String(120), nullable=False)
    
    # Shipping address fields
    shipping_address = db.relationship('ShippingAddress', backref='order', uselist=False, lazy=True, cascade="all, delete-orphan")
    
    # Order items
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

class OrderItem(db.Model):
    __tablename__ = 'order_items'  # Explicitly set table name
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product = db.relationship('Product')

class ShippingAddress(db.Model):
    __tablename__ = 'shipping_addresses'  # Explicitly set table name
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    # Try loading as a regular user first
    user = User.query.get(int(user_id))
    if user:
        return user
    # If not found, try loading as a seller
    return Seller.query.get(int(user_id))

def create_sample_seller():
    if not Seller.query.filter_by(username='seller').first():
        try:
            seller = Seller(
                username='seller',
                email='seller@example.com',
                business_name='Sample Store',
                phone='1234567890',
                address='123 Sample Street'
            )
            seller.set_password('password')
            db.session.add(seller)
            db.session.commit()
            print("Sample seller created successfully")
            return seller
        except Exception as e:
            db.session.rollback()
            print(f"Error creating sample seller: {e}")
            return None
    else:
        return Seller.query.filter_by(username='seller').first()

def create_sample_products():
    # Get or create sample seller
    seller = create_sample_seller()
    if not seller:
        print("Failed to create sample seller")
        return
    
    # Clear all existing products first
    Product.query.delete()
    db.session.commit()
    
    sample_products = [
        {
            'name': 'iPhone 16 256 GB',
            'price': 150000.00,
            'description': 'iPhone 16 256 GB: 5G Mobile Phone with Camera Control, A18 Chip and a Big Boost in Battery Life. Works with AirPods; Gold',
            'image_url': 'https://m.media-amazon.com/images/I/71pX3D7P9YL._AC_SL1500_.jpg',
            'category': 'Electronics',
            'stock': 10,
            'seller_id': seller.id
        },
        {
            'name': 'Boult Q Over Ear Bluetooth Headphones',
            'price': 1900.99,
            'description': 'Boult Q Over Ear Bluetooth Headphones with 70H Playtime, 40mm Bass Drivers, Zen™ ENC Mic, Type-C Fast Charging, 4 EQ Modes, Bluetooth 5.4, AUX Option, Easy Controls, IPX5 Wireless Headphones (Beige)',
            'image_url': 'https://m.media-amazon.com/images/I/61A8x8fO0oL._AC_SL1500_.jpg',
            'category': 'Electronics',
            'stock': 10,
            'seller_id': seller.id
        },
        {
            'name': 'Samsung Galaxy Tab A9+',
            'price': 15999.00,
            'description': 'Samsung Galaxy Tab A9+ WiFi Tablet, 27.94 cm (11.0") Display, 8GB RAM, 128GB Storage, Long Lasting 7040 mAh Battery, Quad Speakers with Dolby Atmos, Graphite',
            'image_url': 'https://m.media-amazon.com/images/I/61b2BrYtVGL._SL1500_.jpg',
            'category': 'Electronics',
            'stock': 10,
            'seller_id': seller.id
        },
        {
            'name': 'Noise ColorFit Pro 5',
            'price': 4999.00,
            'description': 'Noise ColorFit Pro 5 Smart Watch with 1.85" AMOLED Display, Bluetooth Calling, Metallic Build, Functional Crown, Always on Display, Resolution 390x450 pixels, Smart Gestures, Cloud Grey',
            'image_url': 'https://m.media-amazon.com/images/I/617eiZeFtNL._SL1500_.jpg',
            'category': 'Electronics',
            'stock': 10,
            'seller_id': seller.id
        },
        {
            'name': 'OnePlus Nord Buds 3',
            'price': 2999.00,
            'description': 'OnePlus Nord Buds 3 Bluetooth Truly Wireless in Ear Earbuds with Mic, 49dB ANC, 12.4mm Titanium Drivers, IP55 Rating, Upto 44 Hrs Music Playtime, 4-Mic with AI Clear Call Algorithm, in Ear Detection (Starry Black)',
            'image_url': 'https://m.media-amazon.com/images/I/61S7ZK+-O9L._SL1500_.jpg',
            'category': 'Electronics',
            'stock': 10,
            'seller_id': seller.id
        },
        {
            'name': 'ZEBRONICS Zeb-Transformer-M',
            'price': 1499.00,
            'description': 'ZEBRONICS Zeb-Transformer-M Gaming Keyboard and Mouse Combo with Multimedia Keys, Rainbow LED Effect, 1200 DPI Mouse & braided Cable (Black)',
            'image_url': 'https://m.media-amazon.com/images/I/71uY7aSFKcL._SL1500_.jpg',
            'category': 'Electronics',
            'stock': 10,
            'seller_id': seller.id
        },
        {
            'name': 'Redmi Note 13 5G',
            'price': 15999.00,
            'description': 'Redmi Note 13 5G Coral Purple 6GB RAM 128GB ROM | 108MP Main Camera | Snapdragon 685 | 6.67" AMOLED Display 120Hz | 5000mAh Battery | 33W Fast Charging | 2 Years Warranty',
            'image_url': 'https://m.media-amazon.com/images/I/61R+O5ooiDL._SL1500_.jpg',
            'category': 'Electronics',
            'stock': 10,
            'seller_id': seller.id
        },
        {
            'name': 'AGARO Royal Stand Mixer',
            'price': 6999.00,
            'description': 'AGARO Royal Stand Mixer, 1000W, 5 Liters, Stainless Steel Bowl, 8 Speeds with Pulse Function, Includes Beater/Whisk/Dough Hook, (Black)',
            'image_url': 'https://m.media-amazon.com/images/I/616VmoxR6ML._SL1280_.jpg',
            'category': 'Home & Kitchen',
            'stock': 10,
            'seller_id': seller.id
        },
        {
            'name': 'American Tourister Valex',
            'price': 2499.00,
            'description': 'American Tourister Valex 28 Ltrs Medium Casual Backpack Navy Blue, Laptop Bag for Men & Women with Bottle Pocket & Organizer, Backpack for Office Use',
            'image_url': 'https://m.media-amazon.com/images/I/81whJ5OL2cL._SL1500_.jpg',
            'category': 'Fashion',
            'stock': 10,
            'seller_id': seller.id
        },
        {
            'name': 'Philips Hair Straightener',
            'price': 1299.00,
            'description': 'Philips Hair Straightener with 1.8M Swivel Cord, Silk Effect, 210 Degree Heat Temperature, Multiple Temperature Settings for Different Hair Types, Plate Length: 9.4 cm, 2 Years Warranty, BHS376/10',
            'image_url': 'https://m.media-amazon.com/images/I/61C-Og83M-L._SL1500_.jpg',
            'category': 'Beauty & Personal Care',
            'stock': 10,
            'seller_id': seller.id
        },
        {
            'name': 'ASIAN Men\'s Wonder Sports Shoes',
            'price': 649.00,
            'description': 'ASIAN Men\'s Wonder-13 Sports Running,Walking & Gym Shoes with Lightweight Eva Sole Extra Jump Casual Sneaker Shoes for Men\'s & Boy\'s',
            'image_url': 'https://m.media-amazon.com/images/I/61hMQOHmEIL._UL1100_.jpg',
            'category': 'Fashion',
            'stock': 10,
            'seller_id': seller.id
        },
        {
            'name': 'Prestige Electric Kettle',
            'price': 749.00,
            'description': 'Prestige Electric Kettle PKOSS 1.8 litre, 1500W with Auto Shut-off & Boil Dry Protection (Steel)',
            'image_url': 'https://m.media-amazon.com/images/I/51DGcy8eBCL._SL1000_.jpg',
            'category': 'Home & Kitchen',
            'stock': 10,
            'seller_id': seller.id
        },
        {
            'name': 'The Psychology of Money',
            'price': 210.00,
            'description': 'The Psychology of Money: Timeless Lessons on Wealth, Greed, and Happiness - Paperback by Morgan Housel - International Bestseller',
            'image_url': 'https://m.media-amazon.com/images/I/41cWqh0OeQL._SY445_SX342_.jpg',
            'category': 'Books',
            'stock': 10,
            'seller_id': seller.id
        },
        {
            'name': 'Ikigai: Japanese Secret',
            'price': 318.00,
            'description': 'Ikigai: The Japanese Secret to a Long and Happy Life (International Bestseller) - Hardcover by Héctor García',
            'image_url': 'https://m.media-amazon.com/images/I/814L+vq01mL._SY466_.jpg',
            'category': 'Books',
            'stock': 10,
            'seller_id': seller.id
        },
        {
            'name': 'Lakme Cushion Matte Lipstick',
            'price': 299.00,
            'description': 'Lakme 9TO5 Weightless Matte Mousse Lip & Cheek Color, Crimson Silk, 9 g - Long-lasting, Lightweight, Matte Finish',
            'image_url': 'https://m.media-amazon.com/images/I/51VJrk5c9CL._SL1500_.jpg',
            'category': 'Beauty & Personal Care',
            'stock': 10,
            'seller_id': seller.id
        }
    ]
    
    try:
        for product_data in sample_products:
            product = Product(**product_data)
            db.session.add(product)
        db.session.commit()
        print("Sample products created successfully")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating sample products: {e}")

# Create a default user for testing
def create_test_user():
    # First check if the user already exists by both username and email
    if not User.query.filter_by(username='test').first() and not User.query.filter_by(email='test@example.com').first():
        try:
            user = User(username='test', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            print("Test user created successfully")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating test user: {e}")
    else:
        print("Test user already exists")
            
# Create a specific user
def create_specific_user(username, email, password):
    # Check if the user already exists by either username or email
    if not User.query.filter_by(username=username).first() and not User.query.filter_by(email=email).first():
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print(f"User {username} created successfully")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating user {username}: {e}")
    else:
        print(f"User with username {username} or email {email} already exists")

# Routes
@app.route('/')
def home():
    try:
        products = Product.query.all()
        return render_template('index.html', products=products)
    except Exception as e:
        print(f"Error fetching products: {e}")
        return render_template('index.html', products=[])

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    similar_products = Product.query.filter_by(category=product.category).filter(Product.id != product.id).limit(3).all()
    return render_template('product_detail.html', product=product, similar_products=similar_products)

@app.route('/products')
def products():
    try:
        products = Product.query.all()
        return render_template('products.html', products=products)
    except Exception as e:
        print(f"Error fetching products: {e}")
        return render_template('products.html', products=[])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if isinstance(current_user, Seller):
            return redirect(url_for('seller_dashboard'))
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_type = request.form.get('user_type', 'customer')
        
        if user_type == 'customer':
            user = User.query.filter_by(username=username).first()
        else:
            user = Seller.query.filter_by(username=username).first()
            
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            if isinstance(user, Seller):
                return redirect(next_page or url_for('seller_dashboard'))
            return redirect(next_page or url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/seller/login', methods=['GET', 'POST'])
def seller_login():
    if current_user.is_authenticated:
        if isinstance(current_user, Seller):
            return redirect(url_for('seller_dashboard'))
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        seller = Seller.query.filter_by(username=username).first()
        if seller and seller.check_password(password):
            login_user(seller)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('seller_dashboard'))
        else:
            flash('Invalid seller credentials', 'danger')
            return redirect(url_for('login'))
    
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if the request is AJAX
    is_ajax_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Get quantity from request
    if is_ajax_request and request.is_json:
        try:
            data = request.get_json()
            quantity = int(data.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1
    else:
        quantity = 1
        
    # Ensure quantity is at least 1
    if quantity < 1:
        quantity = 1
    
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = Cart(user_id=current_user.id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    
    # Return JSON response for AJAX requests
    if is_ajax_request:
        return jsonify({
            'success': True,
            'message': f'{product.name} added to your cart!',
            'item_count': Cart.query.filter_by(user_id=current_user.id).count()
        })
    
    # For regular form submissions
    flash('Product added to cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/buy_now/<int:product_id>', methods=['GET', 'POST'])
@login_required
def buy_now(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Get quantity from request
    try:
        quantity = int(request.form.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1
        
    # Ensure quantity is at least 1
    if quantity < 1:
        quantity = 1
    
    # Add to cart first
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = Cart(user_id=current_user.id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    
    # Redirect to checkout page (which will be the cart page for now)
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:cart_item_id>', methods=['POST'])
@login_required
def remove_from_cart(cart_item_id):
    cart_item = Cart.query.get_or_404(cart_item_id)
    
    # Check if this cart item belongs to the current user
    if cart_item.user_id != current_user.id:
        flash('You are not authorized to remove this item.', 'danger')
        return redirect(url_for('cart'))
    
    product_name = cart_item.product.name
    db.session.delete(cart_item)
    db.session.commit()
    
    flash(f'{product_name} removed from cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/update_quantity/<int:cart_item_id>', methods=['POST'])
@login_required
def update_quantity(cart_item_id):
    cart_item = Cart.query.get_or_404(cart_item_id)
    
    # Check if this cart item belongs to the current user
    if cart_item.user_id != current_user.id:
        flash('You are not authorized to update this item.', 'danger')
        return redirect(url_for('cart'))
    
    new_quantity = int(request.form.get('quantity', 1))
    if new_quantity < 1:
        new_quantity = 1
    
    cart_item.quantity = new_quantity
    db.session.commit()
    
    flash('Cart updated successfully!', 'success')
    return redirect(url_for('cart'))

# Checkout flow
@app.route('/checkout/address', methods=['GET', 'POST'])
@login_required
def checkout_address():
    # Check if cart is empty
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty.', 'danger')
        return redirect(url_for('cart'))
    
    if request.method == 'POST':
        # Store address in session
        session['checkout_address'] = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'state': request.form.get('state'),
            'pincode': request.form.get('pincode')
        }
        return redirect(url_for('checkout_payment'))
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('checkout_address.html', cart_items=cart_items, total=total)

@app.route('/checkout/payment', methods=['GET', 'POST'])
@login_required
def checkout_payment():
    # Check if address is provided
    if 'checkout_address' not in session:
        flash('Please provide your shipping address.', 'danger')
        return redirect(url_for('checkout_address'))
    
    # Check if cart is empty
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty.', 'danger')
        return redirect(url_for('cart'))
    
    # Remove cart items with missing products and validate products
    valid_cart_items = []
    for item in cart_items:
        if item.product and item.product.price and item.product.stock:
            valid_cart_items.append(item)
        else:
            db.session.delete(item)
    
    if not valid_cart_items:
        db.session.commit()
        flash('Your cart contains invalid items. They have been removed.', 'warning')
        return redirect(url_for('cart'))
    
    if request.method == 'POST':
        try:
            # Get payment info
            payment_method = request.form.get('payment_method')
            if not payment_method:
                flash('Please select a payment method.', 'danger')
                return redirect(url_for('checkout_payment'))
            
            # Calculate totals
            subtotal = sum(item.product.price * item.quantity for item in valid_cart_items)
            total_amount = subtotal  # No shipping cost for now
            
            # Create new order
            order = Order(
                user_id=current_user.id,
                total_amount=total_amount,
                subtotal=subtotal,
                payment_method=payment_method,
                email=session['checkout_address']['email']
            )
            db.session.add(order)
            db.session.flush()  # This gives us the order ID
            
            # Create shipping address
            address_data = session['checkout_address']
            shipping_address = ShippingAddress(
                order_id=order.id,
                name=address_data['name'],
                phone=address_data['phone'],
                address=address_data['address'],
                city=address_data['city'],
                state=address_data['state'],
                pincode=address_data['pincode']
            )
            db.session.add(shipping_address)
            
            # Create order items
            for item in valid_cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    product_name=item.product.name,
                    price=item.product.price,
                    quantity=item.quantity
                )
                db.session.add(order_item)
            
            # Store payment info in session
            if payment_method == 'card':
                card_last4 = request.form.get('card_number', '')[-4:] if request.form.get('card_number') else '****'
                session['checkout_payment'] = {
                    'payment_method': payment_method,
                    'card_name': request.form.get('card_name'),
                    'card_last4': card_last4
                }
            elif payment_method == 'upi':
                session['checkout_payment'] = {
                    'payment_method': payment_method,
                    'upi_id': request.form.get('upi_id')
                }
            
            # Clear cart and commit all changes
            Cart.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()
            
            # Store order ID in session for confirmation page
            session['order_id'] = order.id
            
            return redirect(url_for('order_confirmation'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while processing your order. Please try again.', 'danger')
            print(f"Error processing order: {e}")
            return redirect(url_for('checkout_payment'))
    
    # Calculate total for display
    total = sum(item.product.price * item.quantity for item in valid_cart_items)
    return render_template('checkout_payment.html', cart_items=valid_cart_items, total=total, address=session['checkout_address'])

@app.route('/order/confirmation')
@login_required
def order_confirmation():
    # Check if we have order ID in session
    if 'order_id' not in session:
        flash('No order information found.', 'danger')
        return redirect(url_for('cart'))
    
    # Get order details
    order = Order.query.get(session['order_id'])
    if not order or order.user_id != current_user.id:
        flash('Order not found.', 'danger')
        return redirect(url_for('cart'))
    
    # Clear checkout data from session
    session.pop('checkout_address', None)
    session.pop('checkout_payment', None)
    session.pop('order_id', None)
    
    return render_template('order_confirmation.html', order=order)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=user_orders)

@app.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Ensure the order belongs to current user
    if order.user_id != current_user.id:
        flash('You are not authorized to view this order.', 'danger')
        return redirect(url_for('orders'))
    
    return render_template('order_detail.html', order=order)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    category = request.args.get('category', 'all')
    
    if not query:
        return redirect(url_for('home'))
    
    # Build the search query
    search_query = f"%{query}%"
    
    if category and category != 'all':
        # Search in specific category
        products = Product.query.filter(
            (Product.name.ilike(search_query) | 
             Product.description.ilike(search_query)) &
            (Product.category == category)
        ).all()
    else:
        # Search in all categories
        products = Product.query.filter(
            Product.name.ilike(search_query) | 
            Product.description.ilike(search_query)
        ).all()
    
    return render_template('search_results.html', 
                          products=products, 
                          query=query, 
                          category=category,
                          count=len(products))

if __name__ == '__main__':
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        
        # Create initial data
        create_sample_seller()
        create_sample_products()
        create_test_user()
        create_specific_user('bhawish', 'bhawishgoyat047@gmail.com', 'pwd')
        
        print("Database initialized successfully!")
    app.run(debug=True) 