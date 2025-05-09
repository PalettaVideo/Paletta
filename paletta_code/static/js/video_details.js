document.addEventListener("DOMContentLoaded", function () {
  const addToCartButton = document.getElementById("addToCartButton");
  const popupOverlay = document.getElementById("popupOverlay");
  const confirmAddToCart = document.getElementById("confirmAddToCart");
  const addToCollectionButton = document.getElementById(
    "addToCollectionButton"
  );

  // Use the same localStorage keys as inside_category.js
  const COLLECTION_STORAGE_KEY = "userCollection";
  const CART_STORAGE_KEY = "userCart";

  // Initialize UI and event listeners
  initializeUI();
  setupEventListeners();

  /**
   * Initialize UI elements and storage
   */
  function initializeUI() {
    // Initialize local storage if not present
    if (!localStorage.getItem(COLLECTION_STORAGE_KEY)) {
      localStorage.setItem(COLLECTION_STORAGE_KEY, JSON.stringify([]));
    }
    if (!localStorage.getItem(CART_STORAGE_KEY)) {
      localStorage.setItem(CART_STORAGE_KEY, JSON.stringify([]));
    }
  }

  /**
   * Set up event listeners
   */
  function setupEventListeners() {
    // Add to cart functionality
    if (addToCartButton && popupOverlay && confirmAddToCart) {
      addToCartButton.addEventListener("click", () => {
        popupOverlay.style.display = "flex";
      });

      confirmAddToCart.addEventListener("click", handleAddToCart);

      popupOverlay.addEventListener("click", (event) => {
        if (event.target === popupOverlay) {
          popupOverlay.style.display = "none";
        }
      });
    }

    // Add to collection functionality
    if (addToCollectionButton) {
      addToCollectionButton.addEventListener("click", handleAddToCollection);
    }
  }

  /**
   * Handle adding to cart
   */
  function handleAddToCart() {
    const selectedResolution = document.querySelector(
      'input[name="resolution"]:checked'
    );
    if (!selectedResolution) {
      showNotification("Please select a resolution", "warning");
      return;
    }

    const resolution = selectedResolution.value;
    const price = selectedResolution.dataset.price;

    // Get video ID using the same approach as inside_category.js
    const videoId = getVideoId();
    if (!videoId) {
      showNotification("Error: Could not determine video ID", "error");
      return;
    }

    // Get CSRF token
    const csrftoken = getCSRFToken();
    if (!csrftoken) {
      showNotification("Error: CSRF token not found", "error");
      return;
    }

    // Create URL-encoded form data
    const formData = new URLSearchParams();
    formData.append("video_id", videoId);
    formData.append("resolution", resolution);
    formData.append("price", price);

    // Send AJAX request to add to cart
    fetch("/cart/add/", {
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
        throw new Error(`Network error: ${response.status}`);
      })
      .then((data) => {
        if (data.success) {
          // Update client-side cart cache
          updateCartCache(videoId, resolution, price);

          // Display success message
          const clipTitle = document.querySelector("h1").textContent;
          showNotification(`"${clipTitle}" added to cart (${resolution})`);

          // Close the popup
          popupOverlay.style.display = "none";

          // Update cart count in header if exists
          const cartCountElement = document.querySelector(".cart-count");
          if (cartCountElement && data.cart_count) {
            cartCountElement.textContent = data.cart_count;
          }
        } else {
          showNotification("Error: " + (data.message || data.error), "error");
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        // Try to update cache anyway for offline functionality
        updateCartCache(videoId, resolution, price);
        showNotification("Added to local cart (offline mode)", "info");
      });
  }

  /**
   * Handle adding to collection
   */
  function handleAddToCollection() {
    // Get video ID using the same approach as inside_category.js
    const videoId = getVideoId();
    if (!videoId) {
      showNotification("Error: Could not determine video ID", "error");
      return;
    }

    // Get CSRF token
    const csrftoken = getCSRFToken();
    if (!csrftoken) {
      showNotification("Error: CSRF token not found", "error");
      return;
    }

    // Log what we're sending (same as inside_category.js)
    console.log(`Adding video ID ${videoId} to collection`);

    // Create URL-encoded form data
    const formData = new URLSearchParams();
    formData.append("clip_id", videoId);

    // Send POST request to add to collection (same endpoint as inside_category.js)
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
        console.log(`Response status: ${response.status}`);
        if (response.ok) {
          return response.json();
        }
        throw new Error(`Network error: ${response.status}`);
      })
      .then((data) => {
        console.log("Response data:", data);
        if (data.success) {
          // Update client-side collection cache
          updateCollectionCache(videoId);

          // Show success notification
          const clipTitle = document.querySelector("h1").textContent;
          showNotification(`"${clipTitle}" added to your collection!`);
        } else {
          showNotification(
            "Error: " + (data.error || "Failed to add to collection"),
            "error"
          );
        }
      })
      .catch((error) => {
        console.error("Error adding to collection:", error);
        // Still try to update cache anyway for offline functionality
        updateCollectionCache(videoId);
        showNotification("Added to local collection (offline mode)", "info");
      });
  }

  /**
   * Get the video ID from the page
   * Using a consistent approach that works with both meta tags and data attributes
   */
  function getVideoId() {
    // First try to get from meta tag (current approach in video_details.js)
    const metaTag = document.querySelector('meta[name="clip-id"]');
    if (metaTag && metaTag.content) {
      return metaTag.content;
    }

    // If not found, log error and return null
    console.error("Could not find video ID in page");
    return null;
  }

  /**
   * Get CSRF token from cookies (same as inside_category.js)
   */
  function getCSRFToken() {
    const name = "csrftoken";
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  /**
   * Update the client-side cart cache
   * Taking the best of both implementations
   */
  function updateCartCache(videoId, resolution, price) {
    try {
      // Get current cart from localStorage
      const cart = JSON.parse(localStorage.getItem(CART_STORAGE_KEY)) || [];

      // Get video details from the page
      const videoDetails = getVideoDetailsFromPage();

      // Add the item to cart (with deduplication)
      const existingItemIndex = cart.findIndex(
        (item) => item.id == videoId && item.resolution === resolution
      );

      if (existingItemIndex >= 0) {
        // Update existing item
        cart[existingItemIndex] = {
          ...cart[existingItemIndex],
          ...videoDetails,
          resolution: resolution,
          price: price,
          updated: new Date().toISOString(),
          quantity: (cart[existingItemIndex].quantity || 1) + 1,
        };
      } else {
        // Add new item with quantity 1
        cart.push({
          id: videoId,
          ...videoDetails,
          resolution: resolution,
          price: price,
          added: new Date().toISOString(),
          quantity: 1,
        });
      }

      // Save back to localStorage
      localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));

      console.log("Cart updated in localStorage:", cart);
    } catch (error) {
      console.error("Error updating cart in localStorage:", error);
    }
  }

  /**
   * Update the client-side collection cache
   * Taking the best of both implementations
   */
  function updateCollectionCache(videoId) {
    try {
      // First check if we have a valid video element in the page
      const videoContainer = document.querySelector(".video-container");
      if (!videoContainer) {
        console.error("Video container not found in the DOM");
        return;
      }

      // Get current collection from localStorage
      const collection =
        JSON.parse(localStorage.getItem(COLLECTION_STORAGE_KEY)) || [];

      // Get video details from the page - only if we have valid elements
      const videoDetails = getVideoDetailsFromPage();

      // Only if we have valid video details
      if (!videoDetails.title) {
        console.error("Could not extract valid video details from the page");
        return;
      }

      // Only add if item doesn't exist already
      if (!collection.some((item) => item.id == videoId)) {
        collection.push({
          id: videoId,
          ...videoDetails,
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

  /**
   * Get video details from the current page
   * Extracts all relevant details for consistent storage
   */
  function getVideoDetailsFromPage() {
    // Get video ID from meta tag
    const videoId = getVideoId();

    // Create video object with basic details
    const videoObj = {
      id: videoId,
      title: document.querySelector("h1")?.textContent || "Untitled",
      description:
        document.querySelector(".video-description")?.textContent || "",
    };

    // Try to get thumbnail from various sources
    // 1. Check if there's a meta tag with the thumbnail URL
    const thumbnailMeta = document.querySelector('meta[name="clip-thumbnail"]');
    if (thumbnailMeta && thumbnailMeta.content) {
      videoObj.thumbnail = thumbnailMeta.content;
    }
    // 2. Try to get the video poster attribute if available
    else {
      const videoElement = document.querySelector(".video-container video");
      if (videoElement && videoElement.poster) {
        videoObj.thumbnail = videoElement.poster;
      }
      // 3. If no thumbnail found, store the current page URL
      // This will allow us to fetch it later if needed
      else {
        // Store video ID and current URL to fetch thumbnail later if needed
        videoObj.thumbnail = window.location.href;
        videoObj.needsThumbnail = true;
      }
    }

    // Get tags if available
    const tags = [];
    document.querySelectorAll(".tag").forEach((tag) => {
      tags.push(tag.textContent);
    });
    videoObj.tags = tags;

    return videoObj;
  }

  /**
   * Show a toast notification
   * Same implementation as inside_category.js
   */
  function showNotification(message, type = "success") {
    // Ensure notification styles exist
    if (!document.getElementById("notification-styles")) {
      const style = document.createElement("style");
      style.id = "notification-styles";
      style.textContent = `
        .notification {
          position: fixed;
          bottom: 20px;
          right: 20px;
          padding: 15px 25px;
          border-radius: 5px;
          color: white;
          font-weight: bold;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
          transform: translateY(20px);
          opacity: 0;
          transition: transform 0.3s, opacity 0.3s;
          z-index: 1000;
          max-width: 80%;
        }
        .notification.show {
          transform: translateY(0);
          opacity: 1;
        }
        .notification.success {
          background-color: #80B824;
        }
        .notification.error {
          background-color: #e74c3c;
        }
        .notification.info {
          background-color: #3498db;
        }
        .notification.warning {
          background-color: #f39c12;
        }
      `;
      document.head.appendChild(style);
    }

    // Create notification element
    const notification = document.createElement("div");
    notification.className = `notification ${type}`;
    notification.textContent = message;

    // Add to body
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
});
