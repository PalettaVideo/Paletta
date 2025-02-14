export function validatePassword(password) {
  const requirements = {
    length: password.length >= 8,
    lowercase: /[a-z]/.test(password),
    uppercase: /[A-Z]/.test(password),
    number: /\d/.test(password),
    specialChar: /[@.#$!%^&*.?]/.test(password),
  };

  const validCount = Object.values(requirements).filter(Boolean).length;
  let strength = validCount >= 3 ? "Medium" : "Weak";
  if (validCount === 5) strength = "Strong";

  return { strength, requirements };
}

export function updatePasswordRequirements(password) {
  const { strength, requirements } = validatePassword(password);

  document.getElementById("letter").className = requirements.lowercase
    ? "valid"
    : "invalid";
  document.getElementById("capital").className = requirements.uppercase
    ? "valid"
    : "invalid";
  document.getElementById("number").className = requirements.number
    ? "valid"
    : "invalid";
  document.getElementById("length").className = requirements.length
    ? "valid"
    : "invalid";

  const passwordError = document.getElementById("password-error");
  passwordError.textContent = `Password Strength: ${strength}`;
  passwordError.style.color = strength === "Strong" ? "green" : "orange";
  passwordError.style.display = "block";

  return strength;
}

// event listeners for password validation
export function initialisePasswordValidation() {
  const passwordInput = document.getElementById("password");
  const messageBox = document.getElementById("message");

  if (!passwordInput || !messageBox) return; // ensure elements exist before adding listeners

  passwordInput.addEventListener("focus", () => {
    messageBox.style.display = "block";
  });

  passwordInput.addEventListener("blur", () => {
    messageBox.style.display = "none";
  });

  passwordInput.addEventListener("input", function () {
    updatePasswordRequirements(passwordInput.value);
  });
}
