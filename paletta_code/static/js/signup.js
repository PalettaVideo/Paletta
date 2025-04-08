import {
  updatePasswordRequirements,
  initialisePasswordValidation,
} from "./passwordVerification.js";

document.addEventListener("DOMContentLoaded", function () {
  // initialise password validation if the elements exist
  if (document.getElementById("password")) {
    initialisePasswordValidation();
  }

  // toggle password visibility
  document.querySelectorAll(".toggle-password").forEach((button) => {
    button.addEventListener("click", function () {
      const targetId = this.getAttribute("data-target");
      const targetInput = document.getElementById(targetId);
      if (targetInput) {
        if (targetInput.type === "password") {
          targetInput.type = "text";
          this.textContent = "Hide";
        } else {
          targetInput.type = "password";
          this.textContent = "Show";
        }
      }
    });
  });

  // enable/disable company name input based on checkbox selection
  const companyCheckbox = document.getElementById("company");
  const companyInput = document.getElementById("company-input");

  if (companyCheckbox && companyInput) {
    companyCheckbox.addEventListener("change", function () {
      companyInput.disabled = !this.checked;
      companyInput.required = this.checked;
    });
  }

  // update password requirements for real-time password validation
  const passwordInput = document.getElementById("password");
  if (passwordInput) {
    passwordInput.addEventListener("input", function () {
      updatePasswordRequirements(this.value);
    });
  }

  // add password confirmation validation
  const confirmPasswordInput = document.getElementById("confirm-password");
  const passwordMatch = document.getElementById("password-match");

  if (confirmPasswordInput && passwordInput) {
    confirmPasswordInput.addEventListener("input", function () {
      const password = passwordInput.value;
      const confirmPassword = this.value;

      if (passwordMatch) {
        if (password === confirmPassword) {
          passwordMatch.textContent = "Passwords match";
          passwordMatch.style.color = "green";
        } else {
          passwordMatch.textContent = "Passwords do not match";
          passwordMatch.style.color = "red";
        }
      }
    });
  }

  // form submission validation
  const signupForm = document.querySelector(".signup-form");
  if (signupForm) {
    signupForm.addEventListener("submit", function (event) {
      // get form elements
      const email = document.getElementById("email");
      const firstName = document.getElementById("first_name");
      const lastName = document.getElementById("last_name");
      const password = document.getElementById("password");
      const confirmPassword = document.getElementById("confirm-password");
      const institution = document.getElementById("institution");

      // check if required elements exist and are filled
      let isValid = true;
      let errorMessage = "";

      if (!email || !email.value.trim()) {
        isValid = false;
        errorMessage = "Email is required";
      } else if (!firstName || !firstName.value.trim()) {
        isValid = false;
        errorMessage = "First name is required";
      } else if (!lastName || !lastName.value.trim()) {
        isValid = false;
        errorMessage = "Last name is required";
      } else if (!password || !password.value) {
        isValid = false;
        errorMessage = "Password is required";
      } else if (!confirmPassword || !confirmPassword.value) {
        isValid = false;
        errorMessage = "Please confirm your password";
      } else if (password.value !== confirmPassword.value) {
        isValid = false;
        errorMessage = "Passwords do not match";
      } else if (!institution || institution.value === "") {
        isValid = false;
        errorMessage = "Please select an institution";
      }

      // check if company checkbox is checked and company input is filled
      if (companyCheckbox && companyCheckbox.checked) {
        if (!companyInput || !companyInput.value.trim()) {
          isValid = false;
          errorMessage = "Company name is required";
        }
      }

      // if validation fails, prevent form submission and show error
      if (!isValid) {
        event.preventDefault();
        const errorElement = document.getElementById("password-error");
        if (errorElement) {
          errorElement.textContent = errorMessage;
          errorElement.style.display = "block";
        } else {
          alert(errorMessage);
        }
      }
    });
  }
});
