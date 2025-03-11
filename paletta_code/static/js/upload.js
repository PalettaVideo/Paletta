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
  let selectedTags = [];

  // fetch categories from API
  fetchCategories();

  // event Listeners
  if (selectFileBtn) {
    selectFileBtn.addEventListener("click", function (e) {
      e.preventDefault();
      fileInput.click();
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", handleVideoFileSelect);
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

    // check file size
    if (file.size > MAX_FILE_SIZE) {
      alert("File is too large. Maximum size is 300MB.");
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

    // try to extract video metadata
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
    // TODO: what is meant by client-side approximation?? what part of the process can be done on the server side?
    const video = document.createElement("video");
    video.preload = "metadata";
    video.onloadedmetadata = function () {
      // update duration field if it exists
      const durationInput = document.querySelector(
        '.attribute-group input[placeholder="Duration"]'
      );
      if (durationInput) {
        const duration = Math.round(video.duration);
        const minutes = Math.floor(duration / 60);
        const seconds = duration % 60;
        durationInput.value = `${minutes}:${seconds
          .toString()
          .padStart(2, "0")}`;
      }

      // update format field if it exists
      const formatInput = document.querySelector(
        '.attribute-group input[placeholder="Format"]'
      );
      if (formatInput) {
        const format = file.name.split(".").pop().toUpperCase();
        formatInput.value = format;
      }

      URL.revokeObjectURL(video.src);
    };
    video.src = URL.createObjectURL(file);
  }

  async function fetchCategories() {
    try {
      const response = await fetch("/api/videos/categories/");
      if (!response.ok) throw new Error("Failed to fetch categories");

      const categories = await response.json();
      const categorySelect = document.getElementById("category");

      if (
        categorySelect &&
        categories.results &&
        categories.results.length > 0
      ) {
        // clear existing options
        categorySelect.innerHTML = "";

        // add empty option
        const emptyOption = document.createElement("option");
        emptyOption.value = "";
        emptyOption.textContent = "Select a category";
        categorySelect.appendChild(emptyOption);

        // add categories from API
        categories.results.forEach((category) => {
          const option = document.createElement("option");
          option.value = category.id;
          option.textContent = category.name;
          categorySelect.appendChild(option);
        });
      }
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  }

  async function handleFormSubmit(e) {
    e.preventDefault();

    // validate form
    if (!validateForm()) {
      return;
    }

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

    try {
      // show loading state
      const uploadButton = document.getElementById("upload-button");
      const originalText = uploadButton.textContent;
      uploadButton.textContent = "Uploading...";
      uploadButton.disabled = true;

      // send request
      const response = await fetch("/api/videos/api/upload/", {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
        },
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.message || "Upload failed");
      }

      // success - redirect to history page
      alert("Video uploaded successfully!");
      window.location.href = "/upload/history/";
    } catch (error) {
      alert("Error uploading video: " + error.message);

      // reset button
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
