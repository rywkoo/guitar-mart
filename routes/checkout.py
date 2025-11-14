# routes/checkout.py
from flask import Blueprint, render_template, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db, mail  # <-- mail is now used
from models import User, Invoice, InvoiceItem
from datetime import datetime
from flask_mail import Message

checkout_bp = Blueprint("checkout", __name__, url_prefix="/checkout")


@checkout_bp.route("/", methods=["GET"])
@jwt_required()
def checkout_page():
    """
    Render the checkout page.
    User info is fetched from JWT token.
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
    Expects cart data from frontend (localStorage sent via fetch).
    Sends confirmation email using Flask-Mail.
    """
    identity = get_jwt_identity()
    user = User.query.filter_by(username=identity).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    cart_data = request.get_json()
    if not cart_data or "cart" not in cart_data:
        return jsonify({"error": "Cart data missing"}), 400

    cart = cart_data["cart"]
    if not cart:
        return jsonify({"error": "Cart is empty"}), 400

    # Calculate total
    total_amount = sum(item["price"] * item["quantity"] for item in cart)

    # Generate invoice number
    invoice_number = Invoice.generate_invoice_number()

    # Create invoice
    invoice = Invoice(
        username=user.username,
        invoice_number=invoice_number,
        total_amount=total_amount,
        created_at=datetime.utcnow()
    )
    db.session.add(invoice)
    db.session.flush()  # Get invoice.id without committing yet

    # Create invoice items
    for item in cart:
        invoice_item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=item["id"],
            quantity=item["quantity"],
            price=item["price"]
        )
        db.session.add(invoice_item)

    # Commit all changes
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("DB Error:", str(e))
        return jsonify({"error": "Failed to save invoice"}), 500

    # Send confirmation email
    try:
        msg = Message(
            subject=f"Your Invoice {invoice_number} - Mini Mart",
            sender=("Mini Mart", current_app.config["MAIL_DEFAULT_SENDER"]),
            recipients=[user.email],
            reply_to="no-reply@minimart.com"
        )

        # Email body
        items_html = ""
        for item in cart:
            subtotal = item["price"] * item["quantity"]
            items_html += f"""
            <tr>
                <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{item["name"]}</td>
                <td style="text-align: center;">{item["quantity"]}</td>
                <td style="text-align: right;">${item["price"]:.2f}</td>
                <td style="text-align: right;">${subtotal:.2f}</td>
            </tr>
            """

        msg.html = f"""
        <h2>Thank You for Your Order, {user.username}!</h2>
        <p>Your order has been confirmed. Here are the details:</p>

        <p><strong>Invoice Number:</strong> {invoice_number}</p>
        <p><strong>Order Date:</strong> {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}</p>

        <table style="width: 100%; margin: 20px 0; border-collapse: collapse;">
            <thead>
                <tr style="background: #f8f8f8;">
                    <th style="text-align: left; padding: 10px;">Item</th>
                    <th style="text-align: center;">Qty</th>
                    <th style="text-align: right;">Price</th>
                    <th style="text-align: right;">Total</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
            <tfoot>
                <tr>
                    <td colspan="3" style="text-align: right; padding-top: 15px; font-weight: bold;">Total Amount:</td>
                    <td style="text-align: right; font-weight: bold; color: #2c3e50;">${total_amount:.2f}</td>
                </tr>
            </tfoot>
        </table>

        <p><a href="{request.url_root}" style="color: #3498db; text-decoration: none;">Visit Mini Mart</a> to shop again!</p>

        <hr>
        <small style="color: #777;">This is an automated email. Please do not reply.</small>
        """

        mail.send(msg)
        print(f"Invoice email sent to {user.email}")

    except Exception as e:
        # Log error but don't fail checkout
        print(f"Failed to send email to {user.email}: {str(e)}")
        # Optional: save email failure in logs table later

    return jsonify({
        "success": True,
        "invoice_number": invoice_number,
        "total_amount": total_amount
    })


