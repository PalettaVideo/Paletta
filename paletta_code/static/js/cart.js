document.addEventListener("DOMContentLoaded", function () {
  // Initialize cart functionality
  updateCartSummary();
  setupRemoveButtons();
  setupCheckoutButton();

  /**
   * Updates the cart summary with correct count and prices
   */
  function updateCartSummary() {
    const cartItems = document.querySelectorAll(".cart-item");
    const cartCount = document.getElementById("cart-count");
    const subtotalElement = document.getElementById("subtotal");
    const vatElement = document.getElementById("vat");
    const totalElement = document.getElementById("cart-total");
    const checkoutButton = document.getElementById("checkout-button");

    // Get the clip store URL from a data attribute in the document
    const clipStoreUrl =
      document.querySelector('meta[name="clip-store-url"]')?.content || "/";

    // Update cart count
    if (cartCount) {
      cartCount.textContent = cartItems.length;
    }

    // Calculate totals
    let subtotal = 0;
    cartItems.forEach((item) => {
      const priceElement = item.querySelector(".cart-item-price");
      if (priceElement) {
        const priceText = priceElement.textContent;
        const price = parseFloat(priceText.replace("£", ""));
        if (!isNaN(price)) {
          subtotal += price;
        }
      }
    });

    const vat = subtotal * 0.2;
    const total = subtotal + vat;

    // Update price displays
    if (subtotalElement)
      subtotalElement.textContent = `£${subtotal.toFixed(2)}`;
    if (vatElement) vatElement.textContent = `£${vat.toFixed(2)}`;
    if (totalElement) totalElement.textContent = `£${total.toFixed(2)}`;

    // Enable/disable checkout button
    if (checkoutButton) {
      checkoutButton.disabled = cartItems.length === 0;
    }

    // Show empty cart message if needed
    const cartItemsContainer = document.getElementById("cart-items");
    if (cartItemsContainer && cartItems.length === 0) {
      cartItemsContainer.innerHTML = `
                <div class="empty-cart">
                    <p>Your cart is empty. <a href="${clipStoreUrl}">Browse clip store</a> to add items.</p>
                    <a href="${clipStoreUrl}">
                        <button>Browse Clip Store</button>
                    </a>
          </div>
        `;
    }
  }

  /**
   * Sets up event listeners for remove buttons
   */
  function setupRemoveButtons() {
    const removeButtons = document.querySelectorAll(
      ".cart-item-actions .remove"
    );

    removeButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const itemId = this.getAttribute("data-id");
        if (itemId) {
          removeFromCart(itemId, this);
        }
      });
    });
  }

  /**
   * Removes an item from the cart
   */
  function removeFromCart(itemId, buttonElement) {
    // Get the CSRF token
    const csrftoken = document.querySelector(
      "[name=csrfmiddlewaretoken]"
    ).value;

    // Get the clip store URL from a data attribute in the document
    const clipStoreUrl =
      document.querySelector('meta[name="clip-store-url"]')?.content || "/";

    // Send AJAX request to remove item
    fetch("/api/orders/remove-from-cart/", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": csrftoken,
      },
      body: "order_detail_id=" + itemId,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          // Remove the item from the UI
          const item = document.querySelector(
            `.cart-item[data-id="${itemId}"]`
          );
          if (item) {
            item.remove();
          }

          // Update cart count
          document.getElementById("cart-count").textContent = data.cart_count;

          // If cart is empty, show empty cart message
          if (data.cart_count === 0) {
            const cartItems = document.getElementById("cart-items");
            cartItems.innerHTML = `
            <div class="empty-cart">
              <p>Your cart is empty. <a href="${clipStoreUrl}">Browse clip store</a> to add items.</p>
              <a href="${clipStoreUrl}">
                <button>Browse Clip Store</button>
              </a>
            </div>
          `;

            // Disable checkout button
            document.getElementById("checkout-button").disabled = true;
          }

          // Reload the page to update the totals
          window.location.reload();
        } else {
          alert("Error removing item: " + data.message);
        }
      })
      .catch(() => {
        alert("An error occurred while removing the item from cart.");
      });
  }

  /**
   * Sets up the checkout button
   */
  function setupCheckoutButton() {
    const checkoutButton = document.getElementById("checkout-button");

    if (checkoutButton) {
      checkoutButton.addEventListener("click", function () {
        if (!this.disabled) {
          // Use the checkout URL from the existing href if available
          const checkoutLink = document.querySelector('a[href*="checkout"]');
          if (checkoutLink) {
            window.location.href = checkoutLink.href;
          } else {
            window.location.href = "/checkout/";
          }
        }
      });
    }
  }

  /**
   * Shows a notification message
   */
  function showNotification(message, type = "success") {
    // Create notification element
    const notification = document.createElement("div");
    notification.className = `notification ${type}`;
    notification.textContent = message;

    // Add to body
    document.body.appendChild(notification);

    // Animate in
    setTimeout(() => {
      notification.classList.add("show");
    }, 10);

    // Remove after 3 seconds
    setTimeout(() => {
      notification.classList.remove("show");
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 3000);
  }
});
