import os
from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'rachna_agri_super_secret_key')

# Format Render DATABASE_URL if it uses postgres:// instead of postgresql://
db_url = os.environ.get('DATABASE_URL', 'sqlite:///khata.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.after_request
def inject_theme_script(response):
    if response.content_type and 'text/html' in response.content_type:
        data = response.get_data(as_text=True)
        if '</body>' in data:
            script = f'<script src="{url_for("static", filename="js/app.js")}"></script></body>'
            data = data.replace('</body>', script)
            response.set_data(data)
    return response

# Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default='admin')

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50))
    address = db.Column(db.String(200))
    total_balance = db.Column(db.Float, default=0.0)
    transactions = db.relationship('Transaction', backref='customer', lazy=True, cascade="all, delete-orphan")

class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(150), nullable=False)
    stock_count = db.Column(db.Integer, default=0)
    purchase_price = db.Column(db.Float)
    sale_price = db.Column(db.Float)
    stock_ledgers = db.relationship('StockLedger', backref='inventory', lazy=True, cascade="all, delete-orphan")

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(100))
    stock_ledgers = db.relationship('StockLedger', backref='transaction', lazy=True, cascade="all, delete-orphan")

class StockLedger(db.Model):
    __tablename__ = 'stock_ledger'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('inventory.id'))
    movement_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'))

# Ensure DB initialized via app context avoiding circular imports / push logic
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
            
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            flash('Username already exists')
            return redirect(url_for('register'))
            
        password_hash = generate_password_hash(password)
        new_user = User(username=username, password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # 1. Total Stock Value
    stock_value_result = db.session.query(db.func.sum(Inventory.stock_count * Inventory.purchase_price)).scalar()
    total_stock_value = float(stock_value_result) if stock_value_result else 0.0

    # 2. Total Receivables
    receivables_result = db.session.query(db.func.sum(Customer.total_balance)).filter(Customer.total_balance > 0).scalar()
    total_receivables = float(receivables_result) if receivables_result else 0.0

    # 3. Daily Sales
    today = date.today().isoformat()
    daily_sales_result = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == 'Sale/Credit', Transaction.date.like(f'{today}%')).scalar()
    daily_sales = float(daily_sales_result) if daily_sales_result else 0.0

    # 4. Low Stock Alerts
    low_stock_alerts = Inventory.query.filter(Inventory.stock_count < 10).count()
    
    return render_template('dashboard.html', 
                           username=session.get('username'),
                           total_stock_value=total_stock_value,
                           total_receivables=total_receivables,
                           daily_sales=daily_sales,
                           low_stock_alerts=low_stock_alerts)

@app.route('/customers', methods=['GET', 'POST'])
def customers():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')
        
        new_customer = Customer(name=name, phone=phone, address=address)
        db.session.add(new_customer)
        db.session.commit()
        
        flash('Customer added successfully!')
        return redirect(url_for('customers'))
        
    customers_list = Customer.query.order_by(Customer.name).all()
    return render_template('customers.html', username=session.get('username'), customers=customers_list)

