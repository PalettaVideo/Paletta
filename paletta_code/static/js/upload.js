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
          <video controls preload="metadata" style="max-width: 100%; max-height: 300px; border-radius: 8px;">
            <source src="${URL.createObjectURL(file)}" type="${file.type}">
            Your browser does not support the video tag.
          </video>
        </div>
        <p><strong>Name:</strong> ${file.name}</p>

        <div class="progress-bar" style="display: none;">
          <div class="progress-fill"></div>
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
      const fileSizeGB = (file.size / (1024 * 1024 * 1024)).toFixed(2);

      // Determine upload method for display
      const uploadMethod =
        file.size > 5 * 1024 * 1024 ? "Multipart" : "Single-part";
      uploadButton.textContent = `Uploading... (0%) - ${fileSizeMB}MB (${uploadMethod})`;

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

          if (file.size > 100 * 1024 * 1024) {
            // Show GB for files > 100MB
            uploadButton.textContent = `Uploading... (${progress.toFixed(
              0
            )}%) - ${uploadedGB}GB/${fileSizeGB}GB (${uploadMethod})`;
          } else {
            uploadButton.textContent = `Uploading... (${progress.toFixed(
              0
            )}%) - ${uploadedMB}MB/${fileSizeMB}MB (${uploadMethod})`;
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
    } catch {
      alert(`An error occurred: ${error.message}`);
      uploadButton.textContent = "Upload Clip";
      uploadButton.disabled = false;
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

  async function uploadFileToS3Multipart(uploadURL, file, onProgress) {
    const CHUNK_SIZE = 100 * 1024 * 1024; // 100MB chunks for large files
    const MAX_CONCURRENT_CHUNKS = 10; // 10 concurrent uploads for large files

    try {
      // Parse the presigned URL to get bucket and key
      const url = new URL(uploadURL);
      const bucket = url.hostname.split(".")[0];
      const key = url.pathname.substring(1); // Remove leading slash

      // Log upload details for large files
      const fileSizeGB = (file.size / (1024 * 1024 * 1024)).toFixed(2);
      const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
      console.log(
        `Starting multipart upload: ${fileSizeGB}GB, ${totalChunks} chunks, ${
          CHUNK_SIZE / (1024 * 1024)
        }MB chunks`
      );

      // Create multipart upload
      const createMultipartResponse = await fetch(
        "/api/s3/create-multipart-upload/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify({
            bucket: bucket,
            key: key,
            content_type: file.type,
          }),
        }
      );

      if (!createMultipartResponse.ok) {
        throw new Error("Failed to create multipart upload");
      }

      const { upload_id } = await createMultipartResponse.json();

      // Calculate chunks
      const parts = [];
      let completedChunks = 0;

      // Upload chunks in parallel with limited concurrency
      const uploadChunk = async (chunkIndex) => {
        const start = chunkIndex * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, file.size);
        const chunk = file.slice(start, end);

        // Get presigned URL for this part
        const partResponse = await fetch("/api/s3/get-upload-part-url/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify({
            bucket: bucket,
            key: key,
            upload_id: upload_id,
            part_number: chunkIndex + 1,
          }),
        });

        if (!partResponse.ok) {
          throw new Error(
            `Failed to get presigned URL for part ${chunkIndex + 1}`
          );
        }

        const { presigned_url } = await partResponse.json();

        // Upload the chunk
        const uploadResponse = await fetch(presigned_url, {
          method: "PUT",
          body: chunk,
        });

        if (!uploadResponse.ok) {
          throw new Error(`Failed to upload part ${chunkIndex + 1}`);
        }

        const etag = uploadResponse.headers.get("ETag");
        return {
          PartNumber: chunkIndex + 1,
          ETag: etag,
        };
      };

      // Upload chunks with limited concurrency
      for (let i = 0; i < totalChunks; i += MAX_CONCURRENT_CHUNKS) {
        const chunkPromises = [];
        for (let j = 0; j < MAX_CONCURRENT_CHUNKS && i + j < totalChunks; j++) {
          chunkPromises.push(uploadChunk(i + j));
        }

        const chunkResults = await Promise.all(chunkPromises);
        parts.push(...chunkResults);

        completedChunks += chunkResults.length;
        const progress = (completedChunks / totalChunks) * 100;
        onProgress(progress);

        // Log progress for large files
        if (totalChunks > 10) {
          console.log(
            `Upload progress: ${progress.toFixed(
              1
            )}% (${completedChunks}/${totalChunks} chunks completed)`
          );
        }
      }

      // Complete multipart upload
      console.log(`Completing multipart upload with ${parts.length} parts`);
      const completeResponse = await fetch(
        "/api/s3/complete-multipart-upload/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify({
            bucket: bucket,
            key: key,
            upload_id: upload_id,
            parts: parts,
          }),
        }
      );

      if (!completeResponse.ok) {
        throw new Error("Failed to complete multipart upload");
      }

      console.log(`Multipart upload completed successfully: ${fileSizeGB}GB`);

      // Return a mock response object to maintain compatibility
      return {
        status: 200,
        responseText: "Multipart upload completed successfully",
      };
    } catch (error) {
      console.error("Multipart upload failed:", error);
      throw error;
    }
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
