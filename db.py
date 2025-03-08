from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# -------------------------
# Customer & User Models
# -------------------------
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    users = db.relationship('User', backref='customer', lazy=True)
    apis = db.relationship('CustomerAPI', backref='customer', lazy=True)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # Admin flag
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)  # Nullable for admin users

    def set_password(self, password):
        """Hashes the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies the user's password."""
        return check_password_hash(self.password_hash, password)

# -------------------------
# API Subscription Models
# -------------------------
class API(db.Model):
    __tablename__ = 'apis'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    publisher = db.Column(db.String(100), nullable=False)

class CustomerAPI(db.Model):
    __tablename__ = 'customer_apis'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    api_id = db.Column(db.Integer, db.ForeignKey('apis.id'), nullable=False)

    api = db.relationship('API', backref='customer_api')

class APIService(db.Model):
   __tablename__ = 'api_services'
     id = db.Column(db.Integer, primary_key=True)
     name = db.Column(db.String(100), nullable=False)
     description = db.Column(db.Text)
     subscriptions = db.relationship('Subscription', backref='api', lazy=True)
     billing_records = db.relationship('AppliedBilling', backref='api', lazy=True)

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
      id = db.Column(db.Integer, primary_key=True)
      customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
      api_id = db.Column(db.Integer, db.ForeignKey('api_services.id'), nullable=False)

class BillingLogic(db.Model):
        __tablename__ = 'billing_logic'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        description = db.Column(db.Text)
        applied_billing = db.relationship('AppliedBilling', backref='billing_logic', lazy=True)

class AppliedBilling(db.Model):
        __tablename__ = 'applied_billing'
        id = db.Column(db.Integer, primary_key=True)
        customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
        api_id = db.Column(db.Integer, db.ForeignKey('api_services.id'), nullable=False)
        billing_logic_id = db.Column(db.Integer, db.ForeignKey('billing_logic.id'), nullable=False)
        price = db.Column(db.Float, nullable=False)
        currency = db.Column(db.String(3), nullable=False)
        total_amount = db.Column(db.Float, nullable=False)
        billing_date = db.Column(db.DateTime, default=datetime.utcnow)


class APIPricing(db.Model):
    __tablename__ = 'api_pricing'
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.Integer, db.ForeignKey('api_service.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')  # Currency in 3-letter code
    api = db.relationship('APIService', backref='pricing')

# -------------------------
# Billing Models
# -------------------------
class Billing(db.Model):
    __tablename__ = 'billing'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    api_id = db.Column(db.Integer, db.ForeignKey('apis.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False)  # USD, EUR, etc.
    total_amount = db.Column(db.Float, nullable=False)
    billing_date = db.Column(db.DateTime, default=datetime.utcnow)
    billing_logic = db.Column(db.String(255), nullable=True)  # Description of billing logic

    customer = db.relationship('Customer', backref='billing_entries')
    api = db.relationship('API', backref='billing_entries')

    def __init__(self, customer_id, api_id, price, currency, total_amount, billing_logic=None):
        self.customer_id = customer_id
        self.api_id = api_id
        self.price = price
        self.currency = currency
        self.total_amount = total_amount
        self.billing_logic = billing_logic




# -------------------------
# Logging Configuration
# -------------------------
class LogConfig(db.Model):
    __tablename__ = 'log_config'
    id = db.Column(db.Integer, primary_key=True)
    log_to_file = db.Column(db.Boolean, default=True)
    log_to_db = db.Column(db.Boolean, default=False)
    log_level = db.Column(db.String(20), default='DEBUG')

class LogEntry(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    message = db.Column(db.String(255))

    def __init__(self, message):
        self.message = message
