document.addEventListener("DOMContentLoaded", () => {
  setupSearch();
  setupDeleteFunctionality();
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

/**
 * Set up delete functionality for videos
 */
function setupDeleteFunctionality() {
  // Handle edit video buttons
  const editButtons = document.querySelectorAll(".video-actions .edit");
  editButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      e.preventDefault();
      const videoId = this.getAttribute("data-id");
      window.location.href = `/videos/edit/${videoId}/`;
    });
  });

  // Handle delete video buttons
  const deleteButtons = document.querySelectorAll(".video-actions .delete");
  deleteButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      e.preventDefault();
      const videoId = this.getAttribute("data-id");
      const videoTitle = this.getAttribute("data-title");

      // Show delete confirmation modal
      const modal = document.getElementById("deleteModal");
      const overlay = document.getElementById("modalOverlay");
      const videoTitleElement = document.getElementById("videoTitle");
      const confirmDeleteBtn = document.getElementById("confirmDelete");

      videoTitleElement.textContent = videoTitle;
      confirmDeleteBtn.setAttribute("data-id", videoId);

      modal.style.display = "block";
      overlay.style.display = "block";
    });
  });

  // Handle confirm delete button
  const confirmDeleteBtn = document.getElementById("confirmDelete");
  if (confirmDeleteBtn) {
    confirmDeleteBtn.addEventListener("click", function () {
      const videoId = this.getAttribute("data-id");
      const csrfToken = document.querySelector(
        "[name=csrfmiddlewaretoken]"
      ).value;

      // Use the standard video delete URL since videos always have a library
      const deleteUrl = `/videos/delete/${videoId}/`;

      console.log("Attempting to delete video:", videoId, "at URL:", deleteUrl);

      // Send AJAX request to delete the video
      fetch(deleteUrl, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
        },
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
          return response.json();
        })
        .then((data) => {
          if (data.success) {
            // Remove the video item from the DOM
            const videoElement = document.querySelector(
              `.history-item[data-id="${videoId}"]`
            );
            if (videoElement) {
              videoElement.remove();

              // Check if there are no more videos
              const remainingVideos =
                document.querySelectorAll(".history-item");
              if (remainingVideos.length === 0) {
                const uploadHistoryContainer = document.querySelector(
                  ".upload-history-container"
                );
                const noVideosElement = document.createElement("div");
                noVideosElement.className = "no-videos";
                noVideosElement.innerHTML = `
                                <p>You haven't uploaded any videos yet.</p>
                                <a href="/videos/upload/" class="button">Upload Your First Video</a>
                            `;
                uploadHistoryContainer.replaceWith(noVideosElement);
              }
            }

            // Show success message
            showToast("Video successfully deleted");
          } else {
            // Show error message
            showToast(`Error: ${data.message || "Failed to delete video"}`);
          }

          // Close the modal
          closeDeleteModal();
        })
        .catch((error) => {
          console.error("Error:", error);
          let errorMessage = "An error occurred while deleting the video";

          // Try to provide more specific error messages
          if (error.message.includes("404")) {
            errorMessage = "Video not found or delete endpoint not available";
          } else if (error.message.includes("403")) {
            errorMessage =
              "Permission denied - only the video uploader can delete this video";
          } else if (error.message.includes("JSON")) {
            errorMessage = "Server returned an invalid response";
          }

          showToast(errorMessage);
          closeDeleteModal();
        });
    });
  }

  // Handle close modal button
  const closeModalBtn = document.querySelector(".delete-modal .close");
  if (closeModalBtn) {
    closeModalBtn.addEventListener("click", closeDeleteModal);
  }

  // Close modal when clicking outside
  const modalOverlay = document.getElementById("modalOverlay");
  if (modalOverlay) {
    modalOverlay.addEventListener("click", closeDeleteModal);
  }

  // Toast notification function
  function showToast(message) {
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    document.body.appendChild(toast);

    // Show toast
    setTimeout(() => {
      toast.classList.add("show");

      // Hide and remove toast after 3 seconds
      setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => {
          toast.remove();
        }, 300);
      }, 3000);
    }, 100);
  }

  // Close delete modal function
  function closeDeleteModal() {
    const modal = document.getElementById("deleteModal");
    const overlay = document.getElementById("modalOverlay");

    if (modal) modal.style.display = "none";
    if (overlay) overlay.style.display = "none";
  }
}
