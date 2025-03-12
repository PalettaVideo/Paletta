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

  // initialize search functionality
  initSearch();
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
  fetch("/api/videos/categories/", {
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
      }
    })
    .catch((error) => {
      console.error("Error fetching categories:", error);
    });
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
    categoryLink.href = `/category/${category.name.toLowerCase()}/`;
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
    window.location.href = `/clip-store/?search=${encodeURIComponent(
      query.trim()
    )}`;
  }
}
