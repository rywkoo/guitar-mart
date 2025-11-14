# routes/checkout.py
from flask import Blueprint, render_template, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User, Invoice, InvoiceItem
from datetime import datetime

checkout_bp = Blueprint("checkout", __name__, url_prefix="/checkout")

@checkout_bp.route("/", methods=["GET"])
@jwt_required()
def checkout_page():
    """
    Render the checkout page.
    The page will fetch user info from JWT token.
    """
    identity = get_jwt_identity()
    user = User.query.filter_by(username=identity).first()
    if not user:
        return "User not found", 404

    return render_template("checkout.html", user=user)


@checkout_bp.route("/create_invoice", methods=["POST"])
@jwt_required()
def create_invoice():
    """
    Create an invoice from the current cart.
    Expects cart data from frontend (localStorage sent via fetch)
    """
    from flask import request
    import json, smtplib
    from email.message import EmailMessage

    identity = get_jwt_identity()
    user = User.query.filter_by(username=identity).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    cart_data = request.get_json()
    if not cart_data or "cart" not in cart_data:
        return jsonify({"error": "Cart data missing"}), 400

    cart = cart_data["cart"]
    total_amount = sum(item["price"] * item["quantity"] for item in cart)

    # Create invoice
    invoice_number = Invoice.generate_invoice_number()
    invoice = Invoice(
        username=user.username,
        invoice_number=invoice_number,
        total_amount=total_amount,
        created_at=datetime.utcnow()
    )
    db.session.add(invoice)
    db.session.commit()

    # Create invoice items
    for item in cart:
        invoice_item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=item["id"],
            quantity=item["quantity"],
            price=item["price"]
        )
        db.session.add(invoice_item)
    db.session.commit()

    # Send email (simple example)
    try:
        msg = EmailMessage()
        msg["Subject"] = f"Your Invoice {invoice_number}"
        msg["From"] = "no-reply@minimart.com"
        msg["To"] = user.email
        body = f"Hello {user.username},\n\nThank you for your order.\nInvoice Number: {invoice_number}\nTotal Amount: ${total_amount:.2f}\n\n- Mini Mart"
        msg.set_content(body)

        # Replace this with your SMTP server settings
        with smtplib.SMTP("localhost") as server:
            server.send_message(msg)
    except Exception as e:
        print("Email send failed:", e)

    return jsonify({"success": True, "invoice_number": invoice_number})
