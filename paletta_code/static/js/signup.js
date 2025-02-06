document.querySelectorAll(".institution-checkbox").forEach((checkbox) => {
  checkbox.addEventListener("change", function () {
    const input = document.getElementById(`${this.id}-input`);
    input.disabled = !this.checked;
    input.required = this.checked;
  });
});

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

document
  .querySelector(".signup-form")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    const email = document.getElementById("email").value.trim();
    const name = document.getElementById("name").value.trim();
    const password = document.getElementById("password").value.trim();
    const confirmPassword = document
      .getElementById("confirm-password")
      .value.trim();

    if (!email || !name || !password || !confirmPassword) {
      alert("Please fill in all required fields.");
      return;
    }

    if (password !== confirmPassword) {
      alert("Passwords do not match!");
      return;
    }

    const institutionCheckboxes = document.querySelectorAll(
      ".institution-checkbox:checked"
    );
    const institutions = [];
    for (const checkbox of institutionCheckboxes) {
      const input = document
        .getElementById(`${checkbox.id}-input`)
        .value.trim();
      if (!input) {
        alert(
          "Please fill in the institution details for all selected options."
        );
        return;
      }
      institutions.push(input);
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/users/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email,
          password: password,
          role: "user", // Assuming a default role
          username: name,
          institution: institutions.join(", "),
        }),
      });

      if (response.ok) {
        alert("User created successfully!");
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
