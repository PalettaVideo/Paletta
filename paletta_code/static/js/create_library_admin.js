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

  categoryImageInput.addEventListener("change", function (event) {
    let file = event.target.files[0];
    if (file) {
      let reader = new FileReader();
      reader.onload = function (e) {
        categoryImagePreview.src = e.target.result;
        categoryImagePreview.style.display = "block";
      };
      reader.readAsDataURL(file);
    }
  });

  // Form submission handling
  const libraryForm = document.getElementById("library-form");
  if (libraryForm) {
    libraryForm.addEventListener("submit", function (event) {
      document.getElementById("categories-json").value =
        JSON.stringify(categoriesArray);
    });
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
    image: imagePreview.src, // Base64 of the image
  };
  categoriesArray.push(categoryData);
  document.getElementById("categories-json").value =
    JSON.stringify(categoriesArray);

  // Close the modal
  closeCategoryModal();
};
