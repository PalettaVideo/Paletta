document.addEventListener("DOMContentLoaded", function () {
  // Handle payment method selection
  const paymentMethods = document.querySelectorAll(".payment-method");
  paymentMethods.forEach((method) => {
    method.addEventListener("click", function () {
      // Remove selected class from all methods
      paymentMethods.forEach((m) => m.classList.remove("selected"));
      // Add selected class to clicked method
      this.classList.add("selected");
    });
  });

  // Handle checkout button click
  document
    .getElementById("complete-order")
    .addEventListener("click", function () {
      const form = document.getElementById("checkout-form");

      // Simple validation
      const cardName = document.getElementById("card-name").value;
      const cardNumber = document.getElementById("card-number").value;
      const cardExpiry = document.getElementById("card-expiry").value;
      const cardCvc = document.getElementById("card-cvc").value;

      if (!cardName || !cardNumber || !cardExpiry || !cardCvc) {
        alert("Please fill in all payment details");
        return;
      }

      // In a real app, you would do proper validation and card processing here
      // For now, just send a request to complete the order
      const csrfToken = document.querySelector(
        "[name=csrfmiddlewaretoken]"
      ).value;

      // Disable button and show loading state
      const button = this;
      button.disabled = true;
      button.innerText = "Processing...";

      // Process the order
      fetch("/checkout/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({
          payment_method: document.querySelector(".payment-method.selected")
            .dataset.method,
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            alert("Order completed successfully!");
            // Redirect to order details page
            window.location.href = data.redirect_url;
          } else {
            alert("Error: " + data.message);
            button.disabled = false;
            button.innerText = "Complete Order";
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          alert("An error occurred while processing your order.");
          button.disabled = false;
          button.innerText = "Complete Order";
        });
    });
});
