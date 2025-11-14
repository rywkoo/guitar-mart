# routes/products.py
from flask import Blueprint, jsonify, request, current_app
from models import Product, Category, db
from werkzeug.utils import secure_filename
import os

# ----------------------------------------------------------------------
# Blueprint – Public API (no auth, no /admin)
# ----------------------------------------------------------------------
products_bp = Blueprint("products", __name__, url_prefix="/api")

# ----------------------------------------------------------------------
# Helper: Save uploaded image
# ----------------------------------------------------------------------
def save_image(image_file):
    if not image_file or not image_file.filename:
        return None
    filename = secure_filename(image_file.filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    image_file.save(filepath)
    return filename

# ----------------------------------------------------------------------
# 1. GET /api/products – All products (public)
# ----------------------------------------------------------------------
@products_bp.route("/products", methods=["GET"])
def get_all_products():
    products = (
        Product.query
        .order_by(Product.id.desc())
        .options(db.joinedload(Product.category))
        .all()
    )

    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "stock": p.stock,
            "category_id": p.category_id,
            "category_name": p.category.name if p.category else None,
            "image": p.image
        }
        for p in products
    ]), 200


# ----------------------------------------------------------------------
# 2. GET /api/products/<id> – Single product (public)
# ----------------------------------------------------------------------
@products_bp.route("/products/<int:product_id>", methods=["GET"])
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


# ----------------------------------------------------------------------
# 3. (Optional) POST /api/products – Allow public creation?
#    → Usually **not** for public. Keep in admin only.
#    → But if you *do* want it, just copy from admin (no auth)
# ----------------------------------------------------------------------
# @products_bp.route("/products", methods=["POST"])
# def add_product():
#     # ... same code as admin, but NO @jwt_required or @admin_required
#     # Warning: Anyone can add products! Only enable if intentional.
#     pass