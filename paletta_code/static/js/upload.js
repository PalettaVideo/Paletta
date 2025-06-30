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
  const descriptionWordCount = document.getElementById(
    "description-word-count"
  );
  const tagsInput = document.getElementById("tags");
  const tagsWrapper = document.getElementById("tags-input-wrapper");
  const tagsReference = document.getElementById("tags-reference");
  const uploadForm = document.getElementById("upload-form");

  const MAX_TAGS = 10;
  // Define max file size (256GB in bytes)
  const MAX_FILE_SIZE = 256 * 1024 * 1024 * 1024;

  let selectedTags = [];
  let videoMetadata = {}; // Variable to store extracted metadata

  // fetch categories and content types from API
  fetchCategories();
  fetchContentTypes();

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

  // Add event listeners for content type checkboxes
  const contentTypeCheckboxes = document.querySelectorAll(
    ".content-type-checkbox"
  );
  contentTypeCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", handleContentTypeChange);
  });

  // Category creation removed - categories are now predefined by administrators
  // Users can only select from existing categories

  // functions
  function handleContentTypeChange(event) {
    const selectedContentTypes = document.querySelectorAll(
      ".content-type-checkbox:checked"
    );
    const contentTypesError = document.getElementById("content-types-error");
    const allContentTypeItems = document.querySelectorAll(".content-type-item");

    // If trying to select more than 3, prevent the selection
    if (event && event.target.checked && selectedContentTypes.length > 3) {
      event.target.checked = false;
      if (contentTypesError) {
        contentTypesError.textContent =
          "You can select a maximum of 3 content types.";
        contentTypesError.style.display = "block";
      }
      return;
    }

    // Clear previous error messages
    if (contentTypesError) {
      contentTypesError.style.display = "none";
      contentTypesError.textContent = "";
    }

    // Remove disabled class from all items
    allContentTypeItems.forEach((item) => {
      item.classList.remove("disabled");
      const checkbox = item.querySelector(".content-type-checkbox");
      if (checkbox && !checkbox.checked) {
        checkbox.disabled = false;
      }
    });

    // If exactly 3 content types are selected, disable the rest
    if (selectedContentTypes.length >= 3) {
      allContentTypeItems.forEach((item) => {
        const checkbox = item.querySelector(".content-type-checkbox");
        if (checkbox && !checkbox.checked) {
          item.classList.add("disabled");
          checkbox.disabled = true;
        }
      });
    }
  }
  function handleVideoFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    console.log("Video file selected:", file.name, "Size:", file.size);

    // check file size
    if (file.size > MAX_FILE_SIZE) {
      showUploadLimitModal();
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

    // Use fast, client-side extraction. Server-side is no longer needed.
    extractVideoMetadata(file);
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

  function extractVideoMetadata(file) {
    // this is a client-side approximation - server will do more accurate extraction
    const video = document.createElement("video");
    video.preload = "metadata";
    video.onloadedmetadata = function () {
      // Store metadata in our variable
      videoMetadata.duration = Math.round(video.duration);
      videoMetadata.fileSize = file.size;
      videoMetadata.format = file.name.split(".").pop().toUpperCase();

      // update duration display
      const durationDisplay = document.getElementById("duration-display");
      if (durationDisplay) {
        const duration = videoMetadata.duration;
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
        formatDisplay.textContent = videoMetadata.format;
      }

      // update file size display
      const fileSizeDisplay = document.getElementById("filesize-display");
      if (fileSizeDisplay) {
        const fileSizeMB = videoMetadata.fileSize / (1024 * 1024);
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

      if (!currentLibraryId) {
        console.error("No library ID found, cannot fetch categories");
        return;
      }

      // Use the new unified category API
      let apiUrl = `/api/api/categories/?library=${currentLibraryId}`;
      console.log(`Using unified API URL: ${apiUrl}`);

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

      const categories = await response.json();
      console.log("Categories data:", categories);

      const categorySelect = document.getElementById("category");
      if (!categorySelect) {
        console.error("Category select element not found in DOM");
        return;
      }

      // Clear existing options
      categorySelect.innerHTML = "";

      // Add initial "Select a category" option
      const defaultOption = document.createElement("option");
      defaultOption.value = "";
      defaultOption.textContent = "Select a category";
      categorySelect.appendChild(defaultOption);

      // Add categories to the select dropdown
      categories.forEach((category) => {
        const option = document.createElement("option");
        option.value = category.id;

        // Handle both paletta and library categories
        if (category.type === "paletta_category") {
          option.textContent = `${category.display_name} (Paletta)`;
        } else if (
          category.type === "library_category" ||
          category.type === "subject_area"
        ) {
          option.textContent = category.display_name || category.name;
        } else {
          option.textContent = category.display_name || category.name;
        }

        categorySelect.appendChild(option);
      });

      console.log(`Added ${categories.length} categories to select dropdown`);
    } catch (error) {
      console.error("Error fetching categories:", error);
      const categorySelect = document.getElementById("category");
      if (categorySelect) {
        categorySelect.innerHTML = "";
        const errorOption = document.createElement("option");
        errorOption.value = "";
        errorOption.textContent = "Error loading categories";
        categorySelect.appendChild(errorOption);
      }
    }
  }

  async function fetchContentTypes() {
    try {
      console.log("Fetching content types...");

      const response = await fetch("/api/api/content-types/", {
        method: "GET",
        cache: "no-cache",
        headers: {
          "Cache-Control": "no-cache",
          Pragma: "no-cache",
        },
      });

      console.log("Content types response status:", response.status);
      console.log("Content types response headers:", response.headers);

      if (!response.ok) {
        console.error(
          "Failed to fetch content types. Status:",
          response.status
        );
        const errorText = await response.text();
        console.error("Error response:", errorText);
        return;
      }

      const contentTypes = await response.json();
      console.log("Content types data received:", contentTypes);
      console.log("Number of content types:", contentTypes.length);

      if (!contentTypes || contentTypes.length === 0) {
        console.error("No content types received from API");
        return;
      }

      // Create content types selection UI
      createContentTypesUI(contentTypes);
    } catch (error) {
      console.error("Error fetching content types:", error);
      console.error("Error stack:", error.stack);
    }
  }

  function createContentTypesUI(contentTypes) {
    console.log("Creating content types UI with data:", contentTypes);

    // Use existing content types grid from HTML template
    const contentTypesGrid = document.getElementById("content-types-grid");
    if (!contentTypesGrid) {
      console.error("Content types grid not found in HTML template");
      console.error(
        "Available elements with 'content' in ID:",
        Array.from(document.querySelectorAll('[id*="content"]')).map(
          (el) => el.id
        )
      );
      return;
    }

    console.log("Found content types grid element:", contentTypesGrid);

    // Clear existing content types
    contentTypesGrid.innerHTML = "";

    // Add content types as checkboxes
    contentTypes.forEach((contentType, index) => {
      console.log(`Creating checkbox for content type ${index}:`, contentType);

      const checkboxWrapper = document.createElement("div");
      checkboxWrapper.className = "content-type-item";
      checkboxWrapper.innerHTML = `
        <input type="checkbox" id="content-type-${
          contentType.id
        }" name="content_types" value="${
        contentType.id
      }" class="content-type-checkbox">
        <label for="content-type-${contentType.id}" class="content-type-label">
          <span class="content-type-name">${
            contentType.display_name || contentType.name
          }</span>
        </label>
      `;
      contentTypesGrid.appendChild(checkboxWrapper);
    });

    // Add validation for 1-3 content types selection
    const checkboxes = contentTypesGrid.querySelectorAll(
      ".content-type-checkbox"
    );

    console.log(`Found ${checkboxes.length} checkboxes after creation`);

    checkboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", handleContentTypeChange);
    });

    console.log(
      `✓ Successfully added ${contentTypes.length} content types to the form`
    );
    console.log("Content types grid final HTML:", contentTypesGrid.innerHTML);
  }

  async function handleFormSubmit(e) {
    e.preventDefault();
    const uploadButton = uploadForm.querySelector("button[type='submit']");

    // Validate form fields before proceeding
    if (!validateForm()) {
      alert("Please fill out all required fields: Title and Category.");
      return;
    }

    const file = fileInput.files[0];
    if (!file) {
      alert("Please select a video file to upload.");
      return;
    }

    uploadButton.textContent = "Preparing Upload...";
    uploadButton.disabled = true;

    try {
      // 1. Get presigned URL from our Lambda function via API Gateway
      const apiGatewayUrl = uploadForm.dataset.apiGatewayUrl;
      if (!apiGatewayUrl) {
        throw new Error(
          "API Gateway URL is not configured. Please contact support."
        );
      }
      const response = await fetch(
        `${apiGatewayUrl}?fileName=${file.name}&contentType=${file.type}`
      );

      if (!response.ok) {
        throw new Error("Could not get a presigned URL. Please try again.");
      }

      const { uploadURL, key } = await response.json();
      console.log("Received presigned URL and key:", uploadURL, key);

      // 2. Upload the file directly to S3 using the presigned URL
      uploadButton.textContent = "Uploading... (0%)";
      const s3UploadResponse = await uploadFileToS3(
        uploadURL,
        file,
        (progress) => {
          uploadButton.textContent = `Uploading... (${progress.toFixed(0)}%)`;
        }
      );

      if (s3UploadResponse.status !== 200) {
        throw new Error("S3 upload failed. Please try again.");
      }
      console.log("File successfully uploaded to S3.");

      // 3. Notify the backend that the upload is complete
      uploadButton.textContent = "Finalizing...";
      await notifyBackend(key);

      alert("Upload complete! Your video has been successfully submitted.");
      // Redirect to the success URL provided by the form's data attribute
      const successUrl = uploadForm.dataset.successUrl;
      if (successUrl) {
        window.location.href = successUrl;
      } else {
        console.error(
          "Success URL not found on form data-success-url attribute. Cannot redirect."
        );
        // Fallback or display a message
        window.location.href = "/"; // Redirect to home page as a fallback
      }
    } catch (error) {
      console.error("Upload process failed:", error);
      alert(`An error occurred: ${error.message}`);
      uploadButton.textContent = "Upload Clip";
      uploadButton.disabled = false;
    }
  }

  function uploadFileToS3(uploadURL, file, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("PUT", uploadURL);

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const progress = (event.loaded / event.total) * 100;
          onProgress(progress);
        }
      };

      xhr.onload = () => {
        resolve(xhr);
      };

      xhr.onerror = () => {
        reject(new Error("Network error during S3 upload."));
      };

      xhr.send(file);
    });
  }

  async function notifyBackend(s3Key) {
    const libraryInfo = document.querySelector(".library-info");
    const libraryId = libraryInfo
      ? libraryInfo.getAttribute("data-library-id")
      : null;

    // Get selected content types
    const selectedContentTypes = Array.from(
      document.querySelectorAll(".content-type-checkbox:checked")
    ).map((checkbox) => checkbox.value);

    // Use FormData to send both file and text data
    const formData = new FormData();
    formData.append("title", titleInput.value.trim());
    formData.append("description", descriptionInput.value.trim());
    formData.append("category", document.getElementById("category").value);
    formData.append("tags", selectedTags.join(","));
    formData.append("s3_key", s3Key);
    formData.append("library_id", libraryId);
    formData.append("duration", videoMetadata.duration);
    formData.append("file_size", videoMetadata.fileSize);
    formData.append("format", videoMetadata.format);

    // Add content types (multiple values)
    selectedContentTypes.forEach((contentTypeId) => {
      formData.append("content_types", contentTypeId);
    });

    // Append the thumbnail file if it exists
    const thumbnailFile = previewImageInput.files[0];
    if (thumbnailFile) {
      formData.append("thumbnail", thumbnailFile);
    }

    const response = await fetch("/api/api/upload/", {
      method: "POST",
      headers: {
        // 'Content-Type' is set automatically by the browser for FormData
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: formData,
      credentials: "include", // Include cookies for cross-origin authentication
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || "Backend notification failed.");
    }
    return await response.json();
  }

  function validateForm() {
    const title = titleInput.value.trim();
    const category = document.getElementById("category").value;

    // Validate content types selection
    const selectedContentTypes = document.querySelectorAll(
      ".content-type-checkbox:checked"
    );
    const contentTypesError = document.getElementById("content-types-error");

    if (!title) {
      alert("Please enter a video title");
      titleInput.focus();
      return false;
    }

    if (!category) {
      alert("Please select a category");
      document.getElementById("category").focus();
      return false;
    }

    if (selectedContentTypes.length === 0) {
      alert("Please select at least 1 content type");
      if (contentTypesError) {
        contentTypesError.textContent =
          "Please select at least 1 content type.";
        contentTypesError.style.display = "block";
      }
      return false;
    }

    if (selectedContentTypes.length > 3) {
      alert("Please select no more than 3 content types");
      if (contentTypesError) {
        contentTypesError.textContent =
          "Please select no more than 3 content types.";
        contentTypesError.style.display = "block";
      }
      return false;
    }

    return true;
  }

  function showUploadLimitModal() {
    const modal = document.getElementById("upload-limit-modal");
    const message = document.getElementById("modal-message");
    const closeBtn = modal.querySelector(".close-button");

    message.textContent =
      "The video is above the upload limit of 256GB and won't be processed. Please contact the owner of the website to upload.";
    modal.style.display = "block";

    closeBtn.onclick = function () {
      modal.style.display = "none";
    };

    window.onclick = function (event) {
      if (event.target == modal) {
        modal.style.display = "none";
      }
    };
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
