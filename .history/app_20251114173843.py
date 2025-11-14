# app.py
from flask import Flask, render_template
from extensions import db, migrate, jwt, mail
from config import Config
import os
from flask_cors import CORS

# Import blueprints
from routes.auth import auth_bp
from routes.products import products_bp
from routes.categories import categories_bp
from routes.cart import cart_bp
from routes.invoices import invoices_bp
from routes.admin import admin_bp
from routes.reset import reset_bp

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
# Ensure UPLOAD_FOLDER exists
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'images')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)
jwt.init_app(app)
mail.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")          # /api/auth/login
app.register_blueprint(categories_bp, url_prefix="/api/categories")
app.register_blueprint(cart_bp, url_prefix="/api/cart")
app.register_blueprint(invoices_bp, url_prefix="/api/invoices")
app.register_blueprint(admin_bp)                                 # /admin/dashboard
app.register_blueprint(reset_bp, url_prefix="/api/reset")
app.register_blueprint(products_bp)                              # <-- Public API /api/products

# Pages
@app.route("/")
def home_page():
    return render_template("home.html")

@app.route("/test-product")
def test_product():
    return render_template("test_product.html")

@app.route("/register-page")
def register_page():
    return render_template("register.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/shop")
def shop():
    return render_template("shop.html")

@app.route("/about")
def about():
    return render_template("shop.html")

@app.route("/admin/dashboard")
def dashboard_page():
    return render_template("admin/dashboard.html")  # JS will protect

@app.route("/reset-password")
def reset_password_page():
    return render_template("reset_password.html")

if __name__ == "__main__":
    app.run(debug=True)
