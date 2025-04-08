// get data from collection and cart
function getFavorites() {
  return JSON.parse(localStorage.getItem("userCollection")) || [];
}

function getCart() {
  return JSON.parse(localStorage.getItem("userCart")) || [];
}

// save data from collection and cart
function saveFavorites(favorites) {
  localStorage.setItem("userCollection", JSON.stringify(favorites));
}

function saveCart(cart) {
  localStorage.setItem("userCart", JSON.stringify(cart));
}

// collection content
function renderCollection() {
  const collectionGrid = document.querySelector(".clips-grid");
  const favorites = getFavorites();

  // Clear existing content
  if (collectionGrid) {
    collectionGrid.innerHTML = "";
  } else {
    console.error("Collection grid not found in the DOM");
    return;
  }

  // If there are no localStorage favorites, show empty state
  if (favorites.length === 0) {
    // Get the clip store URL from a data attribute in the document
    const clipStoreUrl =
      document.querySelector('meta[name="clip-store-url"]')?.content || "/";

    collectionGrid.innerHTML = `
      <div class="no-clips">
        <p>Your collection is empty. Browse the clip store to add items to your collection.</p>
        <a href="${clipStoreUrl}">
          <button class="view-details">Browse Clip Store</button>
        </a>
      </div>
    `;
    return;
  }

  // Render clips from localStorage
  favorites.forEach((clip) => {
    // Skip items without an id
    if (!clip.id) return;

    // Use thumbnail if available
    const thumbnailURL =
      clip.thumbnail || "/static/picture/default_thumbnail.png";

    // Create clip card
    const clipCard = document.createElement("div");
    clipCard.className = "clip";
    clipCard.innerHTML = `
      <img src="${thumbnailURL}" alt="${clip.title || "Video"}">
      <div class="clip-details">
        <h2>${clip.title || "Untitled Video"}</h2>
        <a href="/clip/${clip.id}/">
          <button class="view-details">View Details</button>
        </a>
        <button class="remove" data-clip-id="${clip.id}">Remove</button>

      </div>
    `;
    collectionGrid.appendChild(clipCard);

    // Add event listener to remove button
    clipCard.querySelector(".remove").addEventListener("click", function () {
      removeFromCollection(clip.id, this);
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
    // Update localStorage
    const favorites = getFavorites();
    const updatedFavorites = favorites.filter((item) => item.id != clipId);
    saveFavorites(updatedFavorites);

    // Remove from UI
    const clipElement = buttonElement.closest(".clip");
    if (clipElement) {
      clipElement.style.opacity = "0";
      setTimeout(() => {
        clipElement.remove();
        checkEmptyCollection();
      }, 300);
    }

    // Show notification
    showNotification("Clip removed from your collection");
  }

  function checkEmptyCollection() {
    // Check if there are any clips left
    const remainingClips = document.querySelectorAll(".clip");
    if (remainingClips.length === 0) {
      // If no clips left, show empty state
      const clipsGrid = document.querySelector(".clips-grid");
      const clipStoreUrl =
        document.querySelector('meta[name="clip-store-url"]')?.content || "/";

      clipsGrid.innerHTML = `
      <div class="no-clips">
        <p>Your collection is empty. Browse the clip store to add items to your collection.</p>
        <a href="${clipStoreUrl}">
          <button class="view-details">Browse Clip Store</button>
        </a>
      </div>
    `;
    }
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
