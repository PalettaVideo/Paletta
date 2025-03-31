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
  let name = document.getElementById("categoryName").value.trim();
  let description = document.getElementById("categoryDescription").value.trim();
  let imagePreview = document.getElementById("imagePreview");
  const categoryStatus = document.getElementById("category-status");

  if (!name || !description || imagePreview.style.display === "none") {
    document.getElementById("errorText").innerText = "All fields are required!";
    return;
  }

  let categoryList = document.getElementById("categoryList");

  // Create category element
  let categoryItem = document.createElement("div");
  categoryItem.classList.add("category-item");

  let img = document.createElement("img");
  img.src = imagePreview.src;

  let title = document.createElement("div");
  title.classList.add("category-name");
  title.innerText = name;

  let desc = document.createElement("div");
  desc.classList.add("category-desc");
  desc.innerText = description;

  let deleteBtn = document.createElement("button");
  deleteBtn.classList.add("delete-btn");
  deleteBtn.type = "button";
  deleteBtn.innerHTML = "✖️";
  deleteBtn.onclick = function () {
    categoryList.removeChild(categoryItem);
    // Also remove from the array
    const index = categoriesArray.findIndex((cat) => cat.name === name);
    if (index > -1) {
      categoriesArray.splice(index, 1);
      document.getElementById("categories-json").value =
        JSON.stringify(categoriesArray);

      // Show/hide status message based on categories count
      if (categoriesArray.length === 0) {
        categoryStatus.classList.remove("hidden");
      }
    }
  };

  categoryItem.appendChild(img);
  categoryItem.appendChild(title);
  categoryItem.appendChild(desc);
  categoryItem.appendChild(deleteBtn);
  categoryList.appendChild(categoryItem);

  // Store the category data in the array for form submission
  const categoryData = {
    name: name,
    description: description,
    image: imagePreview.dataset.base64 || imagePreview.src, // Use the stored base64 data
  };

  // Add to array and update hidden input
  categoriesArray.push(categoryData);
  document.getElementById("categories-json").value =
    JSON.stringify(categoriesArray);

  // Hide status message once we have categories
  categoryStatus.classList.add("hidden");

  // Debug output to verify data is being stored correctly
  console.log("Categories array:", categoriesArray);
  console.log(
    "Hidden input value:",
    document.getElementById("categories-json").value
  );

  // Close the modal
  closeCategoryModal();
};
