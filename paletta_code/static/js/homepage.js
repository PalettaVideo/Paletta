document.addEventListener("DOMContentLoaded", function () {
  // initialize the popup menu for the user center
  initPopupMenu();

  // initialize search functionality
  initVideoSearch();
  initLibrarySearch();

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
      window.location.href = `/clip-store/?search=${encodeURIComponent(
        query.trim()
      )}&library_slug=${librarySlug}`;
    } else {
      // Legacy URL structure
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
