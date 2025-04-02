document.addEventListener("DOMContentLoaded", function () {
  // Get CSRF token for Django form submissions
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

  // Handle color picker
  let colorInput = document.getElementById("themeColor");
  let colorPreview = document.getElementById("colorPreview");

  // Set initial color preview
  colorPreview.style.background = colorInput.value || "#80B824";

  // Toggle color picker when clicking on color preview
  window.toggleColorPicker = function () {
    colorInput.click();
  };

  // Update color preview when color changes
  window.updateColor = function () {
    colorPreview.style.background = colorInput.value;
  };

  // Handle logo upload
  const fileInput = document.getElementById("file-input");
  const uploadBox = document.getElementById("upload-box");
  const previewContainer = document.getElementById("preview-container");

  uploadBox.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", handleImagePreview);

  function handleImagePreview(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      previewContainer.innerHTML = `
                <img src="${e.target.result}" alt="Logo" style="max-width: 100px; height: auto;">
                <button type="button" class="remove-btn" onclick="removePreview()">×</button>
            `;
    };
    reader.readAsDataURL(file);
  }

  // Remove logo preview
  window.removePreview = function () {
    previewContainer.innerHTML = "";
    fileInput.value = "";
  };

  // Category handling
  let categoryImageInput = document.getElementById("categoryImage");
  let categoryImagePreview = document.getElementById("imagePreview");
  let categoriesArray = [];

  // Initialize categoriesArray and make sure it's set in the form
  document.getElementById("categories-json").value =
    JSON.stringify(categoriesArray);

  categoryImageInput.addEventListener("change", function (event) {
    let file = event.target.files[0];
    if (file) {
      console.log("Category image file selected:", file.name);
      let reader = new FileReader();
      reader.onload = function (e) {
        console.log("Image loaded, setting preview");
        categoryImagePreview.src = e.target.result;
        categoryImagePreview.style.display = "block";
        // Store the base64 data for later use
        categoryImagePreview.dataset.base64 = e.target.result;
        console.log(
          "Base64 data length:",
          categoryImagePreview.dataset.base64.length
        );
      };
      reader.readAsDataURL(file);
    }
  });

  // Form submission handling
  const libraryForm = document.getElementById("library-form");
  if (libraryForm) {
    libraryForm.addEventListener("submit", async function (event) {
      event.preventDefault();

      // Update categories JSON before submission
      document.getElementById("categories-json").value =
        JSON.stringify(categoriesArray);
      console.log("Categories array at submission:", categoriesArray);
      console.log(
        "categories_json value:",
        document.getElementById("categories-json").value
      );

      // Validate form
      if (!validateForm()) {
        return;
      }

      // Create FormData object
      const formData = new FormData(libraryForm);

      // Debug form data
      console.log("Form submission data:");
      for (let pair of formData.entries()) {
        if (pair[0] === "categories_json") {
          console.log(`${pair[0]}: ${pair[1]} (length: ${pair[1].length})`);
          // Parse JSON to verify it's valid
          try {
            const parsed = JSON.parse(pair[1]);
            console.log("Parsed categories:", parsed);
          } catch (e) {
            console.error("Error parsing categories JSON:", e);
            alert(
              "There was an error with the category data. Please try again."
            );
            return;
          }
        } else {
          console.log(`${pair[0]}: ${pair[1]}`);
        }
      }

      try {
        const response = await fetch(
          libraryForm.action || window.location.href,
          {
            method: "POST",
            headers: {
              "X-CSRFToken": csrftoken,
              // Don't set Content-Type here, FormData will set it with boundary
            },
            body: formData,
          }
        );

        // Debug response
        console.log("Response status:", response.status);
        const data = await response.json();
        console.log("Response data:", data);

        if (data.status === "success") {
          // Show success message
          alert(data.message);
          // Redirect to manage libraries page
          window.location.href = data.redirect_url;
        } else {
          // Show error message
          alert("Error: " + JSON.stringify(data.message));
        }
      } catch (error) {
        console.error("Error:", error);
        alert(
          "An error occurred while creating the library. Please try again."
        );
      }
    });
  }

  function validateForm() {
    const nameField = document.getElementById("id_name");
    const descriptionField = document.getElementById("id_description");

    if (!nameField.value.trim()) {
      alert("Please enter a library name");
      nameField.focus();
      return false;
    }

    if (!descriptionField.value.trim()) {
      alert("Please enter a library description");
      descriptionField.focus();
      return false;
    }

    return true;
  }
});

