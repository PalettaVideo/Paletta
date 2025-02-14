// TODO: add a logout button

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const token = localStorage.getItem("access_token");
    console.log("Token:", token);
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
    console.log("User Data:", userData);
    populateProfile(userData);
  } catch (error) {
    console.error("Error fetching user data:", error);
    alert("Failed to load user profile.");
  }

  togglePasswordVisibility("password-input", "toggle-password");
  togglePasswordVisibility("confirm-password-input", "toggle-confirm-password");
  document.querySelectorAll('input[name="institution"]').forEach((input) => {
    input.addEventListener("change", handleInstitutionChange);
  });
});

function populateProfile(user) {
  document.getElementById("email-display").innerText = user.email;
  document.getElementById("name-display").innerText = user.username;
  document.getElementById("institution-display").innerText =
    user.institution || "N/A";
  document.getElementById("email-input").value = user.email;
  document.getElementById("name-input").value = user.username;
  document.getElementById("institution-text").value = user.institution || "";
}

function enableEdit() {
  document.getElementById("view-mode").style.display = "none";
  document.getElementById("edit-mode").style.display = "block";
}

function saveChanges() {
  const email = document.getElementById("email-input").value;
  const name = document.getElementById("name-input").value;
  const institutionText = document.getElementById("institution-text").value;

  if (!institutionText.trim()) {
    alert("Please fill out the institution name.");
    return;
  }

  const token = localStorage.getItem("access_token");

  fetch("/users/me", {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      email,
      username: name,
      institution: institutionText,
    }),
  })
    .then((response) => {
      if (!response.ok) throw new Error("Failed to update profile");
      return response.json();
    })
    .then((updatedUser) => {
      populateProfile(updatedUser);
      document.getElementById("view-mode").style.display = "block";
      document.getElementById("edit-mode").style.display = "none";
    })
    .catch((error) => {
      console.error("Error updating profile:", error);
      alert("Failed to update profile.");
    });
}

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

function handleInstitutionChange() {
  document.getElementById("institution-text-container").style.display = "block";
}