@app.route('/customer/<int:id>', methods=['GET'])
def customer_profile(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    customer = Customer.query.get(id)
    if not customer:
        return "Customer not found", 404
        
    transactions = Transaction.query.filter_by(customer_id=id).order_by(Transaction.date.desc()).all()
    
    status = 'Reliable'
    if customer.total_balance > 0:
        thirty_days_ago = (date.today() - timedelta(days=30)).isoformat()
        old_sales_count = Transaction.query.filter(Transaction.customer_id == id, Transaction.type == 'Sale/Credit', Transaction.date < thirty_days_ago).count()
        if old_sales_count > 0:
            status = 'Overdue'
            
    return render_template('customer_profile.html', username=session.get('username'), customer=customer, transactions=transactions, status=status)

@app.route('/customer/<int:id>/print', methods=['GET'])
def print_khata(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    customer = Customer.query.get(id)
    if not customer:
        return "Not found", 404
    transactions = Transaction.query.filter_by(customer_id=id).order_by(Transaction.date.desc()).all()
    return render_template('print_khata.html', customer=customer, transactions=transactions)

@app.route('/customer/<int:id>/transaction', methods=['POST'])
def add_transaction(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    customer = Customer.query.get(id)
    if not customer:
        return "Not found", 404
        
    tx_type = request.form['type']
    amount = float(request.form['amount'])
    payment_method = request.form.get('payment_method', '')
    
    today = datetime.now().isoformat()
    
    new_tx = Transaction(date=today, customer_id=id, type=tx_type, amount=amount, payment_method=payment_method)
    db.session.add(new_tx)
    
    if tx_type == 'Sale/Credit':
        customer.total_balance += amount
    elif tx_type == 'Payment':
        customer.total_balance -= amount
        
    db.session.commit()
    flash('Transaction added successfully.')
    return redirect(url_for('customer_profile', id=id))

@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Auto-seed logic if Inventory table is completely empty
    if Inventory.query.count() == 0:
        seed_product = Inventory(product_name='Lambda Pesticide (1 Liter)', stock_count=50, purchase_price=800.0, sale_price=1200.0)
        db.session.add(seed_product)
        db.session.commit()

    if request.method == 'POST':
        product_name = request.form['product_name']
        purchase_price = float(request.form['purchase_price'])
        sale_price = float(request.form['sale_price'])
        stock_count = int(request.form['stock_count'])
        
        new_product = Inventory(product_name=product_name, stock_count=stock_count, purchase_price=purchase_price, sale_price=sale_price)
        db.session.add(new_product)
        db.session.commit()
        
        flash('Product added to inventory!')
        return redirect(url_for('inventory'))
        
    products = Inventory.query.order_by(Inventory.product_name).all()
    customers_list = Customer.query.order_by(Customer.name).all()
    
    return render_template('inventory.html', username=session.get('username'), inventory=products, customers=customers_list)

@app.route('/inventory/<int:id>/quick_sale', methods=['POST'])
def quick_sale(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    customer_id = request.form.get('customer_id')
    
    if not customer_id:
        flash('Please select a customer for the Quick Sale.')
        return redirect(url_for('inventory'))
        
    product = Inventory.query.get(id)
    customer = Customer.query.get(customer_id)
    
    if not product or product.stock_count <= 0:
        flash(f'Cannot process Quick Sale. Item out of stock!')
        return redirect(url_for('inventory'))
    
    # 1. Decrement Stock
    product.stock_count -= 1
    
    # 2. Increment Customer Balance
    sale_price = product.sale_price
    customer.total_balance += sale_price
    
    today = datetime.now().isoformat()
    # 3. Add to Transactions
    new_tx = Transaction(date=today, customer_id=customer_id, type='Sale/Credit', amount=sale_price, payment_method=f'Quick Sale: {product.product_name}')
    db.session.add(new_tx)
    # Flush to get the new transaction ID
    db.session.flush()
    
    # 4. Add to Stock Ledger
    new_ledger = StockLedger(date=today, product_id=id, movement_type='Stock_Out', quantity=1, transaction_id=new_tx.id)
    db.session.add(new_ledger)
                 
    db.session.commit()
    flash(f'Quick Sale successful! Billed Rs. {sale_price} to customer.')
    return redirect(url_for('inventory'))

@app.route('/lending')
def lending():
    if 'user_id' not in session: return redirect(url_for('login'))
    lending_customers = Customer.query.filter(Customer.total_balance > 0).order_by(Customer.total_balance.desc()).all()
    return render_template('lending.html', username=session.get('username'), customers=lending_customers)

@app.route('/reports')
def reports():
    if 'user_id' not in session: return redirect(url_for('login'))
    today = date.today().isoformat()
    
    # Calculate today's total sales
    sales_result = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == 'Sale/Credit', Transaction.date.like(f'{today}%')).scalar()
    today_sales = float(sales_result) if sales_result else 0.0
    
    # Calculate today's profit
    try:
        profit_result = db.session.query(
            db.func.sum((Inventory.sale_price - Inventory.purchase_price) * StockLedger.quantity)
        ).select_from(Inventory) \
         .join(StockLedger, StockLedger.product_id == Inventory.id) \
         .join(Transaction, StockLedger.transaction_id == Transaction.id) \
         .filter(Transaction.type == 'Sale/Credit', Transaction.date.like(f'{today}%')).scalar()
        today_profit = float(profit_result) if profit_result else 0.0
    except Exception as e:
        today_profit = 0.0
    
    return render_template('reports.html', username=session.get('username'), today_sales=today_sales, today_profit=today_profit)

@app.route('/backup')
def backup():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # Render fallback conditional
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url and db_url.startswith('postgres'):
        flash('Cloud database backend detected. Backup must be performed directly from the Render Dashboard.')
        return redirect(url_for('reports'))
        
    return send_file('khata.db', as_attachment=True, download_name='khata_backup.db')

@app.route('/customer/<int:id>/delete', methods=['POST'])
def delete_customer(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    tx_count = Transaction.query.filter_by(customer_id=id).count()
    if tx_count > 0:
        flash('Cannot delete customer! Please verify they have no transactional history first.')
    else:
        customer = Customer.query.get(id)
        if customer:
            db.session.delete(customer)
            db.session.commit()
            flash('Customer safely deleted.')
            
    return redirect(url_for('customers'))

@app.route('/inventory/<int:id>/delete', methods=['POST'])
def delete_inventory(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    tx_count = StockLedger.query.filter_by(product_id=id).count()
    if tx_count > 0:
        flash('Cannot delete product! Valid ledger movement records exist.')
    else:
        product = Inventory.query.get(id)
        if product:
            db.session.delete(product)
            db.session.commit()
            flash('Product safely deleted.')
            
    return redirect(url_for('inventory'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
