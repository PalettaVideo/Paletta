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
  const checkEmailBtn = document.getElementById("checkEmail");
  const confirmYesBtn = document.getElementById("confirmYes");
  const confirmNoBtn = document.getElementById("confirmNo");
  const confirmationSection = document.getElementById("confirmationSection");
  const initialActions = document.getElementById("initialActions");

  // State variables
  let currentUserData = null;

  if (addAdminBtn) {
    addAdminBtn.addEventListener("click", function () {
      // Clear previous errors and form values
      document.getElementById("emailError").textContent = "";
      document.getElementById("adminEmail").value = "";
      confirmationSection.style.display = "none";
      initialActions.style.display = "flex";

      modal.style.display = "flex";
    });
  }

  if (closeModal) {
    closeModal.addEventListener("click", function () {
      modal.style.display = "none";
      resetModalState();
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", function () {
      modal.style.display = "none";
      resetModalState();
    });
  }

  window.addEventListener("click", function (event) {
    if (event.target === modal) {
      modal.style.display = "none";
      resetModalState();
    }
  });

  // Reset modal state when closing
  function resetModalState() {
    document.getElementById("emailError").textContent = "";
    document.getElementById("adminEmail").value = "";
    confirmationSection.style.display = "none";
    initialActions.style.display = "flex";
    currentUserData = null;
  }

  // Check if email exists and user's role
  if (checkEmailBtn) {
    checkEmailBtn.addEventListener("click", function () {
      const email = document.getElementById("adminEmail").value.trim();
      document.getElementById("emailError").textContent = "";

      // Validate email format
      if (!email || !isValidEmail(email)) {
        document.getElementById("emailError").textContent =
          "Please enter a valid email address";
        return;
      }

      // Check if user exists
      fetch("/api/accounts/check-user/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
          "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({ email: email }),
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Server error");
          }
          return response.json();
        })
        .then((data) => {
          if (data.exists) {
            currentUserData = data.user;

            // Check if user is already an admin
            if (data.is_admin) {
              document.getElementById("emailError").textContent =
                "This user is already an administrator";
            } else {
              // Show confirmation dialog
              document.getElementById(
                "confirmationMessage"
              ).textContent = `User ${
                data.user.name || data.user.email
              } found. Would you like to promote them to Administrator?`;
              confirmationSection.style.display = "block";
              initialActions.style.display = "none";
            }
          } else {
            document.getElementById("emailError").textContent =
              "User with this email address does not exist in the system";
          }
        })
        .catch(() => {
          document.getElementById("emailError").textContent =
            "An error occurred while checking this email. Please try again.";
        });
    });
  }

  // Handle confirmation response
  if (confirmYesBtn) {
    confirmYesBtn.addEventListener("click", function () {
      if (!currentUserData) return;

      // Promote user to admin
      makeUserAdmin(currentUserData.id);
    });
  }

  if (confirmNoBtn) {
    confirmNoBtn.addEventListener("click", function () {
      // Reset and return to initial state
      resetModalState();
    });
  }

  // Function to promote user to admin
  function makeUserAdmin(userId) {
    fetch("/api/accounts/make-admin/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify({ user_id: userId }),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Server error");
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          // Add new admin to the list
          addAdminToList(data.admin);

          // Close modal
          modal.style.display = "none";
          resetModalState();
        } else {
          document.getElementById("emailError").textContent =
            data.message || "Failed to add administrator";
          confirmationSection.style.display = "none";
          initialActions.style.display = "flex";
        }
      })
      .catch(() => {
        document.getElementById("emailError").textContent =
          "An error occurred. Please try again.";
        confirmationSection.style.display = "none";
        initialActions.style.display = "flex";
      });
  }

  // Add revoke functionality
  document.querySelectorAll(".revoke").forEach((button) => {
    button.addEventListener("click", function () {
      const adminId = this.getAttribute("data-admin-id");
      const adminCard = this.closest(".admin-card");

      if (confirm("Are you sure you want to revoke admin privileges?")) {
        // Send revoke request
        fetch(`/api/accounts/revoke-administrator/${adminId}/`, {
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
          .catch(() => {
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
        <p><strong>Name:</strong> ${admin.name || admin.email}</p>
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
        fetch(`/api/accounts/revoke-administrator/${adminId}/`, {
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
          .catch(() => {
            alert("An error occurred. Please try again.");
          });
      }
    });
  }
});