// Modal functions
window.openCategoryModal = function () {
  document.getElementById("categoryModal").style.display = "block";
  document.getElementById("categoryName").value = "";
  document.getElementById("categoryDescription").value = "";
  document.getElementById("categoryImage").value = "";
  document.getElementById("imagePreview").style.display = "none";
  document.getElementById("errorText").innerText = "";
};

window.closeCategoryModal = function () {
  document.getElementById("categoryModal").style.display = "none";
};

// Add category to the list
window.addCategory = function () {
  const name = document.getElementById("categoryName").value.trim();
  const description = document
    .getElementById("categoryDescription")
    .value.trim();
  const imageInput = document.getElementById("categoryImage");
  const errorText = document.getElementById("errorText");

  // Validate
  if (!name) {
    errorText.textContent = "Category name is required";
    return;
  }

  // Create category object
  const category = {
    name: name,
    description: description,
    // The library ID will be assigned server-side during library creation
    library: null,
  };

  // Handle image if uploaded
  if (imageInput.files && imageInput.files[0]) {
    const reader = new FileReader();
    reader.onload = function (e) {
      category.image = e.target.result; // base64 encoded image
      addCategoryToList(category);
    };
    reader.readAsDataURL(imageInput.files[0]);
  } else {
    addCategoryToList(category);
  }
};

function addCategoryToList(category) {
  // Get existing categories
  const categoriesInput = document.getElementById("categories-json");
  const categories = JSON.parse(categoriesInput.value);

  // Add new category
  categories.push(category);

  // Update hidden input
  categoriesInput.value = JSON.stringify(categories);
  categoriesArray = categories; // Update the global categoriesArray

  // Update UI
  const categoryList = document.getElementById("categoryList");
  const statusMessage = document.getElementById("category-status");

  // Create category item HTML
  const categoryItem = document.createElement("div");
  categoryItem.className = "category-item";
  categoryItem.innerHTML = `
      <div class="category-info">
          <h3>${category.name}</h3>
          <p>${category.description || "No description"}</p>
      </div>
      <button type="button" class="remove-btn" onclick="removeCategory(this, '${
        category.name
      }')">Remove</button>
  `;

  // Add image preview if available
  if (category.image) {
    const imgElement = document.createElement("img");
    imgElement.src = category.image;
    imgElement.className = "category-image-preview";
    categoryItem.prepend(imgElement);
  }

  // Add to list
  categoryList.appendChild(categoryItem);

  // Hide status message if we have categories
  if (categories.length > 0) {
    statusMessage.style.display = "none";
  } else {
    statusMessage.style.display = "block";
  }

  // Close modal and reset form
  closeCategoryModal();
}

window.removeCategory = function (button, categoryName) {
  // Get the category item
  const categoryItem = button.parentNode;

  // Remove from DOM
  categoryItem.remove();

  // Remove from categories array
  const categoriesInput = document.getElementById("categories-json");
  let categories = JSON.parse(categoriesInput.value);

  categories = categories.filter((cat) => cat.name !== categoryName);
  categoriesInput.value = JSON.stringify(categories);
  categoriesArray = categories; // Update the global categoriesArray

  // Show status message if no categories
  const statusMessage = document.getElementById("category-status");
  if (categories.length === 0) {
    statusMessage.style.display = "block";
  }
};
