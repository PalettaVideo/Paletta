import {
  validatePassword,
  updatePasswordRequirements,
  initialisePasswordValidation,
} from "./passwordVerification.js";

/**
 * Helper function to interact with DOM elements
 */
const DOM = {
  // get element by ID
  get: (id) => document.getElementById(id),

  // get element value
  getValue: (id, defaultValue = "") => {
    const element = document.getElementById(id);
    return element ? element.value : defaultValue;
  },

  // get element text
  getText: (id, defaultValue = "") => {
    const element = document.getElementById(id);
    return element ? element.innerText : defaultValue;
  },

  // update element text
  setText: (id, value) => {
    const element = document.getElementById(id);
    if (element) {
      element.innerText = value || "";
    } else {
      console.warn(`Element with ID '${id}' not found`);
    }
  },

  // update input value
  setValue: (id, value) => {
    const element = document.getElementById(id);
    if (element) {
      element.value = value || "";
    } else {
      console.warn(`Input element with ID '${id}' not found`);
    }
  },

  // set display style
  setDisplay: (id, display) => {
    const element = document.getElementById(id);
    if (element) {
      element.style.display = display;
    }
  },
};

function getUserData() {
  try {
    const userDataElement = document.getElementById("user-data");
    if (!userDataElement) {
      throw new Error("User data element not found");
    }
    return JSON.parse(userDataElement.textContent);
  } catch {
    return null;
  }
}

/**
 * Initialise all event listeners and setup
 */
function initializeProfile() {
  // initialise password validation
  initialisePasswordValidation();

  // load user data
  try {
    const userData = getUserData();
    if (userData) {
      populateProfile(userData);
    } else {
      alert("Failed to load user profile.");
    }
  } catch {
    alert("Failed to load user profile.");
  }

  // setup password visibility toggles
  setupPasswordToggles();

  // setup password change checkbox
  setupPasswordChangeCheckbox();

  // setup password validation
  const passwordInput = DOM.get("password-input");
  if (passwordInput) {
    passwordInput.addEventListener("input", function () {
      updatePasswordRequirements(this.value);
    });
  }
}

/**
 * Populate profile with user data
 */
function populateProfile(user) {
  // update display elements
  DOM.setText("email-display", user.email);
  DOM.setText("first-name-display", user.first_name);
  DOM.setText("last-name-display", user.last_name);
  DOM.setText("institution-display", user.institution);
  DOM.setText("company-display", user.company);

  // update input fields
  DOM.setValue("email-input", user.email);
  DOM.setValue("first-name-input", user.first_name);
  DOM.setValue("last-name-input", user.last_name);
  DOM.setValue("company-input", user.company);
}

/**
 * Setup password visibility toggles
 */
function setupPasswordToggles() {
  const setupToggle = (inputId, buttonId) => {
    const input = DOM.get(inputId);
    const button = DOM.get(buttonId);

    if (input && button) {
      button.addEventListener("click", () => {
        const isPassword = input.type === "password";
        input.type = isPassword ? "text" : "password";
        button.textContent = isPassword ? "Hide" : "Show";
      });
    } else {
      console.warn(
        `Could not set up password toggle for ${inputId} and ${buttonId}`
      );
    }
  };

  setupToggle("password-input", "toggle-password");
  setupToggle("confirm-password-input", "toggle-confirm-password");
}

/**
 * Setup password change checkbox behavior
 */
function setupPasswordChangeCheckbox() {
  const checkbox = DOM.get("password-change-checkbox");
  const fields = DOM.get("password-fields");
  const message = DOM.get("message");

  if (checkbox && fields) {
    checkbox.addEventListener("change", function () {
      const display = this.checked ? "block" : "none";
      fields.style.display = display;

      if (message) {
        message.style.display = display;
      }
    });
  }
}

/**
 * Enable edit mode
 */
function enableEdit() {
  DOM.setDisplay("view-mode", "none");
  DOM.setDisplay("edit-mode", "block");
}

/**
 * Save profile changes
 */
function saveChanges() {
  const body = {
    email: DOM.getValue("email-input"),
    first_name: DOM.getValue("first-name-input"),
    last_name: DOM.getValue("last-name-input"),
    company: DOM.getValue("company-input"),
    institution: DOM.getText("institution-display"),
  };

  // handle password change if checkbox is checked
  const passwordChangeCheckbox = DOM.get("password-change-checkbox");
  if (passwordChangeCheckbox && passwordChangeCheckbox.checked) {
    const password = DOM.getValue("password-input");
    const confirmPassword = DOM.getValue("confirm-password-input");

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

  // Determine the correct action URL based on library context
  let actionUrl = "/profile/update/";

  // Check if we're in a library context
  const currentLibrarySlug = document.querySelector(
    'meta[name="current-library-slug"]'
  )?.content;
  if (currentLibrarySlug && currentLibrarySlug !== "paletta") {
    actionUrl = `/library/${currentLibrarySlug}/profile/update/`;
  }

  // create and submit form
  submitFormData(actionUrl, body);
}

/**
 * Create and submit a form with the given data
 */
function submitFormData(action, data) {
  const form = document.createElement("form");
  form.method = "POST";
  form.action = action;

  // add CSRF token
  const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");
  if (csrfToken) {
    const csrfInput = document.createElement("input");
    csrfInput.type = "hidden";
    csrfInput.name = "csrfmiddlewaretoken";
    csrfInput.value = csrfToken.value;
    form.appendChild(csrfInput);
  }

  // add form fields
  for (const key in data) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = key;
    input.value = data[key];
    form.appendChild(input);
  }

  // submit the form
  document.body.appendChild(form);
  form.submit();
}

// initialise on DOM content loaded
document.addEventListener("DOMContentLoaded", initializeProfile);

// expose functions to window for HTML onclick handlers
window.enableEdit = enableEdit;
window.saveChanges = saveChanges;
