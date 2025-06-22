document.addEventListener("DOMContentLoaded", function () {
  // Initialize the popup menu for the user center
  initPopupMenu();

  // Initialize header search functionality
  initHeaderSearch();
});

function initPopupMenu() {
  const centerButton = document.getElementById("centerButton");
  const popupMenu = document.getElementById("popupMenu");

  if (!centerButton || !popupMenu) {
    console.error("Header elements not found:", {
      centerButton: !!centerButton,
      popupMenu: !!popupMenu,
    });
    return;
  }


  centerButton.addEventListener("click", function (event) {
    event.stopPropagation();
    popupMenu.style.display =
      popupMenu.style.display === "block" ? "none" : "block";
  });

  // Close the popup when clicking outside
  document.addEventListener("click", function () {
    popupMenu.style.display = "none";
  });

  popupMenu.addEventListener("click", function (event) {
    event.stopPropagation();
  });
}

function initHeaderSearch() {
  const headerSearchInput = document.getElementById("header-search-input");
  const headerSearchButton = document.getElementById("header-search-button");

  if (headerSearchInput && headerSearchButton) {
    // Perform search on button click
    headerSearchButton.addEventListener("click", function () {
      performHeaderSearch(headerSearchInput.value);
    });

    // Perform search on Enter key
    headerSearchInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        performHeaderSearch(headerSearchInput.value);
      }
    });
  }
}

function performHeaderSearch(query) {
  if (query.trim()) {
    // Check if we're using the new URL structure by looking for a library slug
    const librarySlugMatch =
      window.location.pathname.match(/\/library\/([^/]+)\//);

    if (librarySlugMatch) {
      // New URL structure with library slug
      const librarySlug = librarySlugMatch[1];
      window.location.href = `/library/${librarySlug}/category/clip-store/?search=${encodeURIComponent(
        query.trim()
      )}`;
    } else {
      // Try to get the library context from other potential URL patterns
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
        // Default to main Paletta library if no specific library context is found
        window.location.href = `/home/?search=${encodeURIComponent(
          query.trim()
        )}`;
      }
    }
  }
}
