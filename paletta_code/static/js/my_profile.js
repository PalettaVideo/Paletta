import {
  validatePassword,
  updatePasswordRequirements,
  initialisePasswordValidation,
} from "./passwordVerification.js";

// initialise password validation for real-time password validation
document.addEventListener("DOMContentLoaded", initialisePasswordValidation);

// load the user data and populate the profile
document.addEventListener("DOMContentLoaded", async () => {
  try {
    const token = localStorage.getItem("access_token");
    const response = await fetch("/users/me", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!response.ok) {
      console.error("Response status:", response.status);
      throw new Error("Failed to fetch user data");
    }

    const userData = await response.json();
    populateProfile(userData);
  } catch (error) {
    console.error("Error fetching user data:", error);
    alert("Failed to load user profile.");
  }

  togglePasswordVisibility("password-input", "toggle-password");
  togglePasswordVisibility("confirm-password-input", "toggle-confirm-password");
});

function populateProfile(user) {
  // populate the display fields with the user data
  document.getElementById("email-display").innerText = user.email;
  document.getElementById("name-display").innerText = user.username;
  document.getElementById("institution-display").innerText = user.institution;
  document.getElementById("company-display").innerText = user.company;

  // populate the input fields with the user data
  document.getElementById("email-input").value = user.email;
  document.getElementById("name-input").value = user.username;
  // no change of institution for now, requirements are to be discussed in future
  // document.getElementById("institution-input").value = user.institution;
  document.getElementById("company-input").value = user.company;
}

// enable the edit model when the button is clicked
window.enableEdit = function enableEdit() {
  document.getElementById("view-mode").style.display = "none";
  document.getElementById("edit-mode").style.display = "block";
};

// event listener for password change checkbox
const passwordChangeCheckbox = document.getElementById(
  "password-change-checkbox"
);
const passwordFields = document.getElementById("password-fields");

passwordChangeCheckbox.addEventListener("change", function () {
  if (this.checked) {
    passwordFields.style.display = "block";
    document.getElementById("message").style.display = "block";
  } else {
    passwordFields.style.display = "none";
    document.getElementById("message").style.display = "none";
  }
});

// event listeners for password validation
const passwordInput = document.getElementById("password-input");
passwordInput.addEventListener("input", function () {
  updatePasswordRequirements(this.value);
});

// saves the changes to the profile and updates the user data
window.saveChanges = function saveChanges() {
  const email = document.getElementById("email-input").value;
  const name = document.getElementById("name-input").value;
  const company = document.getElementById("company-input").value;
  const institution = document.getElementById("institution-display").innerText;

  const token = localStorage.getItem("access_token");

  const body = {
    email,
    username: name,
    company,
    institution,
  };

  if (passwordChangeCheckbox.checked) {
    const password = passwordInput.value;
    const confirmPassword = document.getElementById(
      "confirm-password-input"
    ).value;

    if (password !== confirmPassword) {
      alert("Passwords do not match!");
      return;
    }

    const strength = validatePassword(password).strength;
    if (strength !== "Medium" && strength !== "Strong") {
      alert(
        "Your password must be at least Medium strength to update your profile."
      );
      return;
    }

    body.password = password;
  }
  // send the PUT request to the server to update the profile
  fetch("/users/me", {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  })
    .then((response) => {
      if (!response.ok) {
        // log the response status and text for debugging
        console.error("Response status:", response.status);
        return response.text().then((text) => {
          console.error("Response text:", text);
          throw new Error("Failed to update profile");
        });
      }
      return response.json();
    })
    .then((updatedUser) => {
      // update the user data and populate the profile
      populateProfile(updatedUser);
      document.getElementById("view-mode").style.display = "block";
      document.getElementById("edit-mode").style.display = "none";

      // if the password was changed, log out the user
      if (passwordChangeCheckbox.checked) {
        // remove the access token from local storage
        localStorage.removeItem("access_token");
        // redirect to the login page
        window.location.href = "/";
      }
    })
    .catch((error) => {
      // log any errors for debugging
      console.error("Error updating profile:", error);
      alert("Failed to update profile.");
    });
};

// function to toggle password visibility
function togglePasswordVisibility(inputId, buttonId) {
  const input = document.getElementById(inputId);
  const button = document.getElementById(buttonId);

  button.addEventListener("click", () => {
    if (input.type === "password") {
      input.type = "text";
      button.textContent = "Hide";
    } else {
      input.type = "password";
      button.textContent = "Show";
    }
  });
}
