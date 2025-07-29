document.addEventListener("DOMContentLoaded", function () {
  const addToCartButton = document.getElementById("addToCartButton");
  const addToCollectionButton = document.getElementById(
    "addToCollectionButton"
  );

  // Get current library context for localStorage keys
  function getCurrentLibrarySlug() {
    // Try to get from meta tag first (most reliable)
    const metaLibrarySlug = document.querySelector(
      'meta[name="current-library-slug"]'
    )?.content;
    if (metaLibrarySlug) {
      return metaLibrarySlug;
    }

    // Try to get from URL path as fallback
    const pathParts = window.location.pathname.split("/");
    const libraryIndex = pathParts.indexOf("library");
    if (libraryIndex !== -1 && pathParts[libraryIndex + 1]) {
      return pathParts[libraryIndex + 1];
    }

    // Fallback to 'paletta' if no library found
    return "paletta";
  }

  // Get library-specific localStorage keys
  function getCartStorageKey() {
    return `userCart_${getCurrentLibrarySlug()}`;
  }

  function getCollectionStorageKey() {
    return `userCollection_${getCurrentLibrarySlug()}`;
  }

  // Clear stale localStorage data from other libraries
  function clearStaleLibraryData() {
    const currentLibrarySlug = getCurrentLibrarySlug();
    const keysToRemove = [];

    // Check all localStorage keys
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (
        key &&
        (key.startsWith("userCart_") ||
          key.startsWith("userCollection_") ||
          key.startsWith("categoryCache_"))
      ) {
        // If it's not for the current library, mark for removal
        if (!key.endsWith(`_${currentLibrarySlug}`)) {
          keysToRemove.push(key);
        }
      }
    }

    // Remove stale keys
    keysToRemove.forEach((key) => {
      localStorage.removeItem(key);
    });

    // Also clear any general cache that might interfere
    const generalCacheKeys = [
      "lastLibrarySlug",
      "cachedCategories",
      "lastVisitedLibrary",
    ];
    generalCacheKeys.forEach((key) => {
      if (
        localStorage.getItem(key) &&
        localStorage.getItem(key) !== currentLibrarySlug
      ) {
        localStorage.removeItem(key);
      }
    });

    // Set current library slug to prevent future caching issues
    localStorage.setItem("lastLibrarySlug", currentLibrarySlug);
  }

  // Clear stale data and initialize localStorage for cart and collection if not present
  clearStaleLibraryData();

  // Clear stale data and initialize localStorage for cart and collection if not present
  if (!localStorage.getItem(getCollectionStorageKey())) {
    localStorage.setItem(getCollectionStorageKey(), JSON.stringify([]));
  }
  if (!localStorage.getItem(getCartStorageKey())) {
    localStorage.setItem(getCartStorageKey(), JSON.stringify([]));
  }

  setupEventListeners();

  /**
   * Set up event listeners
   */
  function setupEventListeners() {
    // Add to cart functionality - direct call without popup
    if (addToCartButton) {
      addToCartButton.addEventListener("click", function (event) {
        event.preventDefault();
        handleAddToCart();
      });
    }

    // Add to collection functionality
    if (addToCollectionButton) {
      addToCollectionButton.addEventListener("click", function (event) {
        event.preventDefault();
        handleAddToCollection();
      });
    }
  }

  /**
   * Handle adding to cart
   */
  function handleAddToCart() {
    // Use default resolution (no popup needed)
    const resolution = "HD";

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

    // Send AJAX request to add to cart (correct endpoint)
    fetch("/api/orders/add-to-cart/", {
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
          updateCartCache(videoId, resolution);

          // Display success message
          const clipTitle = document.querySelector("h1").textContent;
          showNotification(`"${clipTitle}" added to cart (${resolution})`);

          // Update cart count in header if exists
          const cartCountElement = document.querySelector(".cart-count");
          if (cartCountElement && data.cart_count) {
            cartCountElement.textContent = data.cart_count;
          }
        } else {
          showNotification("Error: " + (data.message || data.error), "error");
        }
      })
      .catch(() => {
        updateCartCache(videoId, resolution);
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

    // Create URL-encoded form data
    const formData = new URLSearchParams();
    formData.append("clip_id", videoId);

    // Send POST request to add to collection (correct endpoint)
    fetch("/api/orders/add-to-collection/", {
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
          // Update client-side collection cache
          updateCollectionCache(videoId);

          // Show success notification
          const clipTitle = document.querySelector("h1").textContent;
          showNotification(`"${clipTitle}" added to your favourites!`);
        } else {
          showNotification(
            "Error: " + (data.error || "Failed to add to favourites"),
            "error"
          );
        }
      })
      .catch(() => {
        // Still try to update cache anyway for offline functionality
        updateCollectionCache(videoId);
        showNotification("Added to local favourites (offline mode)", "info");
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
  function updateCartCache(videoId, resolution) {
    try {
      // Get current cart from localStorage
      const cart = JSON.parse(localStorage.getItem(getCartStorageKey())) || [];

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
          updated: new Date().toISOString(),
          quantity: (cart[existingItemIndex].quantity || 1) + 1,
        };
      } else {
        // Add new item with quantity 1
        cart.push({
          id: videoId,
          ...videoDetails,
          resolution: resolution,
          added: new Date().toISOString(),
          quantity: 1,
        });
      }

      // Save back to localStorage
      localStorage.setItem(getCartStorageKey(), JSON.stringify(cart));
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
        JSON.parse(localStorage.getItem(getCollectionStorageKey())) || [];

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
          getCollectionStorageKey(),
          JSON.stringify(collection)
        );
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
      description: document.querySelector(".video-info p")?.textContent || "",
    };

    // Get subject area
    const subjectAreaElement = document.querySelector(".subject-area-name");
    if (subjectAreaElement) {
      videoObj.subject_area = subjectAreaElement.textContent.trim();
    }

    // Get content types
    const contentTypeBadges = document.querySelectorAll(".content-type-badge");
    if (contentTypeBadges.length > 0) {
      videoObj.content_types = Array.from(contentTypeBadges).map((badge) =>
        badge.textContent.trim()
      );
    }

    // Get paletta category if exists
    const palettaCategoryElement = document.querySelector(
      ".paletta-category-name"
    );
    if (palettaCategoryElement) {
      videoObj.paletta_category = palettaCategoryElement.textContent.trim();
    }

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
    document.querySelectorAll(".tag-badge").forEach((tag) => {
      tags.push(tag.textContent.trim());
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
