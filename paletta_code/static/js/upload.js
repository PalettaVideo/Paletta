document.addEventListener("DOMContentLoaded", function () {
  const fileInput = document.getElementById("file-input");
  const selectFileBtn = document.getElementById("select-file");
  const videoPreviewContainer = document.getElementById(
    "video-preview-container"
  );
  const previewImageInput = document.getElementById("preview-image");
  const previewContainer = document.getElementById("preview-container");
  const titleInput = document.getElementById("title");
  const titleWordCount = document.getElementById("title-word-count");
  const descriptionInput = document.getElementById("description");
  const descriptionWordCount = document.getElementById("description-word-count");
  const tagsInput = document.getElementById("tags");
  const tagsWrapper = document.getElementById("tags-input-wrapper");
  const tagsReference = document.getElementById("tags-reference");
  const uploadForm = document.getElementById("upload-form");

  const MAX_TAGS = 10;
  // Define max file size (5GB in bytes)
  const MAX_FILE_SIZE = 5000 * 1024 * 1024;

  let selectedTags = [];

  // fetch categories from API
  fetchCategories();

  // event Listeners
  if (selectFileBtn) {
    console.log("Select file button found, attaching event listener");
    selectFileBtn.addEventListener("click", function (e) {
      e.preventDefault();
      console.log("Select file button clicked");
      fileInput.click();
    });
  } else {
    console.error("Select file button not found in DOM");
  }

  if (fileInput) {
    console.log("File input found, attaching change event listener");
    fileInput.addEventListener("change", handleVideoFileSelect);
  } else {
    console.error("File input not found in DOM");
  }

  if (previewImageInput) {
    previewImageInput.addEventListener("change", handleThumbnailSelect);
  }

  if (titleInput) {
    titleInput.addEventListener("input", function () {
      updateWordCount(this, titleWordCount, 20);
      
    });
  }

  if (descriptionInput) {
    descriptionInput.addEventListener("input", function () {
      updateWordCount(this, descriptionWordCount, 100);
      
    });
  }

  if (tagsInput) {
    tagsInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === ",") {
        e.preventDefault();
        addTag(this.value.trim());
        this.value = "";
      }
    });

    tagsInput.addEventListener("blur", function () {
      if (this.value.trim()) {
        addTag(this.value.trim());
        this.value = "";
      }
    });
  }

  if (tagsReference) {
    tagsReference.addEventListener("click", function (e) {
      if (e.target.classList.contains("tag")) {
        addTag(e.target.textContent);
      }
    });
  }

  if (uploadForm) {
    uploadForm.addEventListener("submit", handleFormSubmit);
  }

  // Add event listeners for the category modal
  const addCategoryBtn = document.getElementById("add-category-btn");
  const categoryModal = document.getElementById("category-modal");
  const closeCategoryModal = document.getElementById("close-category-modal");
  const saveCategoryBtn = document.getElementById("save-category-btn");
  const categoryNameInput = document.getElementById("category-name");
  const categoryDescInput = document.getElementById("category-description");
  const categoryImageInput = document.getElementById("category-image");
  const categoryImagePreview = document.getElementById(
    "category-image-preview"
  );

  if (addCategoryBtn) {
    addCategoryBtn.addEventListener("click", function () {
      // Reset the form
      categoryNameInput.value = "";
      categoryDescInput.value = "";
      categoryImageInput.value = "";
      document.getElementById("category-image-preview").style.display = "none";
      document.getElementById("error-text").style.display = "none";

      // Show the modal
      categoryModal.style.display = "flex";
    });
  }

  if (closeCategoryModal) {
    closeCategoryModal.addEventListener("click", function () {
      categoryModal.style.display = "none";
    });
  }

  // Close modal when clicking outside
  window.addEventListener("click", function (event) {
    if (event.target === categoryModal) {
      categoryModal.style.display = "none";
    }
  });

  // Handle category image preview
  if (categoryImageInput) {
    categoryImageInput.addEventListener("change", function () {
      const file = this.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
          const imagePreview = document.getElementById(
            "category-image-preview"
          );
          imagePreview.innerHTML = `<img src="${e.target.result}" alt="Category Image Preview" style="max-width: 100px; max-height: 100px;">`;
          imagePreview.style.display = "block";
          // Store the base64 data for later use
          imagePreview.dataset.base64 = e.target.result;
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // Handle save category button
  if (saveCategoryBtn) {
    saveCategoryBtn.addEventListener("click", function () {
      // Validate form
      const errorText = document.getElementById("error-text");
      const categoryName = categoryNameInput.value.trim();

      if (!categoryName) {
        errorText.textContent = "Category name is required";
        errorText.style.display = "block";
        return;
      }

      // Clear any previous error
      errorText.style.display = "none";

      // Create FormData
      const formData = new FormData();
      formData.append("name", categoryName);
      formData.append("description", categoryDescInput.value.trim());

      if (categoryImageInput.files[0]) {
        formData.append("image", categoryImageInput.files[0]);
      }

      // Get library ID from the page if available
      const libraryInfo = document.querySelector(".library-info");
      if (libraryInfo && libraryInfo.getAttribute("data-library-id")) {
        formData.append(
          "library_id",
          libraryInfo.getAttribute("data-library-id")
        );
      }

      // Get CSRF token
      const csrftoken = getCookie("csrftoken");

      // Show loading state
      saveCategoryBtn.textContent = "Saving...";
      saveCategoryBtn.disabled = true;

      // Send the request
      fetch("/videos/categories/", {
        method: "POST",
        headers: {
          "X-CSRFToken": csrftoken,
        },
        body: formData,
      })
        .then((response) => {
          if (!response.ok) {
            return response.text().then((text) => {
              console.error("Error response text:", text);
              try {
                // Try to parse as JSON
                const errorData = JSON.parse(text);
                throw new Error(
                  errorData.detail || `Error: ${response.status}`
                );
              } catch (parseError) {
                // If not JSON, use text as error message
                throw new Error(
                  `Error: ${response.status} - ${text.substring(0, 100)}`
                );
              }
            });
          }
          return response.json();
        })
        .then((data) => {
          // Add the new category to the dropdown
          const categorySelect = document.getElementById("category");
          const option = document.createElement("option");
          option.value = data.id;
          option.textContent = data.name;
          categorySelect.appendChild(option);

          // Select the new category
          categorySelect.value = data.id;

          // Hide the modal
          categoryModal.style.display = "none";

          // Show success message
          alert(`Category "${data.name}" created successfully!`);
        })
        .catch((error) => {
          console.error("Error creating category:", error);
          errorText.textContent = "Error creating category: " + error.message;
          errorText.style.display = "block";
        })
        .finally(() => {
          // Reset button state
          saveCategoryBtn.textContent = "Add Category";
          saveCategoryBtn.disabled = false;
        });
    });
  }

  // functions
  function handleVideoFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    console.log("Video file selected:", file.name, "Size:", file.size);

    // check file size
    if (file.size > MAX_FILE_SIZE) {
      alert("File is too large. Maximum size is 5GB.");
      fileInput.value = "";
      return;
    }

    // check file type
    const validTypes = [
      "video/mp4",
      "video/mpeg",
      "video/quicktime",
      "video/x-msvideo",
      "video/x-flv",
      "video/x-matroska",
    ];
    if (!validTypes.includes(file.type)) {
      alert(
        "Invalid file type. Please upload a video file (MP4, MOV, AVI, etc.)"
      );
      fileInput.value = "";
      return;
    }

    console.log("Video file validation passed");

    // create video preview
    videoPreviewContainer.innerHTML = "";
    const video = document.createElement("video");
    video.controls = true;
    video.src = URL.createObjectURL(file);
    videoPreviewContainer.appendChild(video);

    // update file name display
    const fileNameDisplay = document.createElement("div");
    fileNameDisplay.className = "file-name";
    fileNameDisplay.textContent = file.name;
    videoPreviewContainer.appendChild(fileNameDisplay);

    // show loading indicator for metadata extraction
    const loadingIndicator = document.createElement("div");
    loadingIndicator.className = "loading-indicator";
    loadingIndicator.textContent = "Extracting video information...";
    videoPreviewContainer.appendChild(loadingIndicator);

    console.log("Video preview created, extracting metadata");

    // extract video metadata from server
    extractVideoMetadataFromServer(file);
  }

  function handleThumbnailSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    // check file type
    if (!file.type.startsWith("image/")) {
      alert("Please select an image file for the thumbnail.");
      previewImageInput.value = "";
      return;
    }

    // create image preview
    previewContainer.innerHTML = "";
    const img = document.createElement("img");
    img.src = URL.createObjectURL(file);
    previewContainer.appendChild(img);
  }

  function updateWordCount(input, countElement, limit) {
   
    const words = input.value.trim().split(/\s+/).filter(Boolean);
    const count = words.length;


  

    countElement.textContent = `${count}/${limit} words`;

    if (count > limit) {
      countElement.classList.add("error");
    } else {
      countElement.classList.remove("error");
    }
  }

  function addTag(tag) {
    if (!tag || selectedTags.includes(tag) || selectedTags.length >= MAX_TAGS)
      return;

    selectedTags.push(tag);

    const tagElement = document.createElement("span");
    tagElement.className = "tag";
    tagElement.textContent = tag;

    const removeBtn = document.createElement("span");
    removeBtn.className = "remove-tag";
    removeBtn.innerHTML = "&times;";
    removeBtn.addEventListener("click", function () {
      tagElement.remove();
      selectedTags = selectedTags.filter((t) => t !== tag);
    });

    tagElement.appendChild(removeBtn);
    tagsWrapper.insertBefore(tagElement, tagsInput);
  }

  function updateMetadataFields(metadata) {
    // update duration display
    const durationDisplay = document.getElementById("duration-display");
    if (durationDisplay && metadata.duration) {
      durationDisplay.textContent = metadata.duration;
    }

    // update format display
    const formatDisplay = document.getElementById("format-display");
    if (formatDisplay && metadata.format) {
      formatDisplay.textContent = metadata.format;
    }

    // update file size display
    const fileSizeDisplay = document.getElementById("filesize-display");
    if (fileSizeDisplay && metadata.file_size_display) {
      fileSizeDisplay.textContent = metadata.file_size_display;
    }

    // remove loading indicator if it exists
    const loadingIndicator = document.querySelector(".loading-indicator");
    if (loadingIndicator) {
      loadingIndicator.remove();
    }
  }

  function extractVideoMetadataFromServer(file) {
    console.log("Sending file to server for metadata extraction");

    // create a FormData object to send the file
    const formData = new FormData();
    formData.append("video_file", file);

    // get CSRF token
    const csrfToken = getCookie("csrftoken");

    // send the file to the server for metadata extraction
    fetch("/videos/api/extract-metadata/", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
      },
      body: formData,
    })
      .then((response) => {
        console.log("Metadata extraction response:", response.status);

        // First check if response is ok (status in 200-299 range)
        if (!response.ok) {
          console.error("API error:", response.status, response.statusText);
          // Don't try to parse JSON for non-OK responses
          return response.text().then((text) => {
            throw new Error(
              `API error: ${response.status} ${response.statusText}${
                text ? ` - ${text}` : ""
              }`
            );
          });
        }

        // For successful responses, try to parse as JSON
        return response.text().then((text) => {
          if (!text) {
            throw new Error("Empty response received from server");
          }

          try {
            return JSON.parse(text);
          } catch (e) {
            console.error("Failed to parse JSON:", e, "Response text:", text);
            throw new Error("Invalid JSON response from server");
          }
        });
      })
      .then((data) => {
        console.log("Metadata extraction data:", data);
        if (data.success && data.metadata) {
          // update the UI with the extracted metadata
          updateMetadataFields(data.metadata);
          console.log("Metadata extracted successfully:", data.metadata);
        } else {
          console.error("Failed to extract metadata:", data.message);
          // fall back to client-side extraction
          extractVideoMetadata(file);
        }
      })
      .catch((error) => {
        console.error("Error extracting metadata from server:", error);
        // fall back to client-side extraction
        extractVideoMetadata(file);
      });
  }

  function extractVideoMetadata(file) {
    // this is a client-side approximation - server will do more accurate extraction
    const video = document.createElement("video");
    video.preload = "metadata";
    video.onloadedmetadata = function () {
      // update duration display
      const durationDisplay = document.getElementById("duration-display");
      if (durationDisplay) {
        const duration = Math.round(video.duration);
        const hours = Math.floor(duration / 3600);
        const minutes = Math.floor((duration % 3600) / 60);
        const seconds = duration % 60;
        durationDisplay.textContent = `${minutes}:${seconds
          .toString()
          .padStart(2, "0")}`;
      }

      // update format display
      const formatDisplay = document.getElementById("format-display");
      if (formatDisplay) {
        const format = file.name.split(".").pop().toUpperCase();
        formatDisplay.textContent = format;
      }

      // update file size display
      const fileSizeDisplay = document.getElementById("filesize-display");
      if (fileSizeDisplay) {
        const fileSizeMB = file.size / (1024 * 1024);
        if (fileSizeMB < 1024) {
          fileSizeDisplay.textContent = `${fileSizeMB.toFixed(1)} MB`;
        } else {
          fileSizeDisplay.textContent = `${(fileSizeMB / 1024).toFixed(2)} GB`;
        }
      }

      // remove loading indicator if it exists
      const loadingIndicator = document.querySelector(".loading-indicator");
      if (loadingIndicator) {
        loadingIndicator.remove();
      }

      URL.revokeObjectURL(video.src);
    };
    video.src = URL.createObjectURL(file);
  }

  async function fetchCategories() {
    try {
      console.log("Fetching categories...");
      // Get the current library ID from the page
      let currentLibraryId = null;
      const libraryInfo = document.querySelector(".library-info");
      if (libraryInfo) {
        // Try to extract library ID from data attribute if available
        currentLibraryId = libraryInfo.getAttribute("data-library-id");
      }

      // Build API URL with library filter if we have a library ID
      let apiUrl = "/videos/categories/";
      if (currentLibraryId) {
        apiUrl += `?library=${currentLibraryId}`;
      }
      console.log(`Using API URL: ${apiUrl}`);

      // fetch cache options
      const response = await fetch(apiUrl, {
        method: "GET",
        cache: "no-cache", // force server request, don't check cache
        headers: {
          "Cache-Control": "no-cache",
          Pragma: "no-cache",
        },
      });
      console.log("Response status:", response.status);

      if (!response.ok) {
        console.error("Failed to fetch categories. Status:", response.status);
        throw new Error(`Failed to fetch categories: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("Categories raw data:", data);

      const categorySelect = document.getElementById("category");
      if (!categorySelect) {
        console.error("Category select element not found in DOM");
        return;
      }

      // Handle different possible API response formats
      let categories = [];
      if (data.results && Array.isArray(data.results)) {
        // DRF paginated response format
        categories = data.results;
      } else if (Array.isArray(data)) {
        // Simple array response format
        categories = data;
      } else if (typeof data === "object" && !Array.isArray(data)) {
        // Object response format (convert to array)
        categories = Object.values(data);
      }

      console.log("Processed categories:", categories);

      // Clear existing options
      categorySelect.innerHTML = "";

      // Add initial "Select a category" option
      const defaultOption = document.createElement("option");
      defaultOption.value = "";
      defaultOption.textContent = "Select a category";
      categorySelect.appendChild(defaultOption);

      // Populate select with retrieved categories
      if (categories.length > 0) {
        categories.forEach((category) => {
          const option = document.createElement("option");

          // Handle different category object structures
          let categoryId, categoryName, libraryId, libraryName;

          if (category.id !== undefined) {
            categoryId = category.id;
            categoryName = category.name;

            // Log library information if available for debugging
            if (category.library !== undefined) {
              if (typeof category.library === "object") {
                libraryId = category.library.id;
                libraryName = category.library.name;
              } else {
                libraryId = category.library;
              }
              console.log(
                `Category ${categoryName} (ID: ${categoryId}) belongs to library: ${
                  libraryName || libraryId
                }`
              );
            }
          } else if (category.pk !== undefined) {
            categoryId = category.pk;
            categoryName = category.fields?.name || "Unknown";
          } else {
            console.warn("Unexpected category format:", category);
            return; // Skip this category
          }

          option.value = categoryId;
          option.textContent = categoryName;
          categorySelect.appendChild(option);
        });
        console.log(
          `Added ${categories.length} categories to the select element`
        );
      } else {
        console.warn("No categories found to display");
        const option = document.createElement("option");
        option.disabled = true;
        option.textContent = "No categories available";
        categorySelect.appendChild(option);
      }
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  }

  async function handleFormSubmit(e) {
    // Rest of the function body remains unchanged
    // ...
  }

  function validateForm() {
    // Rest of the function body remains unchanged
    // ...
  }

  // helper function to get CSRF cookie
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
});
