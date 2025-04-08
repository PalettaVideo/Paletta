document.addEventListener("DOMContentLoaded", function () {
  const addToCartButton = document.getElementById("addToCartButton");
  const popupOverlay = document.getElementById("popupOverlay");
  const confirmAddToCart = document.getElementById("confirmAddToCart");
  const addToCollectionButton = document.getElementById(
    "addToCollectionButton"
  );

  // Local storage keys for client-side caching
  const COLLECTION_STORAGE_KEY = "userCollection";
  const CART_STORAGE_KEY = "userCart";

  // Function to initialize local storage if not present
  function initializeLocalStorage() {
    if (!localStorage.getItem(COLLECTION_STORAGE_KEY)) {
      localStorage.setItem(COLLECTION_STORAGE_KEY, JSON.stringify([]));
    }
    if (!localStorage.getItem(CART_STORAGE_KEY)) {
      localStorage.setItem(CART_STORAGE_KEY, JSON.stringify([]));
    }
  }

  // Initialize local storage
  initializeLocalStorage();

  // Add to cart functionality
  if (addToCartButton && popupOverlay && confirmAddToCart) {
    addToCartButton.addEventListener("click", () => {
      popupOverlay.style.display = "flex";
    });

    confirmAddToCart.addEventListener("click", () => {
      const selectedResolution = document.querySelector(
        'input[name="resolution"]:checked'
      );
      if (selectedResolution) {
        const resolution = selectedResolution.value;
        const price = selectedResolution.dataset.price;
        // Get clip ID from meta tag in the document
        const clipId =
          document.querySelector('meta[name="clip-id"]')?.content || "0";

        // Get CSRF token for Django
        const csrftoken = document.querySelector(
          "[name=csrfmiddlewaretoken]"
        ).value;

        // Send AJAX request to add to cart
        fetch("/cart/add/", {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrftoken,
          },
          body: `video_id=${clipId}&resolution=${resolution}&price=${price}`,
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              // Update client-side cart cache
              updateCartCache(clipId, resolution, price);

              // Display success message
              const successMessage = `"${
                document.querySelector("h1").textContent
              }" added to cart (${resolution})`;
              showNotification(successMessage);

              popupOverlay.style.display = "none";

              // Update cart count in header if exists
              const cartCountElement = document.querySelector(".cart-count");
              if (cartCountElement) {
                cartCountElement.textContent = data.cart_count;
              }
            } else {
              showNotification(
                "Error: " + (data.message || data.error),
                "error"
              );
            }
          })
          .catch((error) => {
            console.error("Error:", error);
            showNotification(
              "An error occurred while adding the item to cart.",
              "error"
            );
          });
      } else {
        showNotification("Please select a resolution", "warning");
      }
    });

    popupOverlay.addEventListener("click", (event) => {
      if (event.target === popupOverlay) {
        popupOverlay.style.display = "none";
      }
    });
  }

  // Add to collection functionality
  if (addToCollectionButton) {
    addToCollectionButton.addEventListener("click", () => {
      const clipId = document.querySelector('meta[name="clip-id"]').content;
      const csrftoken = document.querySelector(
        "[name=csrfmiddlewaretoken]"
      ).value;

      // Use URL-encoded form data instead of FormData
      const formData = new URLSearchParams();
      formData.append("clip_id", clipId);

      // Send POST request to add item to collection
      fetch("/collection/add/", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": csrftoken,
        },
        body: formData,
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
            // Update client-side collection cache
            updateCollectionCache(clipId);

            // Show success notification
            const clipTitle = document.querySelector("h1").textContent;
            showNotification(`"${clipTitle}" added to your collection!`);
          } else {
            showNotification("Error: " + data.error, "error");
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          showNotification(
            "Failed to add item to collection. Please try again.",
            "error"
          );
        });
    });
  }

  // Function to update the client-side cart cache
  function updateCartCache(clipId, resolution, price) {
    try {
      // Get current cart from localStorage
      const cart = JSON.parse(localStorage.getItem(CART_STORAGE_KEY)) || [];

      // Get clip title for better display later
      const clipTitle = document.querySelector("h1").textContent;

      // Add the item to cart (with deduplication)
      const existingItemIndex = cart.findIndex(
        (item) => item.id === clipId && item.resolution === resolution
      );

      if (existingItemIndex >= 0) {
        // Update existing item
        cart[existingItemIndex] = {
          id: clipId,
          title: clipTitle,
          resolution: resolution,
          price: price,
          added: new Date().toISOString(),
        };
      } else {
        // Add new item
        cart.push({
          id: clipId,
          title: clipTitle,
          resolution: resolution,
          price: price,
          added: new Date().toISOString(),
        });
      }

      // Save back to localStorage
      localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));

      console.log("Cart updated in localStorage:", cart);
    } catch (error) {
      console.error("Error updating cart in localStorage:", error);
    }
  }

  // Function to update the client-side collection cache
  function updateCollectionCache(clipId) {
    try {
      // Get current collection from localStorage
      const collection =
        JSON.parse(localStorage.getItem(COLLECTION_STORAGE_KEY)) || [];

      // Get clip title and other details for better display later
      const clipTitle = document.querySelector("h1").textContent;
      const clipDescription =
        document.querySelector(".video-info p").textContent;

      // Check if the clip is already in collection
      if (!collection.some((item) => item.id === clipId)) {
        // Add new item
        collection.push({
          id: clipId,
          title: clipTitle,
          description: clipDescription,
          added: new Date().toISOString(),
        });

        // Save back to localStorage
        localStorage.setItem(
          COLLECTION_STORAGE_KEY,
          JSON.stringify(collection)
        );

        console.log("Collection updated in localStorage:", collection);
      }
    } catch (error) {
      console.error("Error updating collection in localStorage:", error);
    }
  }

  // Function to show toast notifications
  function showNotification(message, type = "success") {
    // Create notification element
    const notification = document.createElement("div");
    notification.className = `notification ${type}`;
    notification.textContent = message;

    // Add to document
    document.body.appendChild(notification);

    // Show with animation
    setTimeout(() => {
      notification.classList.add("show");
    }, 10);

    // Auto-hide after 3 seconds
    setTimeout(() => {
      notification.classList.remove("show");
      // Remove from DOM after animation
      setTimeout(() => {
        notification.remove();
      }, 300);
    }, 3000);
  }

  // Add notification styles if not already present
  if (!document.getElementById("notification-styles")) {
    const style = document.createElement("style");
    style.id = "notification-styles";
    style.textContent = `
      .notification {
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 10px 20px;
        background-color: #4CAF50;
        color: white;
        border-radius: 4px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        transform: translateY(100px);
        opacity: 0;
        transition: all 0.3s ease;
        z-index: 1000;
        max-width: 80%;
      }
      .notification.show {
        transform: translateY(0);
        opacity: 1;
      }
      .notification.error {
        background-color: #f44336;
      }
      .notification.warning {
        background-color: #ff9800;
      }
    `;
    document.head.appendChild(style);
  }
});
