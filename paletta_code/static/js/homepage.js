document.addEventListener("DOMContentLoaded", function () {
  // initialize the popup menu for the user center
  initPopupMenu();

  // fetch categories if they're not already loaded from the server-side
  const categoriesContainer = document.getElementById("categories-container");
  if (
    categoriesContainer &&
    categoriesContainer.querySelectorAll(".category").length <= 1
  ) {
    fetchCategories();
  } else {
    // try to load category-specific images
    loadCategoryImages();
  }

  // fetch libraries for the more-libraries-nav section
  const librariesContainer = document.getElementById("libraries-container");
  if (
    librariesContainer &&
    librariesContainer.querySelectorAll(".library-button").length <= 1
  ) {
    fetchLibraries();
  }

  // initialize search functionality
  initSearch();

  // initialize sidebar toggle
  initSidebar();
});

function initPopupMenu() {
  const centerButton = document.getElementById("centerButton");
  const popupMenu = document.getElementById("popupMenu");

  if (centerButton && popupMenu) {
    centerButton.addEventListener("click", function (event) {
      event.stopPropagation();
      popupMenu.style.display =
        popupMenu.style.display === "block" ? "none" : "block";
    });

    // close the popup when clicking outside
    document.addEventListener("click", function () {
      popupMenu.style.display = "none";
    });

    popupMenu.addEventListener("click", function (event) {
      event.stopPropagation();
    });
  }
}

function initSidebar() {
  // Set up sidebar toggle functionality
  window.toggleSidebar = function () {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");

    if (sidebar) {
      sidebar.classList.toggle("active");
      if (overlay) {
        if (sidebar.classList.contains("active")) {
          overlay.style.display = "block";
        } else {
          overlay.style.display = "none";
        }
      }
    }
  };

  window.closeSidebar = function () {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");

    if (sidebar) {
      sidebar.classList.remove("active");
      if (overlay) {
        overlay.style.display = "none";
      }
    }
  };
}

function loadCategoryImages() {
  // Find all category images
  const categoryImages = document.querySelectorAll(".category-image");

  // try to load images from the API with cache control
  fetch("/api/videos/categories/", {
    method: "GET",
    cache: "no-cache",
    headers: {
      "Cache-Control": "no-cache",
      Pragma: "no-cache",
    },
  })
    .then((response) =>
      response.ok
        ? response.json()
        : Promise.reject("Failed to fetch categories")
    )
    .then((data) => {
      if (data.results && data.results.length > 0) {
        // create a map of category names to image URLs
        const categoryImageMap = {};
        data.results.forEach((category) => {
          if (category.image_url) {
            categoryImageMap[category.name] = category.image_url;
          }
        });

        // update images with URLs from the API
        categoryImages.forEach((img) => {
          const categoryName = img.getAttribute("data-category");
          if (categoryName && categoryImageMap[categoryName]) {
            img.src = categoryImageMap[categoryName];
          } else {
            // if no image in API, try static file as fallback
            tryLoadStaticImage(img, categoryName);
          }
        });
      } else {
        // if API returns no results, fall back to static files
        categoryImages.forEach((img) => {
          const categoryName = img.getAttribute("data-category");
          tryLoadStaticImage(img, categoryName);
        });
      }
    })
    .catch((error) => {
      console.error("Error fetching category images:", error);
      // if API fails, fall back to static files
      categoryImages.forEach((img) => {
        const categoryName = img.getAttribute("data-category");
        tryLoadStaticImage(img, categoryName);
      });
    });
}

function tryLoadStaticImage(imgElement, categoryName) {
  if (!categoryName) return;

  // try to load the category-specific image from static files
  const specificImage = new Image();
  specificImage.onload = function () {
    // if the image loads successfully, replace the default image
    imgElement.src = this.src;
  };
  specificImage.onerror = function () {
    // if the image fails to load, keep the default image
    console.log(`No specific image found for category: ${categoryName}`);
  };
  specificImage.src = `/static/picture/${categoryName}.png`;
}

function fetchCategories() {
  // Get the current library ID from the URL or session
  const urlParams = new URLSearchParams(window.location.search);
  const libraryId = urlParams.get("library_id");

  // Construct the API URL with library context if available
  let apiUrl = "/api/videos/categories/";
  if (libraryId) {
    apiUrl += `?library_id=${libraryId}`;
  }

  fetch(apiUrl, {
    method: "GET",
    cache: "no-cache",
    headers: {
      "Cache-Control": "no-cache",
      Pragma: "no-cache",
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to fetch categories");
      }
      return response.json();
    })
    .then((data) => {
      if (data.results && data.results.length > 0) {
        updateCategoriesUI(data.results);
      } else {
        // No categories found yet, text is generated from the backend
        pass;
      }
    })
    .catch((error) => {
      console.error("Error fetching categories:", error);
    });
}

