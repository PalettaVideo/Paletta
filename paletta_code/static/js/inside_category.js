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
    // Setup category navigation in sidebar
    document.querySelectorAll(".category-list li").forEach((categoryItem) => {
      categoryItem.addEventListener("click", function () {
        const category = this.getAttribute("data-category");
        window.location.href =
          category === "all"
            ? "/clip-store/"
            : `/category/${encodeURIComponent(category)}/`;
      });
    });

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
      .then((video) => {
        // Get cart from localStorage
        const cart = JSON.parse(localStorage.getItem("cart")) || [];

        // Check if video is already in cart
        const existingItem = cart.find((item) => item.id === video.id);
        if (existingItem) {
          existingItem.quantity += 1;
        } else {
          // Only store necessary information
          cart.push({
            id: video.id,
            title: video.title,
            thumbnail:
              video.thumbnail_url || "/static/picture/default-thumbnail.png",
            price: video.price || 10.99,
            quantity: 1,
          });
        }

        // Save cart
        localStorage.setItem("cart", JSON.stringify(cart));
        alert(`${video.title} has been added to the cart!`);
      })
      .catch((error) => {
        console.error("Error adding to cart:", error);
        alert("Error adding video to cart.");
      });
  }

  /**
   * Add video to favorites
   */
  function addToFavorites(videoId) {
    fetch(`/api/videos/${videoId}/`, {
      headers: { "Content-Type": "application/json" },
    })
      .then((response) => response.json())
      .then((video) => {
        // Get favorites from localStorage
        const favorites = JSON.parse(localStorage.getItem("favorites")) || [];

        // Check if video is already in favorites
        if (!favorites.some((item) => item.id === video.id)) {
          // Only store necessary information
          favorites.push({
            id: video.id,
            title: video.title,
            thumbnail:
              video.thumbnail_url || "/static/picture/default-thumbnail.png",
            duration: video.duration,
            upload_date: video.upload_date,
          });

          // Save favorites
          localStorage.setItem("favorites", JSON.stringify(favorites));
          alert(`${video.title} has been added to your collection!`);
        } else {
          alert(`${video.title} is already in your collection.`);
        }
      })
      .catch((error) => {
        console.error("Error adding to favorites:", error);
        alert("Error adding video to collection.");
      });
  }

  /**
   * Open video preview
   */
  function openVideoPreview(videoId) {
    // This function would open a modal to preview the video
    // Implement according to your UI design
    alert(`Opening preview for video ID: ${videoId}`);
    // You would usually have a modal implementation here
  }
});
