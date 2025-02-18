import {
  validatePassword,
  updatePasswordRequirements,
  initialisePasswordValidation,
} from "./passwordVerification.js";

// initialise password validation for real-time password validation
document.addEventListener("DOMContentLoaded", initialisePasswordValidation);

// toggle password visibility
document.querySelectorAll(".toggle-password").forEach((button) => {
  button.addEventListener("click", function () {
    const targetId = this.getAttribute("data-target");
    const targetInput = document.getElementById(targetId);
    if (targetInput.type === "password") {
      targetInput.type = "text";
      this.textContent = "Hide";
    } else {
      targetInput.type = "password";
      this.textContent = "Show";
    }
  });
});

// enable/disable company name input based on checkbox selection
document.getElementById("company").addEventListener("change", function () {
  const companyInput = document.getElementById("company-input");
  companyInput.disabled = !this.checked;
  companyInput.required = this.checked;
});

// form submission logic
document
  .querySelector(".signup-form")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    // get the values of the form fields
    const email = document.getElementById("email").value.trim();
    const name = document.getElementById("name").value.trim();
    const password = document.getElementById("password").value.trim();
    const confirmPassword = document
      .getElementById("confirm-password")
      .value.trim();
    const institution = document.getElementById("institution").value;
    const companyCheckbox = document.getElementById("company");
    const company = companyCheckbox.checked
      ? document.getElementById("company-input").value.trim()
      : "";

    // check if all required fields are filled
    if (!email || !name || !password || !confirmPassword) {
      alert("Please fill in all required fields.");
      return;
    }

    // check if the passwords match
    if (password !== confirmPassword) {
      alert("Passwords do not match!");
      return;
    }

    // check if the password is strong enough
    const strength = validatePassword(password).strength;
    if (strength !== "Medium" && strength !== "Strong") {
      alert(
        "Your password must be at least Medium strength to create an account."
      );
      return;
    }

    // check if the institution is selected
    if (!institution) {
      alert("Please select an institution.");
      return;
    }

    // check if the company name is entered if the company checkbox is checked
    if (companyCheckbox.checked && !company) {
      alert("Please enter the company name.");
      return;
    }

    // send the POST request to the server to create the user
    try {
      const response = await fetch("http://127.0.0.1:8000/users", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email,
          password: password,
          role: "customer",
          username: name,
          institution: institution,
          company: company,
        }),
      });

      if (response.ok) {
        alert("User created successfully! Please log in to continue.");
        window.location.href = "/";
      } else {
        const errorData = await response.json();
        console.error("Error data:", errorData);
        alert(`Failed to create user: ${JSON.stringify(errorData)}`);
      }
    } catch (error) {
      console.error("Error:", error);
      alert("An error occurred while creating the user.");
    }
  });

// update password requirements for real-time password validation
document.getElementById("password").addEventListener("input", function () {
  updatePasswordRequirements(this.value);
});
