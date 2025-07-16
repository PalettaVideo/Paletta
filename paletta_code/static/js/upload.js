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
  let selectedContentType = null; // Store the selected content type
  let videoMetadata = {}; // Variable to store extracted metadata

  // fetch content types from API
  fetchContentTypes();

  // event Listeners
  if (selectFileBtn) {
    selectFileBtn.addEventListener("click", function (e) {
      e.preventDefault();
      fileInput.click();
    });
  } else {
    console.error("Select file button not found in DOM");
  }

  if (fileInput) {
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

  // functions

  function handleVideoFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

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

  async function fetchContentTypes() {
    try {
      // Get library ID from meta tag or data attribute
      const libraryId = document
        .querySelector('meta[name="current-library-id"]')
        .getAttribute("content");

      // Use the content types API with library filtering
      let apiUrl = `/api/content-types/`;
      if (libraryId) {
        apiUrl += `?library=${libraryId}`;
      }

      // fetch with cache options
      const response = await fetch(apiUrl, {
        method: "GET",
        cache: "no-cache", // force server request, don't check cache
        headers: {
          "Cache-Control": "no-cache",
          Pragma: "no-cache",
        },
      });

      if (!response.ok) {
        console.error(
          "Failed to fetch content types. Status:",
          response.status
        );
        throw new Error(
          `Failed to fetch content types: ${response.statusText}`
        );
      }

      const contentTypes = await response.json();

      const contentTypesGrid = document.getElementById("content-types-grid");
      const contentTypesError = document.getElementById("content-types-error");

      if (!contentTypesGrid) {
        console.error("Content types grid element not found in DOM");
        return;
      }

      // Clear existing content
      contentTypesGrid.innerHTML = "";

      if (contentTypes.length === 0) {
        contentTypesGrid.innerHTML =
          "<p>No content types available for this library.</p>";
        return;
      }

      // Create content type cards for SINGLE selection only
      contentTypes.forEach((contentType) => {
        const card = document.createElement("div");
        card.className = "content-type-card";
        card.dataset.contentTypeId = contentType.id;
        card.dataset.contentTypeCode =
          contentType.code || contentType.subject_area;

        card.innerHTML = `
          <div class="content-type-title">${
            contentType.display_name || contentType.name
          }</div>
          <div class="content-type-check">✓</div>
        `;

        card.addEventListener("click", function () {
          handleContentTypeSelection(this);
        });

        contentTypesGrid.appendChild(card);
      });
    } catch (error) {
      console.error("Error fetching content types:", error);
      const contentTypesGrid = document.getElementById("content-types-grid");
      const contentTypesError = document.getElementById("content-types-error");

      if (contentTypesError) {
        contentTypesError.textContent = "Error loading content types";
        contentTypesError.style.display = "block";
      }

      if (contentTypesGrid) {
        contentTypesGrid.innerHTML = "";
      }
    }
  }

  function handleContentTypeSelection(clickedCard) {
    // Remove selection from all cards
    const allCards = document.querySelectorAll(".content-type-card");
    allCards.forEach((card) => {
      card.classList.remove("selected");
    });

    // Add selection to clicked card
    clickedCard.classList.add("selected");

    // Store the selected content type
    selectedContentType = {
      id: clickedCard.dataset.contentTypeId,
      code: clickedCard.dataset.contentTypeCode,
    };

    // Hide error message if visible
    const contentTypesError = document.getElementById("content-types-error");
    if (contentTypesError) {
      contentTypesError.style.display = "none";
    }
  }

  async function handleFormSubmit(e) {
    e.preventDefault();
    const uploadButton = uploadForm.querySelector("button[type='submit']");

    // Validate form fields before proceeding
    if (!validateForm()) {
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

      // 2. Upload the file directly to S3 using the presigned URL
      const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1);
      uploadButton.textContent = `Uploading... (0%) - ${fileSizeMB}MB`;
      const s3UploadResponse = await uploadFileToS3(
        uploadURL,
        file,
        (progress) => {
          const uploadedMB = (
            (file.size * progress) /
            100 /
            (1024 * 1024)
          ).toFixed(1);
          uploadButton.textContent = `Uploading... (${progress.toFixed(
            0
          )}%) - ${uploadedMB}MB/${fileSizeMB}MB`;
        }
      );

      if (s3UploadResponse.status !== 200) {
        throw new Error("S3 upload failed. Please try again.");
      }

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

      // Set timeout for large files (5 minutes)
      xhr.timeout = 300000;

      // Add content type header for better S3 handling
      xhr.setRequestHeader("Content-Type", file.type);

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const progress = (event.loaded / event.total) * 100;
          onProgress(progress);
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(xhr);
        } else {
          reject(new Error(`Upload failed with status: ${xhr.status}`));
        }
      };

      xhr.onerror = () => {
        reject(new Error("Network error during S3 upload."));
      };

      xhr.ontimeout = () => {
        reject(new Error("Upload timed out. Please try again."));
      };

      xhr.send(file);
    });
  }

  async function notifyBackend(s3Key) {
    const libraryInfo = document.querySelector(".library-info");
    const libraryId = libraryInfo
      ? libraryInfo.getAttribute("data-library-id")
      : null;

    // Use FormData to send both file and text data
    const formData = new FormData();
    formData.append("title", titleInput.value.trim());
    formData.append("description", descriptionInput.value.trim());
    formData.append(
      "content_type",
      selectedContentType ? selectedContentType.id : ""
    );
    formData.append("tags", selectedTags.join(","));
    formData.append("s3_key", s3Key);
    formData.append("library_id", libraryId);
    formData.append("duration", videoMetadata.duration);
    formData.append("file_size", videoMetadata.fileSize);
    formData.append("format", videoMetadata.format);

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
    const contentTypesError = document.getElementById("content-types-error");

    if (!title) {
      alert("Please enter a video title");
      titleInput.focus();
      return false;
    }

    if (!selectedContentType) {
      if (contentTypesError) {
        contentTypesError.textContent = "Please select a content type";
        contentTypesError.style.display = "block";
      } else {
        alert("Please select a content type");
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
