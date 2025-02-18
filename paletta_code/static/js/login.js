document.addEventListener("DOMContentLoaded", () => {
  document
    .querySelector(".login-form")
    .addEventListener("submit", async function (e) {
      e.preventDefault();

      // get user input
      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value.trim();

      if (!email || !password) {
        alert("Please fill in all required fields.");
        return;
      }

      try {
        // prepare form data as URL-encoded format for OAuth2PasswordRequestForm.
        // Note: send the email value under the "username" key
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);

        // send login request
        const response = await fetch("http://127.0.0.1:8000/auth/token", {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
          },
          body: formData.toString(),
        });

        if (!response.ok) {
          // attempt to parse error response
          const errorData = await response.json();
          console.error("Login failed:", errorData);
          alert(`Login failed: ${errorData.detail || "Invalid credentials"}`);
          return;
        }

        // parse token response
        const data = await response.json();
        console.log("Token response:", data);

        if (data.access_token) {
          localStorage.setItem("access_token", data.access_token);
          console.log("Token stored successfully.");

          // redirect user to homepage
          window.location.href = "/static/html/homepage_internal.html";
        } else {
          alert("Login succeeded, but no token received.");
        }
      } catch (error) {
        console.error("Error during login:", error);
        alert("An error occurred. Please try again.");
      }
    });
});
