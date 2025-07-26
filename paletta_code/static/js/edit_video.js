document.addEventListener("DOMContentLoaded", function () {
  // Handle thumbnail preview
  const thumbnailInput = document.getElementById("thumbnailUpload");
  const thumbnailPreview = document.getElementById("videoThumbnail");

  if (thumbnailInput && thumbnailPreview) {
    thumbnailInput.addEventListener("change", function () {
      if (this.files && this.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
          thumbnailPreview.src = e.target.result;
        };
        reader.readAsDataURL(this.files[0]);
      }
    });
  }

  // Handle publish toggle
  const publishToggle = document.getElementById("isPublished");
  const publishStatus = document.querySelector(".toggle-text");

  if (publishToggle && publishStatus) {
    publishToggle.addEventListener("change", function () {
      publishStatus.textContent = this.checked ? "Published" : "Not Published";
    });
  }

  // Tags management
  const tagsContainer = document.getElementById("tagsContainer");
  const tagInput = document.getElementById("tagInput");
  const addTagBtn = document.getElementById("addTagBtn");
  const tagsDataInput = document.getElementById("tagsData");
  const tagSuggestions = document.getElementById("tagSuggestions");
  let currentTags = [];

  // Initialize currentTags from existing tags
  if (tagsContainer) {
    document.querySelectorAll(".tag-item").forEach((tag) => {
      currentTags.push({
        id: tag.getAttribute("data-id"),
        name: tag.textContent.trim(),
      });
    });
    updateTagsData();
  }

  // Add tag function
  function addTag(tagName, tagId = null) {
    if (!tagName.trim()) return;

    // Check if tag already exists
    if (
      currentTags.some(
        (tag) => tag.name.toLowerCase() === tagName.toLowerCase()
      )
    ) {
      showToast("Tag already exists");
      return;
    }

    // Create tag element
    const tagElement = document.createElement("span");
    tagElement.className = "tag-item";
    if (tagId) tagElement.setAttribute("data-id", tagId);

    tagElement.innerHTML = `
            ${tagName}
            <button type="button" class="tag-remove" onclick="removeTag(this.parentElement)">×</button>
        `;

    // Add to DOM and current tags
    tagsContainer.appendChild(tagElement);
    currentTags.push({
      id: tagId,
      name: tagName,
    });

    // Update hidden input
    updateTagsData();

    // Clear input
    tagInput.value = "";
  }

  // Remove tag function
  window.removeTag = function (tagElement) {
    const tagId = tagElement.getAttribute("data-id");
    const tagName = tagElement.textContent.trim();

    // Remove from current tags
    currentTags = currentTags.filter((tag) => {
      if (tagId) return tag.id !== tagId;
      return tag.name !== tagName;
    });

    // Remove from DOM
    tagElement.remove();

    // Update hidden input
    updateTagsData();
  };

  // Update tags data
  function updateTagsData() {
    tagsDataInput.value = JSON.stringify(currentTags);
  }

  // Add tag event listeners
  if (addTagBtn && tagInput) {
    addTagBtn.addEventListener("click", function () {
      addTag(tagInput.value);
    });

    tagInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        addTag(this.value);
      }
    });

    // Tag search/suggestion feature
    tagInput.addEventListener("input", function () {
      const query = this.value.trim();
      if (query.length < 2) {
        tagSuggestions.style.display = "none";
        return;
      }

      // Fetch tag suggestions (replace with actual API endpoint)
      fetch(`/api/tag-suggestions/?query=${encodeURIComponent(query)}`)
        .then((response) => response.json())
        .then((data) => {
          if (data.tags && data.tags.length > 0) {
            // Populate suggestions
            tagSuggestions.innerHTML = "";
            data.tags.forEach((tag) => {
              const item = document.createElement("div");
              item.className = "tag-suggestion-item";
              item.textContent = tag.name;
              item.addEventListener("click", function () {
                addTag(tag.name, tag.id);
                tagSuggestions.style.display = "none";
                tagInput.value = "";
              });
              tagSuggestions.appendChild(item);
            });

            // Position and show suggestions
            const inputRect = tagInput.getBoundingClientRect();
            tagSuggestions.style.top = `${inputRect.bottom + window.scrollY}px`;
            tagSuggestions.style.left = `${inputRect.left + window.scrollX}px`;
            tagSuggestions.style.display = "block";
          } else {
            tagSuggestions.style.display = "none";
          }
        })
        .catch((error) => {
          console.error("Error fetching tag suggestions:", error);
          tagSuggestions.style.display = "none";
        });
    });

    // Close suggestions when clicking outside
    document.addEventListener("click", function (e) {
      if (!tagInput.contains(e.target) && !tagSuggestions.contains(e.target)) {
        tagSuggestions.style.display = "none";
      }
    });
  }

  // Form submission
  const editForm = document.getElementById("editVideoForm");
  if (editForm) {
    editForm.addEventListener("submit", function (e) {
      e.preventDefault();

      // Validate form
      const title = document.getElementById("videoTitle").value.trim();
      if (!title) {
        showToast("Title is required");
        return;
      }

      // Update tags data before submission
      updateTagsData();

      // Submit form
      const formData = new FormData(this);
      fetch(window.location.pathname, {
        method: "POST",
        body: formData,
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            showToast("Video updated successfully");

            // Redirect after a short delay
            setTimeout(() => {
              window.location.href = data.redirect_url || "/upload-history/";
            }, 1500);
          } else {
            showToast(`Error: ${data.message || "Failed to update video"}`);

            // Show field errors if any
            if (data.errors) {
              Object.keys(data.errors).forEach((field) => {
                const element = document.getElementById(
                  `video${field.charAt(0).toUpperCase() + field.slice(1)}`
                );
                if (element) {
                  element.classList.add("error");

                  // Add error message if not already present
                  const errorElement = document.createElement("p");
                  errorElement.className = "error-text";
                  errorElement.textContent = data.errors[field][0];

                  const formGroup = element.closest(".form-group");
                  const existingError = formGroup.querySelector(".error-text");
                  if (existingError) {
                    existingError.textContent = data.errors[field][0];
                  } else {
                    formGroup.appendChild(errorElement);
                  }
                }
              });
            }
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          showToast("An error occurred while updating the video");
        });
    });
  }

  // Toast notification function
  function showToast(message) {
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    document.body.appendChild(toast);

    // Show toast
    setTimeout(() => {
      toast.classList.add("show");

      // Hide and remove toast after 3 seconds
      setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => {
          toast.remove();
        }, 300);
      }, 3000);
    }, 100);
  }
});
