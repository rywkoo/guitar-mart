# models.py
from datetime import datetime, timedelta
import hashlib
import random
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
import secrets


# -------------------
# USER
# -------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default="user")  # 'user' or 'admin'
    is_active = db.Column(db.Boolean, default=True)

    reset_tokens = db.relationship("ResetToken", backref="user", lazy=True)
    orders = db.relationship("Order", backref="user", lazy=True)
    login_tokens = db.relationship("LoginToken", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# -------------------
# CATEGORY & PRODUCT
# -------------------
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    products = db.relationship("Product", backref="category", lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(100), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)


# -------------------
# ORDER
# -------------------
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    total_price = db.Column(db.Float, default=0.0)
    items = db.relationship("OrderItem", backref="order", lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)


# -------------------
# TOKEN HELPERS
# -------------------
def generate_6digit_token():
    """Generate a secure 6-digit numeric token"""
    return f"{random.SystemRandom().randint(100000, 999999)}"


# -------------------
# RESET TOKEN (6 digits)
# -------------------
class ResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    token_hash = db.Column(db.String(64), nullable=False)  # SHA-256 hash
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used = db.Column(db.Boolean, default=False)

    def is_expired(self):
        return datetime.utcnow() > self.created_at + timedelta(minutes=15)

    @staticmethod
    def generate_token():
        return generate_6digit_token()

    @staticmethod
    def hash_token(token: str):
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def create_for_user(user):
        token = ResetToken.generate_token()
        hashed = ResetToken.hash_token(token)
        reset_token = ResetToken(user_id=user.id, token_hash=hashed)
        db.session.add(reset_token)
        db.session.commit()
        return token  # Return plain token to send via email


# -------------------
# LOGIN TOKEN (6 digits)
# -------------------
class LoginToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    token = db.Column(db.String(6), nullable=False, unique=True)  # 6 digits
    expires_at = db.Column(db.DateTime, nullable=False)

    @staticmethod
    def generate(user, expires_minutes=10):
        token = generate_6digit_token()
        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
        login_token = LoginToken(user_id=user.id, token=token, expires_at=expires_at)
        db.session.add(login_token)
        db.session.commit()
        return login_token  # Return object with .token


# -------------------
# REGISTER TOKEN (6 digits)
# -------------------
class RegisterToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(6), nullable=False, unique=True)  # 6 digits
    expires_at = db.Column(db.DateTime, nullable=False)

    @staticmethod
    def generate(email, expires_minutes=10):
        token = generate_6digit_token()
        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
        reg_token = RegisterToken(email=email, token=token, expires_at=expires_at)
        db.session.add(reg_token)
        db.session.commit()
        return token  # Return plain 6-digit string

    @staticmethod
    def verify(email, token):
        reg_token = RegisterToken.query.filter_by(email=email, token=token).first()
        if reg_token and reg_token.expires_at > datetime.utcnow():
            db.session.delete(reg_token)
            db.session.commit()
            return True
        return False


# -------------------
# INVOICE
# -------------------
class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    invoice_number = db.Column(db.String(20), unique=True, nullable=False)
    total_amount = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship("InvoiceItem", backref="invoice", lazy=True)

    @staticmethod
    def generate_invoice_number():
        last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        next_id = 1 if not last_invoice else last_invoice.id + 1
        return f"INV{next_id:06d}"


class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)