# app.py
from flask import Flask, render_template, redirect, url_for
from extensions import db, migrate, jwt, mail
from config import Config

# Import blueprints
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.products import products_bp
from routes.categories import categories_bp
from routes.cart import cart_bp
from routes.invoices import invoices_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.jinja_env.filters['tojson'] = lambda v: __import__('json').dumps(v)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp)  # /admin/dashboard
    app.register_blueprint(products_bp, url_prefix="/api/products")
    app.register_blueprint(categories_bp, url_prefix="/api/categories")
    app.register_blueprint(cart_bp, url_prefix="/api/cart")
    app.register_blueprint(invoices_bp, url_prefix="/api/invoices")

    # Static pages
    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/register-page")
    def register_page():
        return render_template("register.html")

    @app.route("/reset-password")
    def reset_page():
        return render_template("reset_password.html")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)