function fetchLibraries() {
  fetch("/api/libraries/", {
    method: "GET",
    cache: "no-cache",
    headers: {
      "Cache-Control": "no-cache",
      Pragma: "no-cache",
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to fetch libraries");
      }
      return response.json();
    })
    .then((data) => {
      if (data.results && data.results.length > 0) {
        updateLibrariesUI(data.results);
      }
    })
    .catch((error) => {
      console.error("Error fetching libraries:", error);
    });
}

function updateLibrariesUI(libraries) {
  const librariesContainer = document.getElementById("libraries-container");
  if (!librariesContainer) return;

  // Keep the default Paletta library which should already be there
  const defaultLibrary = librariesContainer.querySelector(".library-button");

  // Clear existing libraries except the default one
  if (defaultLibrary) {
    librariesContainer.innerHTML = "";
    librariesContainer.appendChild(defaultLibrary);
  }

  // Add each library from the API
  libraries.forEach((library) => {
    // Skip adding duplicate of default Paletta if it exists in the API results
    if (library.name.toLowerCase() === "paletta") return;

    const libraryDiv = document.createElement("div");
    libraryDiv.className = "library-button";

    const libraryLink = document.createElement("a");
    libraryLink.href = `/home/?library_id=${library.id}`;

    const img = document.createElement("img");
    // Use the logo from the API if available, otherwise use default
    if (library.logo) {
      img.src = library.logo;
    } else {
      img.src = "/static/picture/default-logo.jpg";
    }
    img.alt = library.name;

    const span = document.createElement("span");
    span.textContent = library.name;

    libraryLink.appendChild(img);
    libraryLink.appendChild(span);
    libraryDiv.appendChild(libraryLink);
    librariesContainer.appendChild(libraryDiv);
  });

  // If no libraries were added (and only the default remains), show a message
  if (librariesContainer.querySelectorAll(".library-button").length <= 1) {
    const noLibraries = document.createElement("p");
    noLibraries.classList.add("no-libraries");
    noLibraries.textContent = "No additional libraries available.";
    librariesContainer.appendChild(noLibraries);
  }
}

function updateCategoriesUI(categories) {
  const categoriesContainer = document.getElementById("categories-container");
  if (!categoriesContainer) return;

  // keep the "All" category which should already be there
  const allCategoryElement = categoriesContainer.querySelector(
    'a[href*="clip_store"]'
  );

  // clear existing categories except "All"
  categoriesContainer.innerHTML = "";

  // add back the "All" category
  if (allCategoryElement) {
    categoriesContainer.appendChild(allCategoryElement);
  }

  // add each category from the API
  categories.forEach((category) => {
    const categoryLink = document.createElement("a");

    // Get the current library ID from the URL
    const urlParams = new URLSearchParams(window.location.search);
    const libraryId = urlParams.get("library_id");

    // Construct the category URL with library context if available
    categoryLink.href = `/category/${category.name.toLowerCase()}/`;
    if (libraryId) {
      categoryLink.href += `?library_id=${libraryId}`;
    }

    categoryLink.style.textDecoration = "none";

    const categoryDiv = document.createElement("div");
    categoryDiv.className = "category";

    const img = document.createElement("img");
    // use the image from the API if available, otherwise use default
    if (category.image_url) {
      img.src = category.image_url;
    } else {
      // path to default image
      img.src = "/static/picture/main_campus.png";
    }
    img.alt = category.name;
    img.className = "category-image";
    img.setAttribute("data-category", category.name);

    const span = document.createElement("span");
    span.textContent = category.name;

    categoryDiv.appendChild(img);
    categoryDiv.appendChild(span);
    categoryLink.appendChild(categoryDiv);
    categoriesContainer.appendChild(categoryLink);
  });

  // if no image is available from the API, try to load from static files
  const categoryImages = document.querySelectorAll(".category-image");
  categoryImages.forEach((img) => {
    if (img.src.includes("default_category.png")) {
      const categoryName = img.getAttribute("data-category");
      tryLoadStaticImage(img, categoryName);
    }
  });
}

function initSearch() {
  const searchInput = document.querySelector(".search-bar input");
  const searchButton = document.querySelector(".search-bar button");

  if (searchInput && searchButton) {
    searchButton.addEventListener("click", function () {
      performSearch(searchInput.value);
    });

    searchInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        performSearch(searchInput.value);
      }
    });
  }
}

function performSearch(query) {
  if (query.trim()) {
    // Get the current library ID from the URL
    const urlParams = new URLSearchParams(window.location.search);
    const libraryId = urlParams.get("library_id");

    // Construct the search URL with library context if available
    let searchUrl = `/clip-store/?search=${encodeURIComponent(query.trim())}`;
    if (libraryId) {
      searchUrl += `&library_id=${libraryId}`;
    }

    window.location.href = searchUrl;
  }
}
