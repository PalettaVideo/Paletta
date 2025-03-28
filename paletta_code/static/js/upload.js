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
      updateWordCount(this, titleWordCount, 25);
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
    fetch("/api/videos/api/extract-metadata/", {
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
      const apiUrl = "/api/videos/categories/";
      console.log("Fetching categories from:", apiUrl);

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

      if (categories.length > 0) {
        // clear existing options
        categorySelect.innerHTML = "";

        // add empty option
        const emptyOption = document.createElement("option");
        emptyOption.value = "";
        emptyOption.textContent = "Select a category";
        categorySelect.appendChild(emptyOption);

        // add categories from API
        categories.forEach((category) => {
          const option = document.createElement("option");
          // Handle both possible property names
          option.value = category.id || category.pk || "";
          option.textContent = category.name || category.title || "";
          categorySelect.appendChild(option);
        });

        console.log("Categories loaded successfully:", categories.length);
      } else {
        console.warn("No categories found in the response");
        console.log("categorySelect:", categorySelect);
        console.log("categories:", categories);
      }
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  }

  async function handleFormSubmit(e) {
    e.preventDefault();
    console.log("Form submission started");

    // validate form
    if (!validateForm()) {
      return;
    }

    console.log("Form validation passed");

    // create FormData object
    const formData = new FormData();
    formData.append("title", titleInput.value.trim());
    formData.append("description", descriptionInput.value.trim());
    formData.append("category", document.getElementById("category").value);
    formData.append("video_file", fileInput.files[0]);

    if (previewImageInput.files[0]) {
      formData.append("thumbnail", previewImageInput.files[0]);
    }

    if (selectedTags.length > 0) {
      formData.append("tags", selectedTags.join(","));
    }

    // get CSRF token
    const csrfToken = getCookie("csrftoken");
    console.log("Submitting form to API...");

    try {
      // show loading state
      const uploadButton = document.getElementById("upload-button");
      const originalText = uploadButton.textContent;
      uploadButton.textContent = "Uploading...";
      uploadButton.disabled = true;

      // Create and show progress elements
      const progressContainer = document.createElement("div");
      progressContainer.className = "upload-progress-container";
      progressContainer.style.display = "block";

      const progressBar = document.createElement("div");
      progressBar.className = "upload-progress-bar";
      progressContainer.appendChild(progressBar);

      const progressText = document.createElement("div");
      progressText.className = "upload-progress-text";
      progressText.textContent = "Preparing upload...";

      // Add progress elements to the video preview container instead of before the button
      const videoPreviewContainer = document.getElementById(
        "video-preview-container"
      );
      videoPreviewContainer.appendChild(progressContainer);
      videoPreviewContainer.appendChild(progressText);

      // Create XMLHttpRequest for progress monitoring
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener("progress", (event) => {
        if (event.lengthComputable) {
          const percentComplete = Math.round(
            (event.loaded / event.total) * 100
          );
          progressBar.style.width = percentComplete + "%";
          progressText.textContent = `Uploading: ${percentComplete}%`;
          console.log(`Upload progress: ${percentComplete}%`);
        }
      });

      xhr.addEventListener("load", () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            let result;
            // Check if we have a response before parsing
            if (xhr.responseText && xhr.responseText.trim()) {
              try {
                result = JSON.parse(xhr.responseText);
                console.log("Upload response data (parsed JSON):", result);
              } catch (parseError) {
                console.error("JSON parse error:", parseError);
                console.log("Raw response text:", xhr.responseText);

                // Even without proper JSON, if status is 200-299, we consider it success
                result = {
                  success: true,
                  message: "Upload appears successful (non-JSON response)",
                };
              }
            } else {
              // Empty response with success status - assume success
              console.log("Empty but successful response");
              result = {
                success: true,
                message: "Upload successful (empty response)",
              };
            }

            if (!result.success) {
              throw new Error(result.message || "Upload failed");
            }

            // Update progress UI
            progressBar.style.width = "100%";
            progressText.textContent = "Upload complete! Redirecting...";

            // Success - redirect to history page
            setTimeout(() => {
              alert("Video uploaded successfully!");
              window.location.href = "/upload/history/";
            }, 1000);
          } catch (error) {
            handleUploadError(error);
          }
        } else {
          // Non-success status code
          let errorMessage = "Upload failed with status: " + xhr.status;
          try {
            if (xhr.responseText) {
              const errorData = JSON.parse(xhr.responseText);
              if (errorData.message) {
                errorMessage = errorData.message;
              }
            }
          } catch (e) {
            // If we can't parse the error response, use default message
            console.error("Couldn't parse error response:", e);
          }

          handleUploadError(new Error(errorMessage));
        }
      });

      xhr.addEventListener("error", () => {
        handleUploadError(new Error("Network error during upload"));
      });

      xhr.addEventListener("abort", () => {
        handleUploadError(new Error("Upload was aborted"));
      });

      // Open and send the request
      xhr.open("POST", "/api/videos/upload/", true);
      xhr.setRequestHeader("X-CSRFToken", csrfToken);
      xhr.send(formData);

      // Helper function for handling errors
      function handleUploadError(error) {
        alert("Error uploading video: " + error.message);
        console.error("Upload error:", error);

        // Reset UI
        progressBar.style.width = "0%";
        progressText.textContent = "Upload failed";
        progressText.style.color = "#d9534f";

        // Reset button
        uploadButton.textContent = originalText;
        uploadButton.disabled = false;
      }
    } catch (error) {
      console.error("Exception during upload:", error);
      alert("Error uploading video: " + error.message);
      uploadButton.textContent = originalText;
      uploadButton.disabled = false;
    }
  }

  function validateForm() {
    // check required fields
    if (!fileInput.files[0]) {
      alert("Please select a video file");
      return false;
    }

    if (!titleInput.value.trim()) {
      alert("Please enter a title");
      titleInput.focus();
      return false;
    }

    if (!document.getElementById("category").value) {
      alert("Please select a category");
      return false;
    }

    // check word limits
    const titleWords = titleInput.value
      .trim()
      .split(/\s+/)
      .filter(Boolean).length;
    if (titleWords > 25) {
      alert("Title exceeds maximum word count (25)");
      titleInput.focus();
      return false;
    }

    const descriptionWords = descriptionInput.value
      .trim()
      .split(/\s+/)
      .filter(Boolean).length;
    if (descriptionWords > 100) {
      alert("Description exceeds maximum word count (100)");
      descriptionInput.focus();
      return false;
    }

    return true;
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