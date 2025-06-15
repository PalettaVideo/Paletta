document.addEventListener("DOMContentLoaded", function () {
  // Clear any stale library cache before initializing the page
  clearStaleLibraryCache();

  // Add debug logging for library context
  const currentLibrarySlug = getCurrentLibrarySlug();
  const currentLibraryName =
    document.querySelector('meta[name="current-library-name"]')?.content ||
    "Unknown";
  const categoriesCount =
    document.querySelector('meta[name="categories-count"]')?.content || "0";

  console.log(`[Homepage Debug] Library context initialized:`);
  console.log(
    `[Homepage Debug] - Current library: ${currentLibraryName} (slug: ${currentLibrarySlug})`
  );
  console.log(`[Homepage Debug] - Categories count: ${categoriesCount}`);
  console.log(`[Homepage Debug] - URL: ${window.location.pathname}`);

  // initialize the popup menu for the user center
  initPopupMenu();

  // initialize search functionality
  initVideoSearch();
  initLibrarySearch();
});

// Get current library context for cache clearing
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

// Clear stale localStorage data from other libraries
function clearStaleLibraryCache() {
  const currentLibrarySlug = getCurrentLibrarySlug();
  const keysToRemove = [];

  console.log(
    `[Homepage Cache Debug] Clearing cache for library: ${currentLibrarySlug}`
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
    console.log(`[Homepage Cache Debug] Removed stale key: ${key}`);
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
        `[Homepage Cache Debug] Removed general cache key: ${key} (was: ${storedValue})`
      );
    }
  });

  // Force clear any cached library state
  if (typeof window.libraryCache !== "undefined") {
    window.libraryCache = {};
  }

  if (keysToRemove.length > 0) {
    console.log(
      `[Homepage Cache Debug] Cleared ${keysToRemove.length} stale localStorage entries for library switch`
    );
  }

  // Set current library slug to prevent future caching issues
  localStorage.setItem("lastLibrarySlug", currentLibrarySlug);
  console.log(
    `[Homepage Cache Debug] Set lastLibrarySlug to: ${currentLibrarySlug}`
  );
}

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

function initVideoSearch() {
  // Main content search for videos
  const videoSearchInput = document.getElementById("video-search-input");
  const videoSearchButton = document.getElementById("video-search-button");

  if (videoSearchInput && videoSearchButton) {
    videoSearchButton.addEventListener("click", function () {
      performVideoSearch(videoSearchInput.value);
    });

    videoSearchInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        performVideoSearch(videoSearchInput.value);
      }
    });
  }
}

function initLibrarySearch() {
  // Sidebar search for libraries
  const librarySearchInput = document.getElementById("library-search-input");
  const librarySearchButton = document.getElementById("library-search-button");
  const clearButton = document.getElementById("library-search-clear");

  if (librarySearchInput && librarySearchButton) {
    // Filter on button click
    librarySearchButton.addEventListener("click", function () {
      performLibrarySearch(librarySearchInput.value);
    });

    // Filter on Enter key
    librarySearchInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        performLibrarySearch(librarySearchInput.value);
      }
    });

    // Filter dynamically on each keystroke
    librarySearchInput.addEventListener("input", function () {
      performLibrarySearch(librarySearchInput.value);

      // Show/hide clear button based on input content
      if (clearButton) {
        clearButton.style.display = librarySearchInput.value.trim()
          ? "block"
          : "none";
      }
    });

    // Clear button functionality
    if (clearButton) {
      clearButton.addEventListener("click", function () {
        librarySearchInput.value = "";
        performLibrarySearch("");
        clearButton.style.display = "none";
        librarySearchInput.focus();
      });
    }
  }
}

function performVideoSearch(query) {
  if (query.trim()) {
    // Check if we're using the new URL structure by looking for a library slug
    const librarySlugMatch =
      window.location.pathname.match(/\/library\/([^/]+)\//);

    if (librarySlugMatch) {
      // New URL structure
      const librarySlug = librarySlugMatch[1];
      window.location.href = `/library/${librarySlug}/category/clip-store/?search=${encodeURIComponent(
        query.trim()
      )}`;
    } else {
      // Try to find library slug in the URL path
      const pathParts = window.location.pathname
        .split("/")
        .filter((part) => part);

      // Look for library slug in URL
      let librarySlug = null;
      if (
        pathParts.includes("library") &&
        pathParts.length > pathParts.indexOf("library") + 1
      ) {
        librarySlug = pathParts[pathParts.indexOf("library") + 1];
      }

      // If we have a library slug, use it
      if (librarySlug) {
        window.location.href = `/library/${librarySlug}/category/clip-store/?search=${encodeURIComponent(
          query.trim()
        )}`;
      } else {
        // Default to the home page with search parameter
        window.location.href = `/home/?search=${encodeURIComponent(
          query.trim()
        )}`;
      }
    }
  }
}

function performLibrarySearch(query) {
  // Filter libraries in the sidebar based on the search query
  const libraryButtons = document.querySelectorAll(".library-button");
  const searchTermLower = query.trim().toLowerCase();
  let matchFound = false;

  // Get the search input and button for visual feedback
  const searchInput = document.getElementById("library-search-input");
  const searchButton = document.getElementById("library-search-button");
  const clearButton = document.getElementById("library-search-clear");

  // If search is empty, show all libraries
  if (!searchTermLower) {
    libraryButtons.forEach((button) => {
      button.style.display = "block";
    });

    // Remove any "no results" message
    const tempMsg = document.querySelector(".no-search-results");
    if (tempMsg) tempMsg.remove();

    // Show the original "no libraries" message if it exists
    const noLibrariesMsg = document.querySelector(
      ".no-libraries:not(.no-search-results)"
    );
    if (noLibrariesMsg) {
      noLibrariesMsg.style.display = "block";
    }

    // Reset visual indicator
    if (searchInput) searchInput.classList.remove("active-filter");
    if (searchButton) searchButton.classList.remove("active-filter");

    // Hide clear button
    if (clearButton) clearButton.style.display = "none";

    return;
  }

  // Otherwise filter based on search term
  libraryButtons.forEach((button) => {
    const libraryName = button.querySelector("span").innerText.toLowerCase();
    if (libraryName.includes(searchTermLower)) {
      button.style.display = "block";
      matchFound = true;
    } else {
      button.style.display = "none";
    }
  });

  // Show visual indicator that filter is active
  if (searchInput) searchInput.classList.add("active-filter");
  if (searchButton) searchButton.classList.add("active-filter");

  // Show clear button
  if (clearButton) clearButton.style.display = "block";

  // Hide the original "no libraries" message during search
  const originalNoLibrariesMsg = document.querySelector(
    ".no-libraries:not(.no-search-results)"
  );
  if (originalNoLibrariesMsg) {
    originalNoLibrariesMsg.style.display = "none";
  }

  // Show/hide the "no search results" message
  let noResultsMsg = document.querySelector(".no-search-results");

  if (!matchFound && libraryButtons.length > 0) {
    // Create or update the no results message
    if (!noResultsMsg) {
      noResultsMsg = document.createElement("p");
      noResultsMsg.className = "no-libraries no-search-results";
      const container = document.getElementById("libraries-container");
      container.appendChild(noResultsMsg);
    }
    noResultsMsg.textContent = `No libraries matching "${query}"`;
    noResultsMsg.style.display = "block";
  } else if (noResultsMsg) {
    // Hide the message if we have matches
    noResultsMsg.style.display = "none";
  }
}
