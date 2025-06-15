document.addEventListener("DOMContentLoaded", function () {
  const tagsFilterButton = document.getElementById("tagsFilterButton");
  const tagsFilterPopup = document.getElementById("tagsFilterPopup");
  const applyTagsFilterButton = document.getElementById("applyTagsFilter");
  const sortByButton = document.getElementById("sortByButton");
  const sortByPopup = document.getElementById("sortByPopup");
  const tagsCount = document.getElementById("tagsCount");
  const categorySearchInput = document.getElementById("category-search-input");
  const searchCategoryButton = document.getElementById(
    "search-category-button"
  );
  const headerSearch = document.getElementById("header-search");
  const headerSearchBtn = document.getElementById("header-search-btn");

  let openPopup = null;
  let selectedTags = [];

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

  // Force clear all stale data on every page load to prevent caching issues
  clearStaleLibraryData();

  // Add debug logging to track library context
  const currentLibrarySlug = getCurrentLibrarySlug();
  const currentLibraryName =
    document.querySelector('meta[name="current-library-name"]')?.content ||
    "Unknown";
  console.log(
    `[Library Debug] Page loaded for library: ${currentLibraryName} (slug: ${currentLibrarySlug})`
  );

  // Initialize UI
  initializeUI();
  setupEventListeners();

  /**
   * Initialize UI elements
   */
  function initializeUI() {
    // Set up popups
    setupPopup(tagsFilterButton, tagsFilterPopup);
    setupPopup(sortByButton, sortByPopup);

    // Initialize tags count
    updateTagsFromURL();
  }

  /**
   * Set up event listeners
   */
  function setupEventListeners() {
    // Category navigation is now handled by HTML links, no JS needed here

    // Setup search functionality
    if (searchCategoryButton && categorySearchInput) {
      searchCategoryButton.addEventListener("click", function () {
        performSearch(categorySearchInput.value);
      });

      categorySearchInput.addEventListener("keypress", function (e) {
        if (e.key === "Enter") {
          performSearch(this.value);
        }
      });
    }

    // Setup header search
    if (headerSearchBtn && headerSearch) {
      headerSearchBtn.addEventListener("click", function () {
        performSearch(headerSearch.value);
      });

      headerSearch.addEventListener("keypress", function (e) {
        if (e.key === "Enter") {
          performSearch(this.value);
        }
      });
    }

    // Setup tag filtering
    if (applyTagsFilterButton) {
      applyTagsFilterButton.addEventListener("click", applyTagsFilter);
    }

    // Setup sort by
    if (sortByPopup) {
      sortByPopup.addEventListener("click", handleSortBySelection);
    }

    // Setup collection and cart buttons
    setupActionButtons();

    // Close popups when clicking outside
    document.addEventListener("click", closePopups);
  }

  /**
   * Setup popup toggle functionality
   */
  function setupPopup(button, popup) {
    if (!button || !popup) return;

    button.addEventListener("click", (event) => {
      event.stopPropagation();
      if (openPopup && openPopup !== popup) {
        openPopup.style.display = "none";
      }
      popup.style.display = popup.style.display === "block" ? "none" : "block";
      openPopup = popup.style.display === "block" ? popup : null;
    });

    popup.addEventListener("click", (event) => event.stopPropagation());
  }

  /**
   * Handle search form submission
   */
  function performSearch(query) {
    if (!query || !query.trim()) return;

    // Get current URL and parameters
    const url = new URL(window.location);
    url.searchParams.set("search", query.trim());

    // Redirect to the same page with search parameter
    window.location.href = url.toString();
  }

  /**
   * Apply tags filter
   */
  function applyTagsFilter() {
    // Get selected tags
    selectedTags = Array.from(
      tagsFilterPopup.querySelectorAll("input:checked")
    ).map((input) => input.value);

    // Update tags count display
    updateTagsCount();

    // Build URL with tags parameter
    const url = new URL(window.location);

    // Clear existing tags
    url.searchParams.delete("tags");

    // Add each tag as a separate parameter for proper server-side handling
    selectedTags.forEach((tag) => {
      url.searchParams.append("tags", tag);
    });

    // Redirect to filtered URL
    window.location.href = url.toString();

    // Close popup
    closePopups();
  }

  /**
   * Handle sort by selection
   */
  function handleSortBySelection(event) {
    if (event.target.tagName === "A") {
      event.preventDefault();
      const sortType = event.target.getAttribute("data-sort");

      // Update URL with sort parameter
      const url = new URL(window.location);
      url.searchParams.set("sort_by", sortType);

      // Redirect to sorted URL
      window.location.href = url.toString();

      // Close popup
      closePopups();
    }
  }

  /**
   * Get tag selection from URL
   */
  function updateTagsFromURL() {
    const url = new URL(window.location);
    const tags = url.searchParams.getAll("tags");

    if (tags.length > 0) {
      selectedTags = tags;

      // Check corresponding checkboxes
      selectedTags.forEach((tag) => {
        const checkbox = document.querySelector(`input[value="${tag}"]`);
        if (checkbox) checkbox.checked = true;
      });

      // Update count display
      updateTagsCount();
    }
  }

  /**
   * Update tags count display
   */
  function updateTagsCount() {
    if (tagsCount) {
      tagsCount.textContent = selectedTags.length;
    }
  }

  /**
   * Set up add to cart and favorites buttons
   */
  function setupActionButtons() {
    // Add to cart buttons
    document.querySelectorAll(".add-to-cart").forEach((button) => {
      button.addEventListener("click", function (e) {
        e.stopPropagation();
        const videoId = this.getAttribute("data-id");
        addToCart(videoId);
      });
    });

    // Add to favorites buttons
    document.querySelectorAll(".like").forEach((button) => {
      button.addEventListener("click", function (e) {
        e.stopPropagation();
        const videoId = this.getAttribute("data-id");
        addToFavorites(videoId);
      });
    });

    // Click on thumbnail for preview
    document.querySelectorAll(".clip-thumbnail").forEach((thumbnail) => {
      thumbnail.addEventListener("click", function () {
        const videoId = this.getAttribute("data-video-id");
        openVideoPreview(videoId);
      });
    });
  }

  /**
   * Close all popups
   */
  function closePopups() {
    if (openPopup) {
      openPopup.style.display = "none";
      openPopup = null;
    }
  }

  /**
   * Get CSRF token from cookies
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
   * Add item to cart
   * @param {number} videoId - ID of video to add
   */
  function addToCart(videoId, resolution = "HD", price = "0") {
    // Get CSRF token
    const csrftoken = getCSRFToken();
    if (!csrftoken) {
      console.error("CSRF token not found");
      showNotification("Error: CSRF token not found", "error");
      return;
    }

    // Create URL-encoded form data
    const formData = new URLSearchParams();
    formData.append("video_id", videoId);
    formData.append("resolution", resolution);
    formData.append("price", price);

    // Fetch request to add to cart
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
        throw new Error("Network response was not ok");
      })
      .then((data) => {
        if (data.success) {
          // Update cart cache in localStorage
          updateCartCache(videoId, resolution, price);
          showNotification("Video added to cart");
        } else {
          showNotification(
            "Error: " + (data.error || "Failed to add to cart"),
            "error"
          );
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        // Try to update cache anyway
        updateCartCache(videoId, resolution, price);
        showNotification("Added to local cart", "info");
      });
  }

  /**
   * Add video to favorites/collection
   * @param {number} videoId - ID of video to add
   */
  function addToFavorites(videoId) {
    // Get CSRF token
    const csrftoken = getCSRFToken();
    if (!csrftoken) {
      console.error("CSRF token not found");
      showNotification("Error: CSRF token not found", "error");
      return;
    }

    // Log what we're sending
    console.log(`Adding video ID ${videoId} to collection`);

    // Create URL-encoded form data
    const formData = new URLSearchParams();
    formData.append("clip_id", videoId);

    // Fetch request to add to favorites
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
        throw new Error(`Network response error: ${response.status}`);
      })
      .then((data) => {
        console.log("Response data:", data);
        if (data.success) {
          // Update collection cache
          updateCollectionCache(videoId);
          showNotification("Video added to your collection");
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
        showNotification("Added to local collection", "info");
      });
  }

  /**
   * Update the client-side cart cache
   * @param {number} videoId - ID of video to add
   * @param {string} resolution - Resolution of the video
   * @param {number|string} price - Price of the video
   */
  function updateCartCache(videoId, resolution, price) {
    const videoCard = document.querySelector(`.clip[data-id="${videoId}"]`);
    if (!videoCard) {
      console.error(`Video card with ID ${videoId} not found`);
      return;
    }

    // Create video object from DOM elements
    const videoObj = {
      id: videoId,
      title: videoCard.querySelector(".clip-title")?.textContent || "Untitled",
      thumbnail: videoCard.querySelector("img")?.src || "",
      description:
        videoCard.querySelector(".clip-description")?.textContent || "",
      resolution: resolution,
      price: price,
    };

    // Get tags if available
    const tags = [];
    videoCard.querySelectorAll(".tag").forEach((tag) => {
      tags.push(tag.textContent);
    });
    videoObj.tags = tags;

    // Get existing cart or create new one
    let cart = JSON.parse(localStorage.getItem(getCartStorageKey())) || [];

    // Check if item already exists in cart
    const existingItemIndex = cart.findIndex((item) => item.id == videoId);
    if (existingItemIndex >= 0) {
      // Update quantity if it exists
      if (cart[existingItemIndex].quantity) {
        cart[existingItemIndex].quantity += 1;
      } else {
        cart[existingItemIndex].quantity = 2;
      }
    } else {
      // Add new item with quantity 1
      videoObj.quantity = 1;
      cart.push(videoObj);
    }

    // Save cart to localStorage
    localStorage.setItem(getCartStorageKey(), JSON.stringify(cart));
  }

  /**
   * Update the client-side collection cache
   * @param {number} videoId - ID of video to add
   */
  function updateCollectionCache(videoId) {
    // Find the correct card containing this video
    const videoCard = document.querySelector(
      `.clip-thumbnail[data-video-id="${videoId}"]`
    );
    if (!videoCard) {
      console.error(`Video card with ID ${videoId} not found`);
      return;
    }

    const clipElement = videoCard.closest(".clip");
    if (!clipElement) {
      console.error(
        `Could not find parent clip element for video ID ${videoId}`
      );
      return;
    }

    // Create video object from DOM elements
    const videoObj = {
      id: videoId,
      title: clipElement.querySelector("h2")?.textContent || "Untitled",
      thumbnail: clipElement.querySelector("img")?.src || "",
      description: "",
    };

    // Get tags if available
    const tags = [];
    clipElement.querySelectorAll(".tag").forEach((tag) => {
      tags.push(tag.textContent);
    });
    videoObj.tags = tags;

    // Get existing collection or create new one
    let collection =
      JSON.parse(localStorage.getItem(getCollectionStorageKey())) || [];

    // Only add if item doesn't exist already
    if (!collection.some((item) => item.id == videoId)) {
      collection.push(videoObj);
      localStorage.setItem(
        getCollectionStorageKey(),
        JSON.stringify(collection)
      );
    }
  }

  /**
   * Open video preview
   */
  function openVideoPreview(videoId) {
    // Navigate to the video detail page
    window.location.href = `/clip/${videoId}/`;
  }

  /**
   * Show a toast notification
   * @param {string} message - Message to display
   * @param {string} type - Type of notification: 'success', 'error', or 'warning'
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

  /**
   * Initialize the page
   */
  function initializePage() {
    // Clear stale data from other libraries first
    clearStaleLibraryData();

    // Setup localStorage if not already present
    if (!localStorage.getItem(getCartStorageKey())) {
      localStorage.setItem(getCartStorageKey(), JSON.stringify([]));
    }

    if (!localStorage.getItem(getCollectionStorageKey())) {
      localStorage.setItem(getCollectionStorageKey(), JSON.stringify([]));
    }

    // Attach event handlers to buttons if needed
    // This would be place to attach buttons if they're added dynamically
  }

  // Run initialization when DOM is loaded
  document.addEventListener("DOMContentLoaded", initializePage);

  // Clear stale localStorage data from other libraries
  function clearStaleLibraryData() {
    const currentLibrarySlug = getCurrentLibrarySlug();
    const currentLibraryName =
      document.querySelector('meta[name="current-library-name"]')?.content ||
      "Unknown";
    const keysToRemove = [];

    console.log(
      `[Cache Debug] Clearing cache for library switch to: ${currentLibraryName} (${currentLibrarySlug})`
    );

    // Check all localStorage keys
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (
        key &&
        (key.startsWith("userCart_") ||
          key.startsWith("userCollection_") ||
          key.startsWith("categoryCache_") ||
          key.startsWith("libraryData_"))
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
      console.log(`[Cache Debug] Removed stale key: ${key}`);
    });

    // Also clear any general cache that might interfere
    const generalCacheKeys = [
      "lastLibrarySlug",
      "cachedCategories",
      "lastVisitedLibrary",
      "categoryData",
    ];
    generalCacheKeys.forEach((key) => {
      const storedValue = localStorage.getItem(key);
      if (storedValue && storedValue !== currentLibrarySlug) {
        localStorage.removeItem(key);
        console.log(
          `[Cache Debug] Removed general cache key: ${key} (was: ${storedValue})`
        );
      }
    });

    // Force clear any cached DOM or JS state by triggering a more aggressive reset
    if (typeof window.libraryCache !== "undefined") {
      window.libraryCache = {};
    }

    if (keysToRemove.length > 0) {
      console.log(
        `[Cache Debug] Cleared ${keysToRemove.length} stale localStorage entries for library switch`
      );
    }

    // Set current library slug to prevent future caching issues
    localStorage.setItem("lastLibrarySlug", currentLibrarySlug);
    console.log(`[Cache Debug] Set lastLibrarySlug to: ${currentLibrarySlug}`);
  }
});
