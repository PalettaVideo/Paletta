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

  // Modal elements
  const confirmModal = document.getElementById("confirmModal");
  const confirmTitle = document.getElementById("confirmTitle");
  const confirmMessage = document.getElementById("confirmMessage");
  const confirmBtn = document.getElementById("confirmBtn");
  const cancelBtn = document.getElementById("cancelBtn");

  // Store the current action and library for the modal
  let currentAction = null;
  let currentLibraryId = null;
  let currentLibraryElement = null;

  // Library action buttons
  const stopButtons = document.querySelectorAll(".stop");
  const closeButtons = document.querySelectorAll(".close");

  // Add event listeners to stop buttons
  stopButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const libraryId = this.getAttribute("data-library-id");
      const libraryItem = this.closest(".library-item");
      const libraryName = libraryItem.querySelector("span").textContent;
      const isActive = this.textContent.trim() === "Stop";

      // Set current action and library
      currentAction = isActive ? "stop" : "start";
      currentLibraryId = libraryId;
      currentLibraryElement = libraryItem;

      // Update modal content
      confirmTitle.textContent = isActive ? "Stop Library" : "Start Library";
      confirmMessage.textContent = `Are you sure you want to ${
        isActive ? "stop" : "start"
      } the library "${libraryName}"?`;

      // Show modal
      confirmModal.style.display = "flex";
    });
  });

  // Add event listeners to close buttons
  closeButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const libraryId = this.getAttribute("data-library-id");
      const libraryItem = this.closest(".library-item");
      const libraryName = libraryItem.querySelector("span").textContent;

      // Set current action and library
      currentAction = "close";
      currentLibraryId = libraryId;
      currentLibraryElement = libraryItem;

      // Update modal content
      confirmTitle.textContent = "Close Library";
      confirmMessage.textContent = `Are you sure you want to close the library "${libraryName}"? This action cannot be undone.`;

      // Show modal
      confirmModal.style.display = "flex";
    });
  });

  // Confirm button action
  confirmBtn.addEventListener("click", function () {
    switch (currentAction) {
      case "stop":
        toggleLibraryStatus(currentLibraryId, false);
        break;
      case "start":
        toggleLibraryStatus(currentLibraryId, true);
        break;
      case "close":
        closeLibrary(currentLibraryId);
        break;
    }

    // Hide modal
    confirmModal.style.display = "none";
  });

  // Cancel button action
  cancelBtn.addEventListener("click", function () {
    confirmModal.style.display = "none";
  });

  // Close modal when clicking outside
  window.addEventListener("click", function (event) {
    if (event.target === confirmModal) {
      confirmModal.style.display = "none";
    }
  });

  // Function to toggle library status (active/inactive)
  function toggleLibraryStatus(libraryId, setActive) {
    fetch(`/libraries/${libraryId}/toggle-status/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify({
        active: setActive,
      }),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Server error");
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          // Update button text
          const stopButton = currentLibraryElement.querySelector(".stop");
          stopButton.innerHTML = `<i class="fas fa-pause"></i> ${
            setActive ? "Stop" : "Start"
          }`;

          // Flash a success message
          const statusMessage = document.createElement("div");
          statusMessage.classList.add("status-message", "success");
          statusMessage.textContent = `Library ${
            setActive ? "started" : "stopped"
          } successfully.`;
          document.querySelector("main").appendChild(statusMessage);

          // Remove the message after 3 seconds
          setTimeout(() => {
            statusMessage.remove();
          }, 3000);
        } else {
          showError(
            data.error || `Failed to ${setActive ? "start" : "stop"} library.`
          );
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        showError("An error occurred. Please try again.");
      });
  }

  // Function to close (delete) a library
  function closeLibrary(libraryId) {
    fetch(`/libraries/${libraryId}/close/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Server error");
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          // Remove library from DOM
          currentLibraryElement.remove();

          // If no more libraries, show "no libraries" message
          const libraryList = document.querySelector(".library-list");
          if (libraryList.children.length === 0) {
            const noLibraries = document.createElement("div");
            noLibraries.classList.add("no-libraries");
            noLibraries.innerHTML =
              '<p>No libraries found. <a href="/libraries/create/">Create a new library</a>.</p>';
            libraryList.appendChild(noLibraries);
          }

          // Flash a success message
          const statusMessage = document.createElement("div");
          statusMessage.classList.add("status-message", "success");
          statusMessage.textContent = "Library closed successfully.";
          document.querySelector("main").appendChild(statusMessage);

          // Remove the message after 3 seconds
          setTimeout(() => {
            statusMessage.remove();
          }, 3000);
        } else {
          showError(data.error || "Failed to close library.");
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        showError("An error occurred. Please try again.");
      });
  }

  // Function to show error messages
  function showError(message) {
    const errorMessage = document.createElement("div");
    errorMessage.classList.add("status-message", "error");
    errorMessage.textContent = message;
    document.querySelector("main").appendChild(errorMessage);

    // Remove the message after 5 seconds
    setTimeout(() => {
      errorMessage.remove();
    }, 5000);
  }
});
