# routes/products.py
from flask import Blueprint, jsonify
from models import Product, db

# Blueprint name = "products", URL prefix = "/api"
products_bp = Blueprint("products", __name__, url_prefix="/api")

@products_bp.route("/products", methods=["GET"])
def get_products():
    """
    Public endpoint – returns all products for the home page.
    """
    products = (
        Product.query
        .order_by(Product.id.desc())
        .options(db.joinedload(Product.category))
        .all()
    )

    result = []
    for p in products:
        result.append({
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "category_name": p.category.name if p.category else "Uncategorized",
            "image": p.image,
        })

    return jsonify(result), 200