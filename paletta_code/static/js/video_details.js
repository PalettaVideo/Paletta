document.addEventListener("DOMContentLoaded", function () {
  const addToCartButton = document.getElementById("addToCartButton");
  const popupOverlay = document.getElementById("popupOverlay");
  const confirmAddToCart = document.getElementById("confirmAddToCart");
  const addToCollectionButton = document.getElementById(
    "addToCollectionButton"
  );
  const requestNowButton = document.getElementById("requestNowButton");

  // Add to cart functionality
  if (addToCartButton && popupOverlay && confirmAddToCart) {
    addToCartButton.addEventListener("click", () => {
      popupOverlay.style.display = "flex";
    });

    confirmAddToCart.addEventListener("click", () => {
      const selectedResolution = document.querySelector(
        'input[name="resolution"]:checked'
      );
      if (selectedResolution) {
        const resolution = selectedResolution.value;
        const price = selectedResolution.dataset.price;
        // Get clip ID from meta tag in the document
        const clipId =
          document.querySelector('meta[name="clip-id"]')?.content || "0";

        // Get CSRF token for Django
        const csrftoken = document.querySelector(
          "[name=csrfmiddlewaretoken]"
        ).value;

        // Send AJAX request to add to cart
        fetch("/cart/add/", {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrftoken,
          },
          body: `video_id=${clipId}&resolution=${resolution}&price=${price}`,
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              alert(
                `Item added to cart! Resolution: ${resolution}, Price: £${price}`
              );
              popupOverlay.style.display = "none";

              // Update cart count in header if exists
              const cartCountElement = document.querySelector(".cart-count");
              if (cartCountElement) {
                cartCountElement.textContent = data.cart_count;
              }
            } else {
              alert("Error: " + (data.message || data.error));
            }
          })
          .catch((error) => {
            console.error("Error:", error);
            alert("An error occurred while adding the item to cart.");
          });
      } else {
        alert("Please select a resolution");
      }
    });

    popupOverlay.addEventListener("click", (event) => {
      if (event.target === popupOverlay) {
        popupOverlay.style.display = "none";
      }
    });
  }

  // Add to collection functionality
  if (addToCollectionButton) {
    addToCollectionButton.addEventListener("click", () => {
      const clipId = document.querySelector('meta[name="clip-id"]').content;
      const csrftoken = document.querySelector(
        "[name=csrfmiddlewaretoken]"
      ).value;

      // Create form data for the request
      const formData = new FormData();
      formData.append("clip_id", clipId);
      formData.append("csrfmiddlewaretoken", csrftoken);

      // Send POST request to add item to collection
      fetch("/collection/add/", {
        method: "POST",
        body: formData,
        headers: {
          "X-CSRFToken": csrftoken,
        },
        credentials: "same-origin",
      })
        .then((response) => {
          if (response.ok) {
            return response.json();
          }
          throw new Error("Network response was not ok");
        })
        .then((data) => {
          if (data.success) {
            alert("Item added to your collection!");
          } else {
            alert("Error: " + data.error);
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          alert("Failed to add item to collection. Please try again.");
        });
    });
  }

  // Request Now functionality
  if (requestNowButton) {
    requestNowButton.addEventListener("click", () => {
      const clipId = document.querySelector('meta[name="clip-id"]').content;
      window.location.href = `/request/${clipId}/`;
    });
  }
});
