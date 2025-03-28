document.addEventListener("DOMContentLoaded", function () {
  const tagsFilterButton = document.getElementById("tagsFilterButton");
  const tagsFilterPopup = document.getElementById("tagsFilterPopup");
  const applyTagsFilterButton = document.getElementById("applyTagsFilter");
  const sortByButton = document.getElementById("sortByButton");
  const sortByPopup = document.getElementById("sortByPopup");
  const tagsCount = document.getElementById("tagsCount");
  const clipsContainer = document.getElementById("clips-container");
  const paginationControls = document.getElementById("pagination-controls");
  const searchButton = document.getElementById("search-button");
  const categorySearch = document.getElementById("category-search");
  const categorySearchInput = document.getElementById("category-search-input");
  const searchCategoryButton = document.getElementById(
    "search-category-button"
  );
  const headerSearch = document.getElementById("header-search");
  const headerSearchBtn = document.getElementById("header-search-btn");

  let openPopup = null;
  let currentPage = 1;
  let currentCategory = "all";
  let currentSortBy = "newest";
  let currentSearchQuery = "";
  let selectedTags = [];
  let totalPages = 1;

  // Initialize app
  initializeUI();
  loadInitialVideos();

  // Initialize UI elements
  function initializeUI() {
    // Set up popups
    togglePopup(tagsFilterButton, tagsFilterPopup);
    togglePopup(sortByButton, sortByPopup);

    // Set up filtering and search
    if (applyTagsFilterButton) {
      applyTagsFilterButton.addEventListener("click", applyTagsFilter);
    }

    if (sortByPopup) {
      sortByPopup.addEventListener("click", handleSortBySelection);
      sortByPopup.addEventListener("click", (event) => event.stopPropagation());
    }

    if (tagsFilterPopup) {
      tagsFilterPopup.addEventListener("click", (event) =>
        event.stopPropagation()
      );
    }

    // Set up category navigation in sidebar
    document.querySelectorAll(".category-list li").forEach((categoryItem) => {
      categoryItem.addEventListener("click", function () {
        const category = this.getAttribute("data-category");
        const displayName = this.textContent.trim();
        changeCategory(category, displayName);
      });
    });

    // Set up search in sidebar
    if (searchButton && categorySearch) {
      searchButton.addEventListener("click", function () {
        performSearch(categorySearch.value);
      });

      categorySearch.addEventListener("keypress", function (e) {
        if (e.key === "Enter") {
          performSearch(this.value);
        }
      });
    }

    // Set up category-specific search
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

    // Set up header search
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

    // Close popups when clicking outside
    document.addEventListener("click", closePopups);

    // Get initial filter values from URL
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has("category")) {
      currentCategory = urlParams.get("category");
      setActiveCategoryInSidebar(currentCategory);
    } else {
      // Check if we're on a category page from the URL path
      const pathMatch = window.location.pathname.match(/\/category\/([^\/]+)/);
      if (pathMatch && pathMatch[1]) {
        currentCategory = decodeURIComponent(pathMatch[1]);
        setActiveCategoryInSidebar(currentCategory);
      }
    }

    if (urlParams.has("search")) {
      currentSearchQuery = urlParams.get("search");
      if (categorySearch) categorySearch.value = currentSearchQuery;
      if (categorySearchInput) categorySearchInput.value = currentSearchQuery;
    }

    if (urlParams.has("sort")) {
      currentSortBy = urlParams.get("sort");
    }

    if (urlParams.has("tags")) {
      selectedTags = urlParams.get("tags").split(",");
      updateTagsCount();
    }
  }

  // Load videos from API
  function loadVideos(page = 1) {
    // Show loading indicator
    clipsContainer.innerHTML =
      '<div class="loading-indicator">Loading clips...</div>';

    // Build API URL with filters
    let apiUrl = `/api/videos/?page=${page}`;

    if (!currentCategory || currentCategory === "all") {
      newPath = "/clip_store/";
    } else {
      // First decode the category in case it's already URL-encoded
      const decodedCategory = decodeURIComponent(currentCategory);
      // Then format category: replace spaces with hyphens for URL path
      const formattedCategory = decodedCategory.replace(/\s+/g, "-");
      newPath = `/category/${encodeURIComponent(formattedCategory)}/`;
    }

    // Add search parameter if needed
    if (currentSearchQuery) {
      apiUrl += `&search=${encodeURIComponent(currentSearchQuery)}`;
    }

    // Add sort parameter
    if (currentSortBy) {
      apiUrl += `&sort_by=${currentSortBy}`;
    }

    // Add tags if selected
    if (selectedTags.length > 0) {
      selectedTags.forEach((tag) => {
        apiUrl += `&tags=${encodeURIComponent(tag)}`;
      });
    }

    // Fetch videos from API
    fetch(apiUrl, {
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => {
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error(
              `Category "${currentCategory}" not found. Please check the category name.`
            );
          }
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        renderVideos(data.results || data);
        // Set up pagination if available
        if (data.count && data.results) {
          totalPages = Math.ceil(data.count / 12); // 12 is page size from StandardResultsSetPagination
          renderPagination(currentPage, totalPages);
        } else {
          paginationControls.innerHTML = "";
        }
      })
      .catch((error) => {
        console.error("Error fetching videos:", error);
        clipsContainer.innerHTML = `
          <div class="error-message">
            <h3>Error loading videos</h3>
            <p>${error.message}</p>
            <p>If you're trying to access a category with spaces in the name, make sure the category exists in the database.</p>
          </div>`;
      });
  }

  // Initial video load
  function loadInitialVideos() {
    // Get initial filter values from URL
    const urlParams = new URLSearchParams(window.location.search);
    currentPage = parseInt(urlParams.get("page") || "1");

    // Load videos
    loadVideos(currentPage);

    // Update category title and banner
    updateCategoryUI(currentCategory);
  }

  // Render videos in the grid
  function renderVideos(videos) {
    if (!clipsContainer) return;

    // Clear container
    clipsContainer.innerHTML = "";

    if (!videos || videos.length === 0) {
      clipsContainer.innerHTML =
        '<div class="no-videos">No videos found.</div>';
      return;
    }

    // Create video cards
    videos.forEach((video) => {
      const videoCard = document.createElement("div");
      videoCard.className = "clip";

      // Generate duration display in MM:SS format
      let durationDisplay = "00:00";
      if (video.duration) {
        const minutes = Math.floor(video.duration / 60);
        const seconds = video.duration % 60;
        durationDisplay = `${minutes.toString().padStart(2, "0")}:${seconds
          .toString()
          .padStart(2, "0")}`;
      }

      // Determine thumbnail URL
      const thumbnailUrl =
        video.thumbnail_url || "/static/picture/default-thumbnail.png";

      videoCard.innerHTML = `
        <div class="clip-thumbnail" data-video-id="${video.id}">
          <img src="${thumbnailUrl}" alt="${video.title}">
          <div class="duration-badge">${durationDisplay}</div>
          <div class="play-button">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M8 5V19L19 12L8 5Z" fill="white"/>
            </svg>
          </div>
        </div>
        <h2>${video.title}</h2>
   <div class="clipactions">
          <button class="like" data-id="${video.id}">
       <svg viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg"><rect fill="none" height="256" width="256"/><path d="M224.6,51.9a59.5,59.5,0,0,0-43-19.9,60.5,60.5,0,0,0-44,17.6L128,59.1l-7.5-7.4C97.2,28.3,59.2,26.3,35.9,47.4a59.9,59.9,0,0,0-2.3,87l83.1,83.1a15.9,15.9,0,0,0,22.6,0l81-81C243.7,113.2,245.6,75.2,224.6,51.9Z"/></svg>
       <span>add to collection</span>
     </button>
          <button class="add-to-cart" data-id="${video.id}"> 
       <svg baseProfile="tiny" height="24px" version="1.2" viewBox="0 0 24 24" width="24px" xml:space="preserve" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><g id="Layer_1"><g>
         <path d="M20.756,5.345C20.565,5.126,20.29,5,20,5H6.181L5.986,3.836C5.906,3.354,5.489,3,5,3H2.75c-0.553,0-1,0.447-1,1    s0.447,1,1,1h1.403l1.86,11.164c0.008,0.045,0.031,0.082,0.045,0.124c0.016,0.053,0.029,0.103,0.054,0.151    c0.032,0.066,0.075,0.122,0.12,0.179c0.031,0.039,0.059,0.078,0.095,0.112c0.058,0.054,0.125,0.092,0.193,0.13    c0.038,0.021,0.071,0.049,0.112,0.065C6.748,16.972,6.87,17,6.999,17C7,17,18,17,18,17c0.553,0,1-0.447,1-1s-0.447-1-1-1H7.847    l-0.166-1H19c0.498,0,0.92-0.366,0.99-0.858l1-7C21.031,5.854,20.945,5.563,20.756,5.345z M18.847,7l-0.285,2H15V7H18.847z M14,7    v2h-3V7H14z M14,10v2h-3v-2H14z M10,7v2H7C6.947,9,6.899,9.015,6.852,9.03L6.514,7H10z M7.014,10H10v2H7.347L7.014,10z M15,12v-2    h3.418l-0.285,2H15z"/><circle cx="8.5" cy="19.5" r="1.5"/><circle cx="17.5" cy="19.5" r="1.5"/></g></g></svg>
        <span>add to cart</span>
     </button>
        </div>
      `;

      clipsContainer.appendChild(videoCard);
    });

    // Add click listeners for preview modal
    document.querySelectorAll(".clip-thumbnail").forEach((thumbnail) => {
      thumbnail.addEventListener("click", function () {
        const videoId = this.getAttribute("data-video-id");
        openVideoPreviewModal(videoId);
      });
    });

    // Add click listeners for add to cart
    document.querySelectorAll(".add-to-cart").forEach((button) => {
      button.addEventListener("click", function (event) {
        event.stopPropagation();
        const videoId = this.getAttribute("data-id");
        addToCart(videoId);
      });
    });

    // Add click listeners for add to favorites
    document.querySelectorAll(".like").forEach((button) => {
      button.addEventListener("click", function (event) {
        event.stopPropagation();
        const videoId = this.getAttribute("data-id");
        addToFavorites(videoId);
      });
    });
  }

  // Render pagination controls
  function renderPagination(currentPage, totalPages) {
    if (!paginationControls) return;

    paginationControls.innerHTML = "";

    if (totalPages <= 1) return;

    // Create pagination container
    const paginationWrapper = document.createElement("div");
    paginationWrapper.className = "pagination-wrapper";

    // Previous button
    if (currentPage > 1) {
      const prevButton = document.createElement("button");
      prevButton.className = "pagination-btn prev";
      prevButton.innerHTML = "&laquo; Previous";
      prevButton.addEventListener("click", () => changePage(currentPage - 1));
      paginationWrapper.appendChild(prevButton);
    }

    // Page numbers
    const maxPageButtons = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxPageButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxPageButtons - 1);

    if (endPage - startPage + 1 < maxPageButtons) {
      startPage = Math.max(1, endPage - maxPageButtons + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      const pageButton = document.createElement("button");
      pageButton.className = `pagination-btn page ${
        i === currentPage ? "active" : ""
      }`;
      pageButton.textContent = i;
      pageButton.addEventListener("click", () => changePage(i));
      paginationWrapper.appendChild(pageButton);
    }

    // Next button
    if (currentPage < totalPages) {
      const nextButton = document.createElement("button");
      nextButton.className = "pagination-btn next";
      nextButton.innerHTML = "Next &raquo;";
      nextButton.addEventListener("click", () => changePage(currentPage + 1));
      paginationWrapper.appendChild(nextButton);
    }

    paginationControls.appendChild(paginationWrapper);
  }

  // Change page
  function changePage(page) {
    currentPage = page;
    loadVideos(page);

    // Update URL without reloading
    updateUrlParams();

    // Scroll to top of content
    document.querySelector(".main-content").scrollTop = 0;
  }

  // Change category
  function changeCategory(category, displayName) {
    currentCategory = category;
    currentPage = 1;

    // Update active category in sidebar
    setActiveCategoryInSidebar(category);

    // Update UI
    updateCategoryUI(category, displayName);

    // Load videos
    loadVideos(currentPage);

    // Update URL
    updateUrlParams();
  }

  // Set active category in sidebar
  function setActiveCategoryInSidebar(category) {
    const categoryItems = document.querySelectorAll(".category-list li");
    if (!categoryItems.length) return;

    categoryItems.forEach((item) => {
      if (item.getAttribute("data-category") === category) {
        item.classList.add("active");
      } else {
        item.classList.remove("active");
      }
    });
  }

  // Update category title and banner
  function updateCategoryUI(category, displayName) {
    // If displayName is not provided, try to get it from the sidebar
    if (!displayName && category !== "all") {
      const categoryElement = document.querySelector(
        `.category-list li[data-category="${category}"]`
      );
      if (categoryElement) {
        displayName = categoryElement.textContent.trim();
      } else {
        // Fallback to a capitalized version of the category
        displayName = category.charAt(0).toUpperCase() + category.slice(1);
      }
    }

    // Update page title
    const pageTitle =
      category === "all"
        ? "All Videos - Paletta"
        : `${displayName || category} - Paletta`;
    document.title = pageTitle;

    // Get the banner element
    const banner = document.querySelector(".banner");
    if (!banner) return;

    // Update banner based on category
    if (category === "all") {
      // All videos view - simpler structure
      banner.innerHTML = `
        <img src="/static/picture/All.png" alt="All">
        <h1 class="banner-title">All Videos in the Library</h1>
      `;
    } else {
      // Category-specific view - container with image and title
      banner.innerHTML = `
        <div class="imagecontainer">
          <h1 class="banner-title">${displayName || category}</h1>
          <img src="/static/picture/All.png" alt="${
            displayName || category
          }" class="category-image">
        </div>
      `;

      // Get category image from API
      const categoryImage = banner.querySelector(".category-image");
      if (categoryImage) {
        loadCategoryImage(category, categoryImage);
      }
    }
  }

  // Load banner image from API with fallback to static files
  // Load banner image from API with fallback to static files
  function loadCategoryImage(category, imageElement) {
    fetch("/api/videos/categories/", {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    })
      .then((response) =>
        response.ok
          ? response.json()
          : Promise.reject("Failed to fetch categories")
      )
      .then((data) => {
        const categories = data.results || data;

        // Find matching category (case-insensitive)
        const categoryData = categories.find(
          (cat) => cat.name.toLowerCase() === category.toLowerCase()
        );

        if (categoryData) {
          // Update image if available
          if (categoryData.banner_url) {
            imageElement.src = categoryData.banner_url;
          } else if (categoryData.image_url) {
            imageElement.src = categoryData.image_url;
          }
        }
      })
      .catch((error) => {
        console.error("Error loading category image:", error);
      });
  }

  // Perform search
  function performSearch(query) {
    currentSearchQuery = query.trim();
    currentPage = 1;

    // Update both search inputs if they exist
    if (categorySearch) categorySearch.value = currentSearchQuery;
    if (categorySearchInput) categorySearchInput.value = currentSearchQuery;
    if (headerSearch) headerSearch.value = currentSearchQuery;

    // Load videos
    loadVideos(currentPage);

    // Update URL
    updateUrlParams();
  }

  // Update URL parameters
  function updateUrlParams() {
    // Create the path based on category
    let newPath;

    if (!currentCategory || currentCategory === "all") {
      newPath = "/clip-store/";
    } else {
      newPath = `/category/${encodeURIComponent(currentCategory)}/`;
    }

    // Add query parameters
    const params = new URLSearchParams();

    if (currentSearchQuery) {
      params.set("search", currentSearchQuery);
    }

    if (currentPage > 1) {
      params.set("page", currentPage);
    }

    if (currentSortBy && currentSortBy !== "newest") {
      params.set("sort", currentSortBy);
    }

    if (selectedTags.length > 0) {
      params.set("tags", selectedTags.join(","));
    }

    // Build full URL and update
    const queryString = params.toString() ? `?${params.toString()}` : "";
    const newUrl = `${newPath}${queryString}`;

    window.history.pushState({ path: newUrl }, "", newUrl);
  }

  // Handle sort by selection
  function handleSortBySelection(event) {
    if (event.target.tagName === "A") {
      event.preventDefault();
      const sortType = event.target.getAttribute("data-sort");

      // Update current sort
      currentSortBy = sortType;
      currentPage = 1;

      // Load videos
      loadVideos(currentPage);

      // Update URL
      updateUrlParams();

      // Close popup
      closePopups();
    }
  }

  // Apply tags filter
  function applyTagsFilter() {
    // Get selected tags
    selectedTags = Array.from(
      tagsFilterPopup.querySelectorAll("input:checked")
    ).map((input) => input.value);

    // Update tags count
    updateTagsCount();

    // Reset page
    currentPage = 1;

    // Load videos
    loadVideos(currentPage);

    // Update URL
    updateUrlParams();

    // Close popup
    closePopups();
  }

  // Update tags count display
  function updateTagsCount() {
    if (!tagsCount) return;
    tagsCount.textContent = selectedTags.length;
  }

  // Open video preview modal
  function openVideoPreviewModal(videoId) {
    // Get elements
    const modal = document.getElementById("videoPreviewModal");
    const modalTitle = document.getElementById("modal-video-title");
    const modalVideo = document.getElementById("preview-video");
    const modalDescription = document.getElementById("modal-video-description");
    const modalDuration = document.getElementById("modal-video-duration");
    const modalUploader = document.getElementById("modal-video-uploader");
    const modalDate = document.getElementById("modal-video-date");
    const modalTags = document.getElementById("modal-video-tags");
    const addToCartButton = document.getElementById("add-to-cart-modal");
    const addToFavoritesButton = document.getElementById(
      "add-to-favorites-modal"
    );

    if (!modal) return;

    // Show loading state
    modalTitle.textContent = "Loading...";
    modalDescription.textContent = "";
    modalDuration.textContent = "";
    modalUploader.textContent = "";
    modalDate.textContent = "";
    modalTags.innerHTML = "";

    // Get video details from API
    fetch(`/api/videos/${videoId}/`, {
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then((video) => {
        // Set modal content
        modalTitle.textContent = video.title;
        modalDescription.textContent =
          video.description || "No description provided.";

        // Format duration
        if (video.duration) {
          const minutes = Math.floor(video.duration / 60);
          const seconds = video.duration % 60;
          modalDuration.textContent = `${minutes}:${seconds
            .toString()
            .padStart(2, "0")}`;
        } else {
          modalDuration.textContent = "Unknown";
        }

        // Set uploader and date
        modalUploader.textContent = video.uploaded_by_username || "Unknown";

        // Format date
        if (video.upload_date) {
          const uploadDate = new Date(video.upload_date);
          modalDate.textContent = uploadDate.toLocaleDateString();
        } else {
          modalDate.textContent = "Unknown";
        }

        // Add tags
        modalTags.innerHTML = "";
        if (video.tags && video.tags.length > 0) {
          video.tags.forEach((tag) => {
            const tagSpan = document.createElement("span");
            tagSpan.className = "tag";
            tagSpan.textContent = tag.name;
            modalTags.appendChild(tagSpan);
          });
        } else {
          modalTags.innerHTML = "<span class='no-tags'>No tags</span>";
        }

        // Set video source
        if (video.video_file_url) {
          modalVideo.src = video.video_file_url;
          modalVideo.load();
        } else {
          // If no video file URL, show a message
          modalVideo.innerHTML = "Video not available for preview.";
        }

        // Set up add to cart button
        if (addToCartButton) {
          addToCartButton.setAttribute("data-id", video.id);
          addToCartButton.addEventListener("click", function () {
            addToCart(video.id);
          });
        }

        // Set up add to favorites button
        if (addToFavoritesButton) {
          addToFavoritesButton.setAttribute("data-id", video.id);
          addToFavoritesButton.addEventListener("click", function () {
            addToFavorites(video.id);
          });
        }
      })
      .catch((error) => {
        console.error("Error fetching video details:", error);
        modalTitle.textContent = "Error loading video";
        modalDescription.textContent = `Error: ${error.message}`;
      });

    // Show modal
    modal.style.display = "block";

    // Set up close button
    const closeBtn = modal.querySelector(".close-modal");
    if (closeBtn) {
      closeBtn.addEventListener("click", function () {
        modal.style.display = "none";
        // Pause video when closing modal
        if (modalVideo) {
          modalVideo.pause();
        }
      });
    }

    // Close modal when clicking outside
    window.addEventListener("click", function (event) {
      if (event.target === modal) {
        modal.style.display = "none";
        // Pause video when closing modal
        if (modalVideo) {
          modalVideo.pause();
        }
      }
    });
  }

  // Toggle popup visibility
  function togglePopup(button, popup) {
    if (!button || !popup) return;

    button.addEventListener("click", (event) => {
      event.stopPropagation();
      if (openPopup && openPopup !== popup) {
        openPopup.style.display = "none";
      }
      popup.style.display = popup.style.display === "block" ? "none" : "block";
      openPopup = popup.style.display === "block" ? popup : null;
    });
  }

  // Close all popups
  function closePopups() {
    if (openPopup) {
      openPopup.style.display = "none";
      openPopup = null;
    }
  }

  // Add to cart
  function addToCart(videoId) {
    fetch(`/api/videos/${videoId}/`, {
      headers: {
        "Content-Type": "application/json",
      },
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
            thumbnail: video.thumbnail_url,
            price: video.price || 10.99, // Default price if not set
            quantity: 1,
          });
        }

        // Save cart
        localStorage.setItem("cart", JSON.stringify(cart));

        // Show success message
        alert(`${video.title} has been added to the cart!`);
      })
      .catch((error) => {
        console.error("Error adding to cart:", error);
        alert("Error adding video to cart.");
      });
  }

  // Add to favorites
  function addToFavorites(videoId) {
    fetch(`/api/videos/${videoId}/`, {
      headers: {
        "Content-Type": "application/json",
      },
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
            thumbnail: video.thumbnail_url,
            duration: video.duration,
            upload_date: video.upload_date,
          });

          // Save favorites
          localStorage.setItem("favorites", JSON.stringify(favorites));

          // Show success message
          alert(`${video.title} has been added to your collection!`);
        } else {
          // Show already in favorites message
          alert(`${video.title} is already in your collection.`);
        }
      })
      .catch((error) => {
        console.error("Error adding to favorites:", error);
        alert("Error adding video to collection.");
      });
  }
});
