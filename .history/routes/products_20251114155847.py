# routes/products.py
from flask import Blueprint, jsonify
from models import Product, db

products_bp = Blueprint("products", __name__, url_prefix="/admin")

@products_bp.route("/api/products", methods=["GET"])
def public_products():
    """
    Public endpoint – returns the latest products (used on the home page)
    """
    products = (
        Product.query
        .order_by(Product.id.desc())
        .options(db.joinedload(Product.category))   # <-- eager load category
        .all()
    )

    product_list = []
    for p in products:
        # ---- Safe category name ------------------------------------------------
        category_name = p.category.name if p.category else "Uncategorized"

        product_list.append({
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "category_name": category_name,
            "image": p.image,                     # filename only, e.g. "apple.jpg"
        })

    return jsonify(product_list), 200