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

    // Update cart count
    if (cartCount) {
      cartCount.textContent = cartItems.length;
    }

    // Calculate totals
    let subtotal = 0;
    cartItems.forEach((item) => {
      const priceText = item.querySelector(".cart-item-price").textContent;
      const price = parseFloat(priceText.replace("£", ""));
      if (!isNaN(price)) {
        subtotal += price;
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
                    <p>Your cart is empty. <a href="/clip-store/">Browse clip store</a> to add items.</p>
                    <a href="/clip-store/">
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

    // Create form data for the request
    const formData = new FormData();
    formData.append("item_id", itemId);
    formData.append("csrfmiddlewaretoken", csrftoken);

    // Send POST request to remove item from cart
    fetch("/cart/remove/", {
      method: "POST",
      body: formData,
      headers: {
        "X-CSRFToken": csrftoken,
      },
      credentials: "same-origin",
    })
      .then((response) => {
        if (response.ok) {
          return response.json();
        }
        throw new Error("Network response was not ok");
      })
      .then((data) => {
        if (data.success) {
          // Find the cart item element and remove it
          const cartItem = buttonElement.closest(".cart-item");
          if (cartItem) {
            cartItem.style.opacity = "0";
            setTimeout(() => {
              cartItem.remove();
              updateCartSummary();

              // Show success message
              showNotification("Item removed from cart");
            }, 300);
          }
        } else {
          // Show error message
          showNotification(
            "Error: " + (data.error || "Failed to remove item"),
            "error"
          );
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        showNotification("Failed to remove item from cart", "error");
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
          window.location.href = "/checkout/";
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

const centerButton = document.getElementById("centerButton");
const popupMenu = document.getElementById("popupMenu");

centerButton.addEventListener("click", (event) => {
  event.stopPropagation();
  popupMenu.style.display =
    popupMenu.style.display === "block" ? "none" : "block";
});

document.addEventListener("click", () => {
  popupMenu.style.display = "none";
});

popupMenu.addEventListener("click", (event) => {
  event.stopPropagation();
});
