# routes/public_products.py
from flask import Blueprint, jsonify
from models import Product, db

# Public blueprint – no /admin prefix
public_products_bp = Blueprint(
    "public_products",               # name
    __name__,                        # module
    url_prefix="/api"                # → /api/products
)

@public_products_bp.route("/products", methods=["GET"])
def get_products():
    """
    Public endpoint – returns all products (used on the home page).
    You can later add pagination, limit, etc.
    """
    products = (
        Product.query
        .order_by(Product.id.desc())
        .options(db.joinedload(Product.category))   # Eager-load category → no N+1
        .all()
    )

    result = []
    for p in products:
        result.append({
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "category_name": p.category.name if p.category else "Uncategorized",
            "image": p.image,                # filename only (e.g. "apple.jpg")
        })

    return jsonify(result), 200