document.addEventListener("DOMContentLoaded", function () {
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
      console.log(`Updated ${fieldId}:`, field.value);
      button.textContent = "Edit";
    }
  };

  // Category management
  let editingCategory = null;

  window.openCategoryModal = function () {
    document.getElementById("categoryModalTitle").innerText = "Add a Category";
    document.getElementById("categoryName").value = "";
    document.getElementById("categoryDescription").value = "";
    document.getElementById("imagePreview").src = "";
    document.getElementById("imagePreview").style.display = "none";
    document.getElementById("saveCategoryBtn").innerText = "Add";
    editingCategory = null;

    document.getElementById("categoryModal").style.display = "block";
  };

  window.closeCategoryModal = function () {
    document.getElementById("categoryModal").style.display = "none";
  };

  window.editCategoryModal = function (event, categoryItem) {
    if (event.target.classList.contains("delete-btn")) {
      return;
    }

    editingCategory = categoryItem;

    document.getElementById("categoryModalTitle").innerText = "Edit Category";
    document.getElementById("categoryName").value =
      categoryItem.querySelector(".category-name").innerText;
    document.getElementById("categoryDescription").value =
      categoryItem.querySelector(".category-desc").innerText;

    let img = categoryItem.querySelector("img");
    if (img) {
      document.getElementById("imagePreview").src = img.src;
      document.getElementById("imagePreview").style.display = "block";
    }

    document.getElementById("saveCategoryBtn").innerText = "Save";
    document.getElementById("categoryModal").style.display = "block";
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
    let name = document.getElementById("categoryName").value.trim();
    let description = document
      .getElementById("categoryDescription")
      .value.trim();
    let imagePreview = document.getElementById("imagePreview");

    if (!name || !description || imagePreview.style.display === "none") {
      document.getElementById("errorText").innerText =
        "All fields are required!";
      return;
    }

    if (editingCategory) {
      editingCategory.querySelector(".category-name").innerText = name;
      editingCategory.querySelector(".category-desc").innerText = description;
      if (imagePreview.src) {
        editingCategory.querySelector("img").src = imagePreview.src;
      }
    } else {
      let categoryList = document.getElementById("categoryList");
      let categoryItem = document.createElement("div");
      categoryItem.classList.add("category-item");
      categoryItem.setAttribute("data-id", "new_" + Date.now()); // Temporary ID for new categories
      categoryItem.onclick = function (event) {
        editCategoryModal(event, categoryItem);
      };

      let img = document.createElement("img");
      img.src = imagePreview.src;

      let title = document.createElement("div");
      title.classList.add("category-name");
      title.innerText = name;

      let desc = document.createElement("div");
      desc.classList.add("category-desc");
      desc.innerText = description;
      desc.style.display = "none";

      let deleteBtn = document.createElement("button");
      deleteBtn.classList.add("delete-btn");
      deleteBtn.innerHTML = "✖️";
      deleteBtn.onclick = function (event) {
        event.stopPropagation();
        categoryList.removeChild(categoryItem);
        updateCategoriesData();
        checkCategoriesEmpty();
      };

      categoryItem.appendChild(img);
      categoryItem.appendChild(title);
      categoryItem.appendChild(desc);
      categoryItem.appendChild(deleteBtn);
      categoryList.appendChild(categoryItem);

      // Hide the "no categories" message when adding a category
      document.getElementById("no-categories-message").style.display = "none";
    }

    closeCategoryModal();
    updateCategoriesData();
  };

  // Check if categories are empty and show/hide the message
  window.checkCategoriesEmpty = function () {
    const categoryItems = document.querySelectorAll(
      "#categoryList .category-item"
    );
    const noCategoriesMessage = document.getElementById(
      "no-categories-message"
    );

    if (categoryItems.length === 0) {
      noCategoriesMessage.style.display = "block";
    } else {
      noCategoriesMessage.style.display = "none";
    }
  };

  window.openContributorModal = function () {
    document.getElementById("contributorModal").style.display = "block";
    document.getElementById("modalOverlay").style.display = "block";
  };

  window.closeContributorModal = function () {
    document.getElementById("contributorModal").style.display = "none";
    document.getElementById("modalOverlay").style.display = "none";
  };

  window.addContributor = function () {
    let name = document.getElementById("contributorName").value;
    let email = document.getElementById("contributorEmail").value;
    if (!name || !email) {
      alert("Please fill in all fields");
      return;
    }

    let contributorList = document.getElementById("contributorList");
    let contributorItem = document.createElement("div");
    contributorItem.classList.add("contributor-item");
    contributorItem.setAttribute("data-id", "new_" + Date.now()); // Temporary ID for new contributors
    contributorItem.innerHTML = `
            <span>Name: ${name} | Email: ${email}</span>
            <button class="delete-btn" onclick="this.parentElement.remove(); updateContributorsData();">Remove</button>
        `;
    contributorList.appendChild(contributorItem);

    document.getElementById("contributorName").value = "";
    document.getElementById("contributorEmail").value = "";
    closeContributorModal();
    updateContributorsData();
  };

  // Collect form data for submission
  function updateCategoriesData() {
    const categoryItems = document.querySelectorAll(
      "#categoryList .category-item"
    );
    const categories = Array.from(categoryItems).map((item) => {
      return {
        id: item.dataset.id,
        name: item.querySelector(".category-name").innerText,
        description: item.querySelector(".category-desc").innerText,
        image: item.querySelector("img").src,
      };
    });

    document.getElementById("categoriesData").value =
      JSON.stringify(categories);
  }

  function updateContributorsData() {
    const contributorItems = document.querySelectorAll(
      "#contributorList .contributor-item"
    );
    const contributors = Array.from(contributorItems).map((item) => {
      const text = item.querySelector("span").innerText;
      const name = text.split("|")[0].replace("Name:", "").trim();
      const email = text.split("|")[1].replace("Email:", "").trim();

      return {
        id: item.dataset.id,
        name: name,
        email: email,
      };
    });

    document.getElementById("contributorsData").value =
      JSON.stringify(contributors);
  }

  // Initialize data collections
  updateCategoriesData();
  updateContributorsData();

  // Handle form submission
  const form = document.getElementById("editLibraryForm");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();

      try {
        // Update hidden inputs with current data
        updateCategoriesData();
        updateContributorsData();

        // Submit form data using AJAX
        const formData = new FormData(form);

        fetch(form.action || window.location.href, {
          method: "POST",
          body: formData,
          headers: {
            "X-CSRFToken": csrftoken,
            "X-Requested-With": "XMLHttpRequest",
          },
        }).then((response) => {
            console.log("Response status:", response.status);
            if (!response.ok) {
              throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
          })
          .then((data) => {
            console.log("Response data:", data);

            // Show success message
            if (data.status === "success") {
              alert(data.message);
            } else {
              alert("Error: " + (data.message || "Unknown error occurred"));
            }

            // Always redirect regardless of status
            console.log(
              "Attempting redirect to:",
              data.redirect_url || "/libraries/manage/"
            );

            // Force redirect using a more direct approach
            setTimeout(function () {
              window.location.replace(
                data.redirect_url || "/libraries/manage/"
              );
            }, 500);
          })
          .catch((error) => {
            console.error("Error:", error);
            alert(
              "An error occurred while saving changes. Redirecting to library management page."
            );

            // Force redirect after error using the same approach
            setTimeout(function () {
              window.location.replace("/libraries/manage/");
            }, 500);
          });
      } catch (error) {
        console.error("Form processing error:", error);
        alert(
          "An unexpected error occurred while processing the form. Redirecting to library management page."
        );

        // Force redirect after error using the same approach
        setTimeout(function () {
          window.location.replace("/libraries/manage/");
        }, 500);
      }
    });
  }
});
