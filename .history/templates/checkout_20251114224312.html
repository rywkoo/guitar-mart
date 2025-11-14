{% extends "base.html" %}
{% block title %}Checkout - Mini Mart{% endblock %}

{% block content %}
<style>
.checkout-container {
  max-width: 900px;
  margin: 2rem auto;
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}

.checkout-title {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
}

.cart-item {
  display: flex;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid #eee;
  gap: 1rem;
}

.cart-item:last-child {
  border-bottom: none;
}

.cart-item img {
  width: 90px;
  height: 90px;
  object-fit: cover;
  border-radius: 10px;
  background: #f3f3f3;
}

.cart-item-info {
  flex: 1;
}

.cart-item-name {
  font-size: 1.1rem;
  font-weight: 600;
}

.cart-price {
  margin-top: 4px;
  color: var(--color-text-muted);
  font-size: 0.95rem;
}

.cart-summary {
  margin-top: 2rem;
  text-align: right;
}

.cart-summary h3 {
  font-size: 1.4rem;
}

.checkout-btn {
  margin-top: 1rem;
  background: var(--color-primary);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 700;
}

.checkout-btn:hover {
  background: var(--color-primary-light);
  box-shadow: 0 4px 12px var(--color-primary-shadow);
}

/* Empty cart message */
.cart-empty {
  text-align: center;
  padding: 3rem 1rem;
  font-size: 1.1rem;
  color: var(--color-text-muted);
}
</style>

<div class="checkout-container">
  <h2 class="checkout-title">Checkout</h2>
  <div id="checkoutItems"></div>

  <div class="cart-summary">
    <h3>Total: $<span id="checkoutTotal">0.00</span></h3>
    <button class="checkout-btn" id="checkoutBtn">Confirm & Pay</button>
  </div>
</div>

<script>
document.addEventListener("DOMContentLoaded", () => {
  const checkoutItemsDiv = document.getElementById("checkoutItems");
  const checkoutTotalSpan = document.getElementById("checkoutTotal");
  const checkoutBtn = document.getElementById("checkoutBtn");

  const cart = JSON.parse(localStorage.getItem("cart") || "[]");

  if (cart.length === 0) {
    checkoutItemsDiv.innerHTML = `<div class="cart-empty">Your cart is empty.</div>`;
    checkoutBtn.disabled = true;
    return;
  }

  let total = 0;
  let html = "";
  cart.forEach(item => {
    const subtotal = item.price * item.quantity;
    total += subtotal;

    html += `
      <div class="cart-item">
        <img src="/static/images/${item.image}" alt="${item.name}">
        <div class="cart-item-info">
          <div class="cart-item-name">${item.name}</div>
          <div class="cart-price">$${item.price.toFixed(2)} x ${item.quantity} = $${subtotal.toFixed(2)}</div>
        </div>
      </div>
    `;
  });

  checkoutItemsDiv.innerHTML = html;
  checkoutTotalSpan.textContent = total.toFixed(2);

  checkoutBtn.addEventListener("click", async () => {
    const token = localStorage.getItem("jwtToken") || localStorage.getItem("token");
    if (!token) {
      alert("You must be logged in to checkout.");
      return;
    }

    try {
      const res = await fetch("/checkout/create_invoice", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ cart })
      });

      if (!res.ok) {
        const text = await res.text();
        console.error("Server error:", text);
        alert("Checkout failed. Please try again.");
        return;
      }

      const data = await res.json();

      if (data.success) {
        alert(`Invoice created! Invoice number: ${data.invoice_number}`);
        localStorage.removeItem("cart");
        window.location.href = "/";
      } else {
        alert("Checkout failed: " + (data.message || "Unknown error"));
      }
    } catch (err) {
      console.error(err);
      alert("An error occurred. Check console for details.");
    }
  });
});
</script>
{% endblock %}
