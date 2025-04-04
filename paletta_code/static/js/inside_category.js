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
   * Add video to cart
   */
  function addToCart(videoId) {
    fetch(`/api/videos/${videoId}/`, {
      headers: { "Content-Type": "application/json" },
    })
      .then((response) => response.json())
      .then((data) => {
        // Add to cart logic here
        console.log(`Added video ${videoId} to cart:`, data);
        // Show success message
        showNotification("Video added to cart successfully!");
      })
      .catch((error) => {
        console.error("Error adding to cart:", error);
        showNotification("Failed to add video to cart.", "error");
      });
  }

  /**
   * Add video to favorites/collection
   */
  function addToFavorites(videoId) {
    fetch(`/api/videos/${videoId}/`, {
      headers: { "Content-Type": "application/json" },
    })
      .then((response) => response.json())
      .then((data) => {
        // Add to favorites logic here
        console.log(`Added video ${videoId} to favorites:`, data);
        // Show success message
        showNotification("Video added to collection successfully!");
      })
      .catch((error) => {
        console.error("Error adding to favorites:", error);
        showNotification("Failed to add video to collection.", "error");
      });
  }

  /**
   * Open video preview
   */
  function openVideoPreview(videoId) {
    // This would open a modal or navigate to a video preview page
    console.log("Opening preview for video:", videoId);
    // Placeholder - implement actual preview functionality
  }

  /**
   * Show a notification message
   */
  function showNotification(message, type = "success") {
    // Create notification element if it doesn't exist
    let notification = document.getElementById("notification");
    if (!notification) {
      notification = document.createElement("div");
      notification.id = "notification";
      document.body.appendChild(notification);
    }

    // Set message and type
    notification.textContent = message;
    notification.className = `notification ${type}`;

    // Show notification
    notification.style.display = "block";

    // Hide after 3 seconds
    setTimeout(() => {
      notification.style.display = "none";
    }, 3000);
  }
});
