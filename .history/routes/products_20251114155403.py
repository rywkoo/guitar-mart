# routes/products.py
from flask import Blueprint, jsonify
from models import Product

products_bp = Blueprint("products", __name__)

@products_bp.route("/api/products", methods=["GET"])
def public_products():
    products = Product.query.order_by(Product.id.desc()).all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "price": float(p.price),
        "category_name": p.category.name if p.category else None,
        "image": p.image  # just the filename
    } for p in products]), 200
