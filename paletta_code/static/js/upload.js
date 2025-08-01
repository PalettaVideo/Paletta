// Begin script - Add beforeunload event listener
window.addEventListener("beforeunload", function (e) {
  if (window.__uploadInProgress__) {
    e.preventDefault();
    e.returnValue =
      "Are you sure you want to leave the page? The video upload will stop!";
    return e.returnValue;
  }
});

// Override console logging during upload
function suppressConsole() {
  // console.log = function () {};
  // console.debug = function () {};
  // console.warn = function () {};
  // console.info = function () {};
  // console.error = function () {};
}

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
      updateCharacterCount(this, titleWordCount, 200);
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

  function updateCharacterCount(input, countElement, limit) {
    const count = input.value.length;

    countElement.textContent = `${count}/${limit} characters`;

    if (count > limit) {
      countElement.classList.add("error");
    } else {
      countElement.classList.remove("error");
    }
  }

  function handleVideoFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    // File size validation - 10GB limit
    const maxFileSize = 10 * 1024 * 1024 * 1024; // 10GB in bytes
    if (file.size > maxFileSize) {
      const fileSizeGB = (file.size / (1024 * 1024 * 1024)).toFixed(2);
      alert(
        `File size (${fileSizeGB}GB) exceeds the maximum allowed size of 10GB. Please select a smaller file.`
      );
      fileInput.value = "";
      return;
    }

    // File type validation
    const allowedTypes = [
      "video/mp4",
      "video/mpeg",
      "video/quicktime",
      "video/x-msvideo",
      "video/webm",
      "video/ogg",
      "video/x-ms-wmv",
      "video/x-flv",
    ];
    if (!allowedTypes.includes(file.type)) {
      alert("Please select a valid video file (MP4, MOV, AVI, etc.).");
      fileInput.value = "";
      return;
    }

    // Display file info
    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1);
    const fileSizeGB = (file.size / (1024 * 1024 * 1024)).toFixed(2);

    // Show upload method info
    let uploadMethod = "Single-part upload";
    if (file.size > 5 * 1024 * 1024) {
      // 5MB
      uploadMethod = "Multipart upload (optimized for large files)";
    }

    const previewContainer = document.getElementById("video-preview-container");
    previewContainer.innerHTML = `
      <div class="file-info">
        <h3>Selected Video</h3>
        <div class="video-preview">
          <video controls preload="metadata" style="max-width: 100%; max-height: 350px; border-radius: 8px;">
            <source src="${URL.createObjectURL(file)}" type="${file.type}">
            Your browser does not support the video tag.
          </video>
        </div>
        <p><strong>Name:</strong> ${file.name}</p>

        <div class="progress-bar" style="display: none;">
          <div class="progress-fill"></div>
        </div>
        <div class="upload-progress" style="display: none;">
          <div class="progress-text">0%</div>
        </div>
      </div>
    `;

    // Extract and display video metadata
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
    } catch {
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
    window.__uploadInProgress__ = true;
    suppressConsole();

    const uploadButton = uploadForm.querySelector("button[type='submit']");

    // Validate form fields before proceeding
    if (!validateForm()) {
      window.__uploadInProgress__ = false;
      return;
    }

    const file = fileInput.files[0];
    if (!file) {
      alert("Please select a video file to upload.");
      window.__uploadInProgress__ = false;
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
      const fileSizeGB = (file.size / (1024 * 1024 * 1024)).toFixed(2);

      // Determine upload method and calculate chunks for multipart
      const uploadMethod =
        file.size > 5 * 1024 * 1024 ? "Multipart" : "Single-part";
      const CHUNK_SIZE = 100 * 1024 * 1024; // 100MB chunks
      const totalChunks =
        file.size > 5 * 1024 * 1024 ? Math.ceil(file.size / CHUNK_SIZE) : 1;

      uploadButton.textContent = `Uploading... (0%) - ${fileSizeMB}MB (${uploadMethod})`;

      // Show progress bar
      const progressBar = document.querySelector(".progress-bar");
      const progressFill = document.querySelector(".progress-fill");
      const uploadProgress = document.querySelector(".upload-progress");
      const progressTextElement = document.querySelector(".progress-text");

      if (progressBar && progressFill) {
        progressBar.style.display = "block";
        progressFill.style.width = "0%";
      }

      if (uploadProgress && progressTextElement) {
        uploadProgress.style.display = "block";
        progressTextElement.textContent = "0%";
      }

      const s3UploadResponse = await uploadFileToS3(
        uploadURL,
        file,
        (progress) => {
          const uploadedMB = (
            (file.size * progress) /
            100 /
            (1024 * 1024)
          ).toFixed(1);
          const uploadedGB = (
            (file.size * progress) /
            100 /
            (1024 * 1024 * 1024)
          ).toFixed(2);

          // Show simple progress text
          let progressText = `Uploading... (${progress.toFixed(0)}%)`;

          if (file.size > 100 * 1024 * 1024) {
            // Show GB for files > 100MB
            uploadButton.textContent = `${progressText} - ${uploadedGB}GB/${fileSizeGB}GB (${uploadMethod})`;
          } else {
            uploadButton.textContent = `${progressText} - ${uploadedMB}MB/${fileSizeMB}MB (${uploadMethod})`;
          }

          // Update progress bar
          const progressBar = document.querySelector(".progress-bar");
          const progressFill = document.querySelector(".progress-fill");
          const uploadProgress = document.querySelector(".upload-progress");
          const progressTextElement = document.querySelector(".progress-text");

          if (progressBar && progressFill) {
            progressBar.style.display = "block";
            progressFill.style.width = `${progress}%`;
          }

          if (uploadProgress && progressTextElement) {
            uploadProgress.style.display = "block";
            progressTextElement.textContent = `${progress.toFixed(0)}%`;
          }
        }
      );

      if (s3UploadResponse.status !== 200) {
        throw new Error("S3 upload failed. Please try again.");
      }

      // 3. Notify the backend that the upload is complete
      uploadButton.textContent = "Finalizing...";
      await notifyBackend(key);

      alert("Upload complete! Your video has been successfully submitted.");
      window.__uploadInProgress__ = false;
      // Redirect to the success URL provided by the form's data attribute
      const successUrl = uploadForm.dataset.successUrl;
      if (successUrl) {
        window.location.href = successUrl;
      } else {
        // Fallback or display a message
        window.location.href = "/"; // Redirect to home page as a fallback
      }
    } catch (error) {
      alert(`An error occurred: ${error.message}`);
      uploadButton.textContent = "Upload Clip";
      uploadButton.disabled = false;
      window.__uploadInProgress__ = false;
    }
  }

  function uploadFileToS3(uploadURL, file, onProgress) {
    // Use multipart upload for files larger than 5MB
    const MULTIPART_THRESHOLD = 5 * 1024 * 1024; // 5MB

    if (file.size > MULTIPART_THRESHOLD) {
      return uploadFileToS3Multipart(uploadURL, file, onProgress);
    } else {
      return uploadFileToS3Single(uploadURL, file, onProgress);
    }
  }

  function uploadFileToS3Single(uploadURL, file, onProgress) {
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

  function uploadFileToS3Multipart(uploadURL, file, onProgress) {
    const CHUNK_SIZE = 100 * 1024 * 1024;
    const MAX_CONCURRENT_CHUNKS = 10;

    return (async function () {
      const url = new URL(uploadURL);
      const bucket = url.hostname.split(".")[0];
      const key = url.pathname.substring(1);
      const totalChunks = Math.ceil(file.size / CHUNK_SIZE);

      // Track cumulative uploaded bytes for smooth progress
      let totalUploadedBytes = 0;
      const totalFileSize = file.size;
      const activeChunkProgress = {}; // chunkIndex → bytes uploaded

      const createMultipartResponse = await fetch(
        "/api/s3/create-multipart-upload/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify({ bucket, key, content_type: file.type }),
        }
      );

      const { upload_id } = await createMultipartResponse.json();
      const parts = [];

      const uploadChunk = async (chunkIndex) => {
        const start = chunkIndex * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, file.size);
        const chunk = file.slice(start, end);

        const partResponse = await fetch("/api/s3/get-upload-part-url/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify({
            bucket,
            key,
            upload_id,
            part_number: chunkIndex + 1,
          }),
        });

        const { presigned_url } = await partResponse.json();

        return new Promise((resolve, reject) => {
          const xhr = new XMLHttpRequest();
          xhr.open("PUT", presigned_url);
          xhr.setRequestHeader("Content-Type", file.type);

          xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
              // Track this chunk's progress
              activeChunkProgress[chunkIndex] = event.loaded;

              // Calculate cumulative progress from all active chunks
              const uploaded = Object.values(activeChunkProgress).reduce(
                (sum, bytes) => sum + bytes,
                0
              );

              // Calculate overall progress based on actual bytes uploaded
              const progress = (uploaded / totalFileSize) * 100;
              onProgress(progress);
            }
          };

          xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              // Mark this chunk as fully uploaded
              activeChunkProgress[chunkIndex] = chunk.size;

              const etag = xhr.getResponseHeader("ETag");
              resolve({ PartNumber: chunkIndex + 1, ETag: etag });
            } else {
              reject(new Error(`Failed to upload part ${chunkIndex + 1}`));
            }
          };

          xhr.onerror = () => {
            reject(new Error(`Network error uploading part ${chunkIndex + 1}`));
          };

          xhr.send(chunk);
        });
      };

      for (let i = 0; i < totalChunks; i += MAX_CONCURRENT_CHUNKS) {
        const chunkPromises = [];
        for (let j = 0; j < MAX_CONCURRENT_CHUNKS && i + j < totalChunks; j++) {
          chunkPromises.push(uploadChunk(i + j));
        }
        const chunkResults = await Promise.all(chunkPromises);
        parts.push(...chunkResults);

        // Update progress after each batch completes
        const completed = parts.length;
        const progress = (completed / totalChunks) * 100;
        onProgress(progress);
      }

      await fetch("/api/s3/complete-multipart-upload/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ bucket, key, upload_id, parts }),
      });

      return {
        status: 200,
        responseText: "Multipart upload completed successfully",
      };
    })();
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

    const response = await fetch("/api/uploads/", {
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
    const description = descriptionInput.value.trim();
    const thumbnail = previewImageInput.files[0];
    const contentTypesError = document.getElementById("content-types-error");

    if (!fileInput.files.length) {
      alert("WARNING: A video file is required.");
      return false;
    }

    if (!title) {
      alert("WARNING: A title is required.");
      titleInput.focus();
      return false;
    }

    if (!description) {
      alert("WARNING: A description is required.");
      descriptionInput.focus();
      return false;
    }

    if (!thumbnail) {
      alert("WARNING: A thumbnail image is required.");
      return false;
    }

    if (!selectedContentType) {
      if (contentTypesError) {
        contentTypesError.textContent = "WARNING: Select a content type.";
        contentTypesError.style.display = "block";
      } else {
        alert("WARNING: A content type must be selected.");
      }
      return false;
    }

    if (selectedTags.length === 0) {
      alert("WARNING: At least one tag is required.");
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
