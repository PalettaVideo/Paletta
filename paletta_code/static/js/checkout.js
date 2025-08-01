document.addEventListener("DOMContentLoaded", function () {
  // Extract data from HTML
  const videoIds = [];
  const videoElements = document.querySelectorAll(".cart-item[data-video-id]");
  videoElements.forEach((element) => {
    const videoId = element.getAttribute("data-video-id");
    if (videoId) {
      videoIds.push(parseInt(videoId));
    }
  });

  const userEmail = document.getElementById("download-email").value || "";
  const csrfToken =
    document.querySelector("[name=csrfmiddlewaretoken]").value || "";

  // Set global variables for compatibility
  window.videoIds = videoIds;
  window.userEmail = userEmail;
  window.csrfToken = csrfToken;

  // Get elements
  const requestDownloadsBtn = document.getElementById("request-downloads");
  const emailInput = document.getElementById("download-email");
  const loadingIndicator = document.getElementById("loading-indicator");
  const successMessage = document.getElementById("success-message");
  const errorMessage = document.getElementById("error-message");
  const errorText = document.getElementById("error-text");

  // Validate email format
  function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  // Show loading state
  function showLoading() {
    requestDownloadsBtn.disabled = true;
    requestDownloadsBtn.innerText = "Submitting Request...";
    loadingIndicator.style.display = "block";
    successMessage.style.display = "none";
    errorMessage.style.display = "none";
  }

  // Hide loading state
  function hideLoading() {
    requestDownloadsBtn.disabled = false;
    requestDownloadsBtn.innerText = "Submit Video Request";
    loadingIndicator.style.display = "none";
  }

  // Show success message
  function showSuccess(message) {
    successMessage.style.display = "block";
    successMessage.innerHTML = `<strong>Success!</strong> ${message}`;

    // Hide success message after 10 seconds
    setTimeout(() => {
      successMessage.style.display = "none";
    }, 10000);
  }

  // Show error message
  function showError(message) {
    errorMessage.style.display = "block";
    errorText.textContent = message;

    // Hide error message after 10 seconds
    setTimeout(() => {
      errorMessage.style.display = "none";
    }, 10000);
  }

  // Handle download request
  function handleDownloadRequest() {
    const email = emailInput.value.trim();

    // Validate email
    if (!email) {
      showError("Please enter an email address");
      return;
    }

    if (!isValidEmail(email)) {
      showError("Please enter a valid email address");
      return;
    }

    // Check if video IDs are available
    if (!window.videoIds || window.videoIds.length === 0) {
      showError("No videos selected for request");
      return;
    }

    // Show loading state
    showLoading();

    // Prepare request data
    const requestData = {
      video_ids: window.videoIds,
      email: email,
    };

    // Make API request
    fetch("/api/orders/bulk-download-request/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": window.csrfToken,
      },
      body: JSON.stringify(requestData),
    })
      .then((response) => response.json())
      .then((data) => {
        hideLoading();

        if (data.success) {
          const message = `Your video request has been submitted successfully! 
                          ${data.successful_count} of ${data.total_count} videos submitted for review.
                          Our FilmBright team will contact you at ${email} to discuss licensing and pricing.`;
          showSuccess(message);

          // Optional: Redirect to orders page after 5 seconds
          setTimeout(() => {
            window.location.href = "/orders/";
          }, 5000);
        } else {
          let errorMsg = data.message || "Failed to submit video request";

          // Show specific errors if available
          if (data.results && data.results.length > 0) {
            const failedVideos = data.results.filter((r) => !r.success);
            if (failedVideos.length > 0) {
              errorMsg += `\n\nFailed videos:\n${failedVideos
                .map((v) => `- ${v.video_title || "Unknown"}: ${v.error}`)
                .join("\n")}`;
            }
          }

          showError(errorMsg);
        }
      })
      .catch(() => {
        hideLoading();
        showError(
          "An error occurred while submitting your video request. Please try again."
        );
      });
  }

  // Add event listener to download button
  if (requestDownloadsBtn) {
    requestDownloadsBtn.addEventListener("click", handleDownloadRequest);
  }

  // Add event listener to email input for Enter key
  if (emailInput) {
    emailInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        handleDownloadRequest();
      }
    });
  }

  // Email validation on input
  if (emailInput) {
    emailInput.addEventListener("input", function () {
      const email = this.value.trim();
      if (email && !isValidEmail(email)) {
        this.style.borderColor = "#dc3545";
      } else {
        this.style.borderColor = "#ddd";
      }
    });
  }
});
