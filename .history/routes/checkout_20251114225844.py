# checkout.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_mail import Message
from extensions import db, mail
from models import User, Invoice, InvoiceItem, Product
from datetime import datetime

checkout_bp = Blueprint("checkout", __name__, url_prefix="/checkout")

@checkout_bp.route("/create_invoice", methods=["POST"])
@jwt_required()
def create_invoice():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    data = request.get_json()
    cart = data.get("cart", [])

    if not cart:
        return jsonify({"success": False, "message": "Cart is empty"}), 400

    try:
        # Create Invoice
        invoice_number = Invoice.generate_invoice_number()
        invoice = Invoice(username=user.username, invoice_number=invoice_number, created_at=datetime.utcnow())
        db.session.add(invoice)
        db.session.commit()  # Commit to generate invoice.id

        total_amount = 0
        for item in cart:
            product = Product.query.get(item["id"])
            if not product:
                continue
            quantity = item.get("quantity", 1)
            price = product.price
            total_amount += price * quantity
            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=product.id,
                quantity=quantity,
                price=price
            )
            db.session.add(invoice_item)

        invoice.total_amount = total_amount
        db.session.commit()

        # Send Email
        msg = Message(
            subject=f"Your Mini Mart Invoice #{invoice.invoice_number}",
            recipients=[user.email],
            html=f"""
            <h3>Hi {user.username},</h3>
            <p>Thank you for your purchase! Your invoice number is <b>{invoice.invoice_number}</b>.</p>
            <p>Total Amount: ${total_amount:.2f}</p>
            <h4>Items:</h4>
            <ul>
            {''.join([f"<li>{item['name']} x {item['quantity']} = ${item['price']*item['quantity']:.2f}</li>" for item in cart])}
            </ul>
            <p>We appreciate your business!</p>
            """
        )
        mail.send(msg)

        return jsonify({"success": True, "invoice_number": invoice.invoice_number})

    except Exception as e:
        db.session.rollback()
        print("Checkout error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500
