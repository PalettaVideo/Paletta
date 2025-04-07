// get data from collection and cart
function getFavorites() {
  return JSON.parse(localStorage.getItem("favorites")) || [];
}

function getCart() {
  return JSON.parse(localStorage.getItem("cart")) || [];
}

// save data from collection and cart
function saveFavorites(favorites) {
  localStorage.setItem("favorites", JSON.stringify(favorites));
}

function saveCart(cart) {
  localStorage.setItem("cart", JSON.stringify(cart));
}

// collection content
function renderCollection() {
  const collectionGrid = document.querySelector(".clips-grid");
  const favorites = getFavorites();
  collectionGrid.innerHTML = "";

  // Get the clip store URL from a data attribute in the document
  // This avoids hardcoding URLs in JavaScript
  const clipStoreUrl =
    document.querySelector('meta[name="clip-store-url"]')?.content || "/";

  if (favorites.length === 0) {
    collectionGrid.innerHTML = `
      <div class="empty-collection">
        <p>Your collection is empty. Browse and add clips from the <a href="${clipStoreUrl}">Clip Store</a>.</p>
      </div>
    `;
    return;
  }

  favorites.forEach((clip) => {
    const tagsHTML = clip.tags
      .map((tag) => `<span class="tag">${tag}</span>`)
      .join("");
    const clipCard = document.createElement("div");
    clipCard.className = "clip";
    clipCard.innerHTML = `
      <img src="${clip.image}" alt="${clip.title}">
      <div class="clip-details">
        <h2>${clip.title}</h2>
        <p>Category: ${clip.category || "N/A"}</p>
        <div class="tags">${tagsHTML || "No Tags"}</div>
        <button class="add-to-cart" data-id="${clip.id}">Add to cart</button>
        <button class="remove" data-id="${clip.id}">Remove</button>
      </div>
    `;
    collectionGrid.appendChild(clipCard);

    // add event listener
    clipCard.querySelector(".add-to-cart").addEventListener("click", () => {
      const cart = getCart();
      // print
      console.log("Current Cart:", cart);
      if (!cart.some((item) => item.id === clip.id)) {
        cart.push(clip);
        saveCart(cart);
        alert("Added to cart!");
        console.log("Updated Cart:", cart);
      } else {
        alert("This clip is already in your cart!");
      }
    });

    clipCard.querySelector(".remove").addEventListener("click", () => {
      const updatedFavorites = favorites.filter((item) => item.id !== clip.id);
      saveFavorites(updatedFavorites);
      renderCollection();
    });
  });
}

// initialize
document.addEventListener("DOMContentLoaded", () => {
  renderCollection();

  // Set up event listeners for remove buttons
  setupRemoveButtons();

  function setupRemoveButtons() {
    const removeButtons = document.querySelectorAll(".remove");

    removeButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const clipId = this.getAttribute("data-clip-id");
        if (clipId) {
          removeFromCollection(clipId, this);
        }
      });
    });
  }

  function removeFromCollection(clipId, buttonElement) {
    // Get the CSRF token
    const csrftoken = document.querySelector(
      "[name=csrfmiddlewaretoken]"
    ).value;

    // Create form data for the request
    const formData = new FormData();
    formData.append("clip_id", clipId);
    formData.append("csrfmiddlewaretoken", csrftoken);

    // Send POST request to remove item from collection
    fetch("/collection/remove/", {
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
          // Find the clip element and remove it
          const clipElement = buttonElement.closest(".clip");
          if (clipElement) {
            clipElement.style.opacity = "0";
            setTimeout(() => {
              clipElement.remove();

              // Check if there are any clips left
              const remainingClips = document.querySelectorAll(".clip");
              if (remainingClips.length === 0) {
                // If no clips left, show empty state
                const clipsGrid = document.querySelector(".clips-grid");
                const clipStoreUrl =
                  document.querySelector('meta[name="clip-store-url"]')
                    ?.content || "/";

                clipsGrid.innerHTML = `
                <div class="no-clips">
                  <p>Your collection is empty. Browse the clip store to add items to your collection.</p>
                  <a href="${clipStoreUrl}">
                    <button class="add-to-cart">Browse Clip Store</button>
                  </a>
                </div>
              `;
              }
            }, 300);
          }

          // Show success message
          showNotification("Clip removed from your collection");
        } else {
          // Show error message
          showNotification(
            "Error: " + (data.error || "Failed to remove clip"),
            "error"
          );
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        showNotification("Failed to remove clip from collection", "error");
      });
  }

  function showNotification(message, type = "success") {
    // Create notification element
    const notification = document.createElement("div");
    notification.className = `notification ${type}`;
    notification.textContent = message;

    // Add to body
    document.body.appendChild(notification);

    // Animate in
    setTimeout(() => {
      notification.classList.add("show");
    }, 10);

    // Remove after 3 seconds
    setTimeout(() => {
      notification.classList.remove("show");
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 3000);
  }
});
