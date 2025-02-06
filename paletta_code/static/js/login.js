document

  .querySelector(".login-form")

  .addEventListener("submit", async function (e) {
    e.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!email || !password) {
      alert("Please fill in all required fields.");

      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/login/", {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({ email: email, password: password }),
      });

      if (response.ok) {
        window.location.href = "/static/html/homepage_internal.html";
      } else {
        const data = await response.json();

        // Check if data.detail is an array or object and handle accordingly
        const errorMessage = Array.isArray(data.detail)
          ? data.detail.map((err) => err.msg || JSON.stringify(err)).join(", ")
          : data.detail.msg || JSON.stringify(data.detail);

        alert(`Login failed: ${errorMessage}`);
      }
    } catch (error) {
      console.error("Error:", error);

      alert("An error occurred during login.");
    }
  });
