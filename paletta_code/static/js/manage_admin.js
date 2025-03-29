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

  // Add CSRF token to all AJAX requests
  function setupAjaxCSRF() {
    $.ajaxSetup({
      beforeSend: function (xhr, settings) {
        if (
          !/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) &&
          !this.crossDomain
        ) {
          xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
      },
    });
  }

  // Set up AJAX to include CSRF token for fetch requests
  function fetchWithCSRF(url, options = {}) {
    const csrfToken = getCookie("csrftoken");
    const fetchOptions = {
      ...options,
      headers: {
        ...options.headers,
        "X-CSRFToken": csrfToken,
      },
    };
    return fetch(url, fetchOptions);
  }

  // Modal handling
  const modal = document.getElementById("adminModal");
  const addAdminBtn = document.getElementById("addAdmin");
  const closeModal = document.querySelector(".close");
  const closeBtn = document.querySelector(".close-btn");
  const confirmAddBtn = document.getElementById("confirmAdd");

  if (addAdminBtn) {
    addAdminBtn.addEventListener("click", function () {
      // Clear previous errors and form values
      document.getElementById("nameError").textContent = "";
      document.getElementById("emailError").textContent = "";
      document.getElementById("adminName").value = "";
      document.getElementById("adminEmail").value = "";
      document.getElementById("adminInstitution").value = "";

      modal.style.display = "flex";
    });
  }

  if (closeModal) {
    closeModal.addEventListener("click", function () {
      modal.style.display = "none";
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", function () {
      modal.style.display = "none";
    });
  }

  window.addEventListener("click", function (event) {
    if (event.target === modal) {
      modal.style.display = "none";
    }
  });

  // Handle adding a new administrator
  if (confirmAddBtn) {
    confirmAddBtn.addEventListener("click", function () {
      const name = document.getElementById("adminName").value.trim();
      const email = document.getElementById("adminEmail").value.trim();
      const institution = document
        .getElementById("adminInstitution")
        .value.trim();

      // Reset error messages
      document.getElementById("nameError").textContent = "";
      document.getElementById("emailError").textContent = "";

      // Validation
      let hasErrors = false;

      if (name === "") {
        document.getElementById("nameError").textContent = "Name is required";
        hasErrors = true;
      }

      if (email === "") {
        document.getElementById("emailError").textContent = "Email is required";
        hasErrors = true;
      } else if (!isValidEmail(email)) {
        document.getElementById("emailError").textContent =
          "Please enter a valid email";
        hasErrors = true;
      }

      if (hasErrors) {
        return;
      }

      // Prepare data for submission
      const formData = new FormData();
      formData.append("name", name);
      formData.append("email", email);
      if (institution) {
        formData.append("institution", institution);
      }
      formData.append("csrfmiddlewaretoken", csrftoken);

      // Submit via AJAX
      fetch("/add-administrator/", {
        method: "POST",
        body: formData,
        headers: {
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
            // Create new admin card and add to DOM
            addAdminToList(data.admin);
            modal.style.display = "none";

            // Clear form
            document.getElementById("adminName").value = "";
            document.getElementById("adminEmail").value = "";
            document.getElementById("adminInstitution").value = "";
          } else {
            // Handle validation errors from server
            if (data.errors.name) {
              document.getElementById("nameError").textContent =
                data.errors.name;
            }
            if (data.errors.email) {
              document.getElementById("emailError").textContent =
                data.errors.email;
            }
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          alert(
            "An error occurred while adding the administrator. Please try again."
          );
        });
    });
  }

  // Add revoke functionality
  document.querySelectorAll(".revoke").forEach((button) => {
    button.addEventListener("click", function () {
      const adminId = this.getAttribute("data-admin-id");
      const adminCard = this.closest(".admin-card");

      if (confirm("Are you sure you want to revoke admin privileges?")) {
        // Send revoke request
        fetch(`/revoke-administrator/${adminId}/`, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrftoken,
            "Content-Type": "application/json",
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
              // Remove admin card from DOM
              adminCard.remove();

              // If no more admins, show message
              if (document.querySelectorAll(".admin-card").length === 0) {
                const noAdmins = document.createElement("p");
                noAdmins.classList.add("no-admins");
                noAdmins.textContent = "No administrators found.";
                document.getElementById("adminList").appendChild(noAdmins);
              }
            } else {
              alert(data.message || "Failed to revoke admin privileges.");
            }
          })
          .catch((error) => {
            console.error("Error:", error);
            alert("An error occurred. Please try again.");
          });
      }
    });
  });

  // Helper function to validate email format
  function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }

  // Helper function to add a new admin to the DOM
  function addAdminToList(admin) {
    const adminList = document.getElementById("adminList");

    // Remove "no administrators" message if present
    const noAdminsMessage = adminList.querySelector(".no-admins");
    if (noAdminsMessage) {
      noAdminsMessage.remove();
    }

    const newAdmin = document.createElement("div");
    newAdmin.classList.add("admin-card");
    newAdmin.dataset.id = admin.id;

    const libraryNames =
      admin.libraries && admin.libraries.length > 0
        ? admin.libraries.join("; ")
        : "N/A";

    newAdmin.innerHTML = `
            <p><strong>Institution:</strong> ${
              admin.institution || "Not specified"
            }</p>
            <p><strong>Email:</strong> ${admin.email}</p>
            <p><strong>Name:</strong> ${admin.name}</p>
            <p><strong>Library Name:</strong> ${libraryNames}</p>
            <button class="revoke" data-admin-id="${
              admin.id
            }">Revoke Admin Privileges</button>
        `;

    adminList.appendChild(newAdmin);

    // Add event listener to new revoke button
    newAdmin.querySelector(".revoke").addEventListener("click", function () {
      const adminId = this.getAttribute("data-admin-id");
      const adminCard = this.closest(".admin-card");

      if (confirm("Are you sure you want to revoke admin privileges?")) {
        // Send revoke request
        fetch(`/revoke-administrator/${adminId}/`, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrftoken,
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
          },
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              adminCard.remove();

              // If no more admins, show message
              if (document.querySelectorAll(".admin-card").length === 0) {
                const noAdmins = document.createElement("p");
                noAdmins.classList.add("no-admins");
                noAdmins.textContent = "No administrators found.";
                document.getElementById("adminList").appendChild(noAdmins);
              }
            } else {
              alert(data.message || "Failed to revoke admin privileges.");
            }
          })
          .catch((error) => {
            console.error("Error:", error);
            alert("An error occurred. Please try again.");
          });
      }
    });
  }
});
