document.addEventListener("DOMContentLoaded", () => {
  setupSearch();
  setupDeleteButtons();
});

/**
 * Set up the search functionality for the video history
 */
function setupSearch() {
  const searchInput = document.querySelector(".search-input");

  if (!searchInput) return;

  searchInput.addEventListener("input", (e) => {
    const searchTerm = e.target.value.toLowerCase().trim();
    const historyItems = document.querySelectorAll(".history-item");

    historyItems.forEach((item) => {
      const title = item.querySelector("h3").textContent.toLowerCase();
      const isVisible = title.includes(searchTerm);

      item.style.display = isVisible ? "flex" : "none";
    });

    // Show or hide the no-results message
    const noResults = document.querySelector(".no-results");
    if (noResults) {
      const visibleItems = document.querySelectorAll(
        '.history-item[style="display: flex"]'
      ).length;
      noResults.style.display = visibleItems === 0 ? "block" : "none";
    }
  });
}

/**
 * Helper function to get CSRF cookie
 */
function getCookie(name) {
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
 * Format file size into human-readable format
 * (Utility function that can be used if needed)
 */
function formatSize(bytes) {
  if (bytes === 0) return "0 B";

  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));

  return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + " " + units[i];
}

/**
 * Format date for more readable display
 * (Utility function that can be used if needed)
 */
function formatDate(isoString) {
  const date = new Date(isoString);
  const options = {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  };

  return date.toLocaleDateString(undefined, options);
}
