document.addEventListener("DOMContentLoaded", function () {
  // Get CURRENT_LIBRARY_ID from a data attribute on the form element
  const editLibraryForm = document.getElementById("editLibraryForm");
  const CURRENT_LIBRARY_ID = editLibraryForm
    ? parseInt(editLibraryForm.dataset.libraryId)
    : null;

  // Set up CSRF token for AJAX requests
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

  // Add CSRF token to all AJAX requests
  function csrfSafeMethod(method) {
    return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method);
  }

  // Set up AJAX to include CSRF token
  if (window.XMLHttpRequest) {
    const oldSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function (data) {
      if (!csrfSafeMethod(this._method) && !this._headers.has("X-CSRFToken")) {
        this.setRequestHeader("X-CSRFToken", csrftoken);
      }
      oldSend.apply(this, arguments);
    };
  }

  // Theme Color Picker
  let colorInput = document.getElementById("themeColor");
  colorInput.addEventListener("change", function () {
    // Just update the color preview - don't change the body background
    document.getElementById("colorPreview") &&
      (document.getElementById("colorPreview").style.backgroundColor =
        colorInput.value);
  });

  // Logo Upload
  let logoUpload = document.getElementById("logoUpload");
  let libraryLogo = document.getElementById("libraryLogo");

  document.querySelector(".change-btn").addEventListener("click", function () {
    logoUpload.click();
  });

  logoUpload.addEventListener("change", function (event) {
    let file = event.target.files[0];
    if (!file) return;

    let reader = new FileReader();
    reader.onload = (e) => {
      libraryLogo.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });

  // Toggle edit mode for text fields
  window.toggleEdit = function (fieldId, button) {
    let field = document.getElementById(fieldId);

    if (field.hasAttribute("readonly")) {
      field.removeAttribute("readonly");
      field.focus();
      button.textContent = "Save";
    } else {
      field.setAttribute("readonly", true);
      button.textContent = "Edit";
    }
  };

  // Category management
  let currentEditingCategory = null;

  // Check if category list is empty and show/hide message
  window.checkCategoriesEmpty = function () {
    const categoryList = document.getElementById("categoryList");
    const categoryItems = categoryList.querySelectorAll(".category-item");
    const noMessage = document.getElementById("no-categories-message");

    if (categoryItems.length === 0) {
      noMessage.style.display = "block";
    } else {
      noMessage.style.display = "none";
    }
  };

  window.openCategoryModal = function () {
    document.getElementById("categoryModalTitle").innerText = "Add a Category";
    document.getElementById("categoryName").value = "";
    document.getElementById("categoryDescription").value = "";
    document.getElementById("imagePreview").src = "";
    document.getElementById("imagePreview").style.display = "none";
    document.getElementById("saveCategoryBtn").innerText = "Add";
    document.getElementById("categoryModal").style.display = "block";
    document.getElementById("modalOverlay").style.display = "block";
    currentEditingCategory = null;
  };

  window.closeCategoryModal = function () {
    document.getElementById("categoryModal").style.display = "none";
    document.getElementById("modalOverlay").style.display = "none";
    document.getElementById("errorText").textContent = "";
  };

  window.editCategoryModal = function (event, categoryElement) {
    if (event.target.classList.contains("delete-btn")) {
      return;
    }

    event.stopPropagation();
    const categoryId = categoryElement.dataset.id;
    const categoryName =
      categoryElement.querySelector(".category-name").textContent;
    const categoryDesc =
      categoryElement.querySelector(".category-desc").textContent;
    const categoryImage = categoryElement.querySelector("img").src;

    document.getElementById("categoryModalTitle").textContent = "Edit Category";
    document.getElementById("categoryName").value = categoryName;
    document.getElementById("categoryDescription").value = categoryDesc;

    const imagePreview = document.getElementById("imagePreview");
    imagePreview.src = categoryImage;
    imagePreview.style.display = "block";

    document.getElementById("saveCategoryBtn").textContent = "Save Changes";
    document.getElementById("categoryModal").style.display = "block";
    document.getElementById("modalOverlay").style.display = "block";

    currentEditingCategory = {
      element: categoryElement,
      id: categoryId,
    };
  };

  document
    .getElementById("categoryImage")
    .addEventListener("change", function (event) {
      let file = event.target.files[0];
      if (file) {
        let reader = new FileReader();
        reader.onload = function (e) {
          document.getElementById("imagePreview").src = e.target.result;
          document.getElementById("imagePreview").style.display = "block";
        };
        reader.readAsDataURL(file);
      }
    });

  window.saveCategory = function () {
    const name = document.getElementById("categoryName").value.trim();
    const description = document
      .getElementById("categoryDescription")
      .value.trim();
    const imageInput = document.getElementById("categoryImage");
    const errorText = document.getElementById("errorText");

    // Validate input
    if (!name) {
      errorText.textContent = "Category name is required";
      return;
    }

    // Process image
    let imagePromise = Promise.resolve(null);
    if (imageInput.files && imageInput.files[0]) {
      imagePromise = new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = function (e) {
          resolve(e.target.result);
        };
        reader.readAsDataURL(imageInput.files[0]);
      });
    }

    // Once we have the image (if any), create or update the category
    imagePromise.then((imageData) => {
      if (currentEditingCategory) {
        // Update existing category
        updateCategory(currentEditingCategory, name, description, imageData);
      } else {
        // Create new category
        createCategory(name, description, imageData);
      }

      closeCategoryModal();
    });
  };

  function createCategory(name, description, imageData) {
    // Create category element
    const categoryList = document.getElementById("categoryList");
    const newCategory = document.createElement("div");
    newCategory.className = "category-item";
    newCategory.setAttribute("onclick", "editCategoryModal(event, this)");

    // Generate a temporary ID that'll be replaced with the real one after saving
    const tempId = "temp_" + Date.now();
    newCategory.dataset.id = tempId;

    // Create category content
    let categoryHTML = `
        <div class="category-name">${name}</div>
        <div class="category-desc" style="display: none;">${description}</div>
        <button type="button" class="delete-btn" onclick="event.stopPropagation(); this.parentElement.remove(); checkCategoriesEmpty();">✖️</button>
    `;

    // Add image if provided
    if (imageData) {
      categoryHTML = `<img src="${imageData}" alt="${name}">` + categoryHTML;
    } else {
      // Use default image path - this will be set by Django template in the HTML
      const defaultImage = document.querySelector("#categoryList img")
        ? document.querySelector("#categoryList img").src
        : "/static/picture/All.png";
      categoryHTML = `<img src="${defaultImage}" alt="${name}">` + categoryHTML;
    }

    newCategory.innerHTML = categoryHTML;
    categoryList.appendChild(newCategory);
    checkCategoriesEmpty();

    // Add to the form data that will be submitted
    appendCategoryToFormData({
      id: tempId,
      name: name,
      description: description,
      image: imageData,
      library: CURRENT_LIBRARY_ID,
    });
  }

  function updateCategory(categoryData, name, description, imageData) {
    const element = categoryData.element;

    // Update name and description
    element.querySelector(".category-name").textContent = name;
    element.querySelector(".category-desc").textContent = description;

    // Update image if new one provided
    if (imageData) {
      element.querySelector("img").src = imageData;
    }

    // Update form data
    appendCategoryToFormData({
      id: categoryData.id,
      name: name,
      description: description,
      image: imageData ? imageData : null,
      library: CURRENT_LIBRARY_ID,
    });
  }

  function appendCategoryToFormData(category) {
    const categoriesInput = document.getElementById("categoriesData");
    let categories = [];

    // Parse existing categories if any
    if (categoriesInput.value) {
      categories = JSON.parse(categoriesInput.value);
    }

    // Check if category exists (for update)
    const existingIndex = categories.findIndex((c) => c.id === category.id);
    if (existingIndex >= 0) {
      categories[existingIndex] = category;
    } else {
      categories.push(category);
    }

    // Save back to input
    categoriesInput.value = JSON.stringify(categories);
  }

  // Helper function to validate email
  function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }

  // Collect form data for submission
  function updateCategoriesData() {
    const categoryItems = document.querySelectorAll(
      "#categoryList .category-item"
    );

    const categories = Array.from(categoryItems).map((item) => {
      const id = item.dataset.id;
      const name = item.querySelector(".category-name").textContent;
      const description = item.querySelector(".category-desc").textContent;
      const imageSrc = item.querySelector("img").src;

      return {
        id: id,
        name: name,
        description: description,
        image: imageSrc.includes("data:image") ? imageSrc : null,
        library: CURRENT_LIBRARY_ID,
      };
    });

    document.getElementById("categoriesData").value =
      JSON.stringify(categories);
  }

  // Initialize data collections
  updateCategoriesData();

  // When the form is submitted, collect all category data
  if (editLibraryForm) {
    editLibraryForm.addEventListener("submit", function (e) {
      // Ensure categories data is collected
      updateCategoriesData();
    });
  }

  // Handle form submission
  const form = document.getElementById("editLibraryForm");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();

      try {
        // Update hidden inputs with current data
        updateCategoriesData();

        // Submit form data using AJAX
        const formData = new FormData(form);

        fetch(form.action || window.location.href, {
          method: "POST",
          body: formData,
          headers: {
            "X-CSRFToken": csrftoken,
            "X-Requested-With": "XMLHttpRequest",
          },
        })
          .then((response) => {
            if (!response.ok) {
              throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
          })
          .then((data) => { 
            // Show success message
            if (data.status === "success") {
              alert(data.message);
            } else {
              alert("Error: " + (data.message || "Unknown error occurred"));
            }

            setTimeout(function () {
              window.location.replace(
                data.redirect_url || "/libraries/manage/"
              );
            }, 500);
          })
          .catch(() => {
            alert(
              "An error occurred while saving changes. Redirecting to library management page."
            );
            setTimeout(function () {
              window.location.replace("/libraries/manage/");
            }, 500);
          });
      } catch {
        alert(
          "An unexpected error occurred while processing the form. Redirecting to library management page."
        );
        setTimeout(function () {
          window.location.replace("/libraries/manage/");
        }, 500);
      }
    });
  }

  // Initialize the page
  window.checkCategoriesEmpty();
});
