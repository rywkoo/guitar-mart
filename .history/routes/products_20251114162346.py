# routes/products.py
from flask import Blueprint, jsonify, current_app
from models import Product, db
from werkzeug.utils import secure_filename
import os

products_bp = Blueprint("products", __name__, url_prefix="/api")

# Helper to save uploaded image
def save_image(image_file):
    if not image_file or not image_file.filename:
        return None
    filename = secure_filename(image_file.filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    image_file.save(filepath)
    return filename

# 1️⃣ GET all products (public)
@products_bp.route("/products", methods=["GET"])
def get_all_products():
    products = Product.query.order_by(Product.id.desc()).all()
    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "stock": p.stock,
            "category_id": p.category_id,
            "category_name": p.category.name if p.category else None,
            "image": p.image
        } for p in products
    ]), 200

# 2️⃣ GET single product (public)
@products_bp.route("/products/<int:product_id>", methods=["GET"], strict_slashes=False)
def get_product(product_id):
    p = Product.query.get_or_404(product_id)
    return jsonify({
        "id": p.id,
        "name": p.name,
        "price": float(p.price),
        "stock": p.stock,
        "category_id": p.category_id,
        "category_name": p.category.name if p.category else None,
        "image": p.image
    }), 200
