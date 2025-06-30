document.addEventListener("DOMContentLoaded", function () {
  console.log("Manage libraries page loaded");
  console.log("Checking for required elements...");

  // Check if required elements exist
  const confirmModal = document.getElementById("confirmModal");
  const confirmBtn = document.getElementById("confirmBtn");
  const categoriesModal = document.getElementById("categoriesModal");

  console.log("confirmModal:", confirmModal ? "found" : "NOT FOUND");
  console.log("confirmBtn:", confirmBtn ? "found" : "NOT FOUND");
  console.log("categoriesModal:", categoriesModal ? "found" : "NOT FOUND");

  // Get CSRF token for AJAX requests
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

  const csrftoken = getCookie("csrftoken");
  console.log("CSRF token:", csrftoken ? "found" : "NOT FOUND");

  // Global variables for confirmation modal
  let pendingAction = null;
  let pendingActionData = null;

  // Library action functions
  window.editLibrary = function (libraryId) {
    window.location.href = `/libraries/edit/?library_id=${libraryId}`;
  };

  window.deleteLibrary = function (libraryId, libraryName) {
    showConfirmModal(
      "Delete Library",
      `Are you sure you want to delete "${libraryName}"? This action cannot be undone.`,
      () => executeLibraryAction(libraryId, "delete")
    );
  };

  // Category management functions
  window.manageCategoriesModal = function (libraryId, libraryName) {
    const modal = document.getElementById("categoriesModal");
    const categoriesContent = document.getElementById("categories-content");

    // Update modal title
    modal.querySelector(
      ".modal-header h3"
    ).textContent = `Manage Categories - ${libraryName}`;

    // Show modal
    modal.style.display = "block";

    // Load current categories
    loadLibraryCategories(libraryId);

    // Load available subject areas
    loadAvailableSubjectAreas(libraryId);
  };

  window.closeCategoriesModal = function () {
    document.getElementById("categoriesModal").style.display = "none";
  };

  window.addSelectedCategories = function () {
    const selectedAreas = Array.from(
      document.querySelectorAll("#available-subject-areas input:checked")
    );
    if (selectedAreas.length === 0) {
      alert("Please select at least one subject area to add.");
      return;
    }

    const libraryId =
      document.getElementById("categoriesModal").dataset.libraryId;
    const categoriesData = selectedAreas.map((checkbox) => ({
      subject_area: checkbox.value,
      description: `Custom ${checkbox.nextElementSibling.textContent} category`,
    }));

    addCategoriesToLibrary(libraryId, categoriesData);
  };

  // Add custom category function
  window.addCustomCategory = function () {
    const customNameInput = document.getElementById("custom-category-name");
    const customName = customNameInput.value.trim();

    if (!customName) {
      alert("Please enter a custom category name.");
      customNameInput.focus();
      return;
    }

    if (customName.length > 100) {
      alert("Category name must be 100 characters or less.");
      customNameInput.focus();
      return;
    }

    const libraryId =
      document.getElementById("categoriesModal").dataset.libraryId;

    const categoriesData = [
      {
        subject_area: "custom",
        custom_name: customName,
        description: `Custom category: ${customName}`,
      },
    ];

    // Clear the input after adding
    customNameInput.value = "";

    addCategoriesToLibrary(libraryId, categoriesData);
  };

  // Execute library actions
  function executeLibraryAction(libraryId, action) {
    let url;
    let method = "POST";

    switch (action) {
      case "delete":
        url = `/api/libraries/libraries/${libraryId}/`;
        method = "DELETE";
        break;
      default:
        console.error("Unknown action:", action);
        return;
    }

    fetch(url, {
      method: method,
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        // Handle both old and new response formats
        const isSuccess = data.status === "success" || data.success === true;
        const message =
          data.message ||
          (isSuccess
            ? "Action completed successfully"
            : "Unknown error occurred");

        if (isSuccess) {
          alert(message);
          location.reload(); // Refresh the page to show updated status
        } else {
          alert("Error: " + message);
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("An error occurred while performing the action");
      });
  }

  // Load library categories
  function loadLibraryCategories(libraryId) {
    const categoriesContent = document.getElementById("categories-content");
    categoriesContent.innerHTML = "<p>Loading categories...</p>";

    // Store library ID for later use
    document.getElementById("categoriesModal").dataset.libraryId = libraryId;

    fetch(`/api/api/categories/?library=${libraryId}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.length === 0) {
          categoriesContent.innerHTML =
            "<p>No categories found for this library.</p>";
          return;
        }

        let html =
          "<h4>Current Categories</h4><div class='current-categories-list'>";
        data.forEach((category) => {
          const isPrivate =
            category.subject_area === "private" || category.code === "private";
          const removeButton = isPrivate
            ? `<span class="category-protected"><i class="fas fa-lock"></i> Protected</span>`
            : `<button type='button' class='btn btn-sm btn-danger' onclick='removeCategory("${category.id}", "${category.display_name}")'>
              <i class='fas fa-trash'></i> Remove
            </button>`;

          html += `
            <div class='category-item ${isPrivate ? "private-category" : ""}'>
              <span class='category-name'>${category.display_name}</span>
              ${removeButton}
            </div>
          `;
        });
        html += "</div>";
        categoriesContent.innerHTML = html;
      })
      .catch((error) => {
        console.error("Error loading categories:", error);
        categoriesContent.innerHTML =
          "<p>Error loading categories. Please try again.</p>";
      });
  }

  // Load available subject areas
  function loadAvailableSubjectAreas(libraryId) {
    const container = document.getElementById("available-subject-areas");

    // Define all possible subject areas
    const allSubjectAreas = [
      { value: "engineering_sciences", label: "Engineering Sciences" },
      {
        value: "mathematical_physical_sciences",
        label: "Mathematical & Physical Sciences",
      },
      { value: "medical_sciences", label: "Medical Sciences" },
      { value: "life_sciences", label: "Life Sciences" },
      { value: "brain_sciences", label: "Brain Sciences" },
      { value: "built_environment", label: "Built Environment" },
      { value: "population_health", label: "Population Health" },
      { value: "arts_humanities", label: "Arts & Humanities" },
      {
        value: "social_historical_sciences",
        label: "Social & Historical Sciences",
      },
      { value: "education", label: "Education" },
      { value: "fine_art", label: "Fine Art" },
      { value: "law", label: "Law" },
      { value: "business", label: "Business" },
    ];

    // Get current categories to exclude them
    fetch(`/api/api/categories/?library=${libraryId}`)
      .then((response) => response.json())
      .then((currentCategories) => {
        const existingAreas = currentCategories.map(
          (cat) => cat.subject_area || cat.category_type
        );
        const availableAreas = allSubjectAreas.filter(
          (area) => !existingAreas.includes(area.value)
        );

        if (availableAreas.length === 0) {
          container.innerHTML =
            "<p>All subject areas are already added to this library.</p>";
          return;
        }

        let html = "";
        availableAreas.forEach((area) => {
          html += `
            <div class='subject-area-item'>
              <input type='checkbox' id='add_${area.value}' value='${area.value}'>
              <label for='add_${area.value}'>${area.label}</label>
            </div>
          `;
        });
        container.innerHTML = html;
      })
      .catch((error) => {
        console.error("Error loading available subject areas:", error);
        container.innerHTML = "<p>Error loading available options.</p>";
      });
  }

  // Add categories to library
  function addCategoriesToLibrary(libraryId, categoriesData) {
    fetch(`/api/libraries/libraries/${libraryId}/add_categories/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ categories: categoriesData }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "success") {
          alert("Categories added successfully");
          loadLibraryCategories(libraryId);
          loadAvailableSubjectAreas(libraryId);

          // Clear any checked checkboxes
          const checkboxes = document.querySelectorAll(
            "#available-subject-areas input:checked"
          );
          checkboxes.forEach((checkbox) => (checkbox.checked = false));
        } else {
          alert("Error: " + (data.message || "Failed to add categories"));
        }
      })
      .catch((error) => {
        console.error("Error adding categories:", error);
        alert("An error occurred while adding categories");
      });
  }

  // Remove category
  window.removeCategory = function (categoryId, categoryName) {
    showConfirmModal(
      "Remove Category",
      `Are you sure you want to remove "${categoryName}"? This will affect all videos in this category.`,
      () => {
        fetch(`/api/videos/categories/${categoryId}/`, {
          method: "DELETE",
          headers: {
            "X-CSRFToken": csrftoken,
          },
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.status === "success") {
              alert("Category removed successfully");
              const libraryId =
                document.getElementById("categoriesModal").dataset.libraryId;
              loadLibraryCategories(libraryId);
              loadAvailableSubjectAreas(libraryId);
            } else {
              alert("Error: " + (data.message || "Failed to remove category"));
            }
          })
          .catch((error) => {
            console.error("Error removing category:", error);
            alert("An error occurred while removing the category");
          });
      }
    );
  };

  // Confirmation modal functions
  function showConfirmModal(title, message, confirmCallback) {
    const modal = document.getElementById("confirmModal");
    const titleElement = document.getElementById("confirmTitle");
    const messageElement = document.getElementById("confirmMessage");
    const confirmBtn = document.getElementById("confirmBtn");

    if (!confirmBtn) {
      console.error("Confirm button not found");
      return;
    }

    titleElement.textContent = title;
    messageElement.textContent = message;

    // Store the callback for later execution
    pendingAction = confirmCallback;

    modal.style.display = "block";
  }

  window.closeConfirmModal = function () {
    document.getElementById("confirmModal").style.display = "none";
    pendingAction = null;
  };

  window.executeConfirmedAction = function () {
    if (pendingAction) {
      pendingAction();
      closeConfirmModal();
    }
  };

  // Close modals when clicking outside
  window.addEventListener("click", function (event) {
    const categoriesModal = document.getElementById("categoriesModal");
    const confirmModal = document.getElementById("confirmModal");

    if (event.target === categoriesModal) {
      closeCategoriesModal();
    }
    if (event.target === confirmModal) {
      closeConfirmModal();
    }
  });
});
