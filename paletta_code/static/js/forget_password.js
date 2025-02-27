// Wait for the DOM to be fully loaded before executing any code
document.addEventListener("DOMContentLoaded", function () {
  // No client-side form submission needed
  // The form will be submitted directly to Django
});

function goBack() {
  window.history.back();
}

function redirectToLogin() {
  window.location.href = "login.html";
}
