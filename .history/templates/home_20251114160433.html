# products.py
from flask import Blueprint, jsonify, current_app
from models import Product, Category, db

# ----------------------------------------------------------------------
# 1. Reusable function – get all products
# ----------------------------------------------------------------------
def get_all_products():
    """
    Returns a list of dicts with id, name, price, category_name and image.
    Safe for JSON serialization.
    """
    products = (
        Product.query
        .order_by(Product.id.desc())
        .options(db.joinedload(Product.category))
        .all()
    )

    return [
        {
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "category_name": p.category.name if p.category else "Uncategorized",
            "image": p.image,
        }
        for p in products
    ]


# ----------------------------------------------------------------------
# 2. Blueprint + public endpoint
# ----------------------------------------------------------------------
products_bp = Blueprint("products", __name__, url_prefix="/api")


@products_bp.route("/products", methods=["GET"])
def api_get_products():
    """Public endpoint – returns all products (used on the home page)."""
    return jsonify(get_all_products()), 200


# ----------------------------------------------------------------------
# 3. (Optional) Seed a few test products – run once
# ----------------------------------------------------------------------
def seed_test_data():
    """
    Creates a category + 4 products if the DB is empty.
    Call this from the Flask shell or a one-off script.
    """
    if Product.query.first():
        return  # already seeded

    with current_app.app_context():
        # create category
        cat = Category(name="Fruits", description="Fresh fruits")
        db.session.add(cat)
        db.session.flush()  # gives us cat.id

        # create products
        db.session.add_all([
            Product(name="Apple",      price=1.99, stock=50, image="apple.jpg",      category_id=cat.id),
            Product(name="Banana",     price=0.79, stock=80, image="banana.jpg",     category_id=cat.id),
            Product(name="Orange",     price=2.49, stock=30, image="orange.jpg",     category_id=cat.id),
            Product(name="Mango",      price=3.99, stock=20, image="mango.jpg",      category_id=cat.id),
        ])
        db.session.commit()
        print("Seeded 4 test products.")