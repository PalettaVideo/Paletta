// Constants
const COLLECTION_STORAGE_KEY = "userCollection";
const CART_STORAGE_KEY = "userCart";

// Get current library context for localStorage keys
function getCurrentLibrarySlug() {
  // Try to get from meta tag first (most reliable)
  const metaLibrarySlug = document.querySelector(
    'meta[name="current-library-slug"]'
  )?.content;
  if (metaLibrarySlug) {
    return metaLibrarySlug;
  }

  // Try to get from URL path as fallback
  const pathParts = window.location.pathname.split("/");
  const libraryIndex = pathParts.indexOf("library");
  if (libraryIndex !== -1 && pathParts[libraryIndex + 1]) {
    return pathParts[libraryIndex + 1];
  }

  // Fallback to 'paletta' if no library found
  return "paletta";
}

// Get library-specific localStorage keys
function getCartStorageKey() {
  return `userCart_${getCurrentLibrarySlug()}`;
}

function getCollectionStorageKey() {
  return `userCollection_${getCurrentLibrarySlug()}`;
}

// get data from collection and cart
function getFavorites() {
  return JSON.parse(localStorage.getItem(getCollectionStorageKey())) || [];
}

function getCart() {
  return JSON.parse(localStorage.getItem(getCartStorageKey())) || [];
}

// save data from collection and cart
function saveFavorites(favorites) {
  localStorage.setItem(getCollectionStorageKey(), JSON.stringify(favorites));
}

function saveCart(cart) {
  localStorage.setItem(getCartStorageKey(), JSON.stringify(cart));
}

// Clear stale localStorage data from other libraries
function clearStaleLibraryData() {
  const currentLibrarySlug = getCurrentLibrarySlug();
  const keysToRemove = [];

  // Check all localStorage keys
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (
      key &&
      (key.startsWith("userCart_") || key.startsWith("userCollection_"))
    ) {
      // If it's not for the current library, mark for removal
      if (!key.endsWith(`_${currentLibrarySlug}`)) {
        keysToRemove.push(key);
      }
    }
  }

  // Remove stale keys
  keysToRemove.forEach((key) => {
    localStorage.removeItem(key);
  });

  if (keysToRemove.length > 0) {
    console.log(
      `Cleared ${keysToRemove.length} stale localStorage entries for library switch`
    );
  }
}

// Get default thumbnail path for missing thumbnails
function getDefaultThumbnail() {
  // Try to get from the page if available
  const defaultThumbnailPath = document.querySelector(
    'meta[name="default-thumbnail"]'
  )?.content;
  return defaultThumbnailPath || "/static/picture/default-thumbnail.png";
}

// Process thumbnail URLs that might be page URLs
function processThumbnail(clip) {
  // If the clip needs a thumbnail (added from video detail page)
  if (clip.needsThumbnail) {
    // Get the video ID from the clip and make a request to the server
    // for the thumbnail URL, then update the local storage
    if (clip.id) {
      // Return a promise to fetch the thumbnail
      return fetchThumbnailForClip(clip.id)
        .then((thumbnailUrl) => {
          if (thumbnailUrl) {
            // Update clip with the fetched thumbnail
            clip.thumbnail = thumbnailUrl;
            clip.needsThumbnail = false;

            // Update storage
            const favorites = getFavorites();
            const updatedFavorites = favorites.map((item) =>
              item.id == clip.id
                ? { ...item, thumbnail: thumbnailUrl, needsThumbnail: false }
                : item
            );
            saveFavorites(updatedFavorites);
          }
          return clip;
        })
        .catch((error) => {
          console.error(`Error fetching thumbnail for clip ${clip.id}:`, error);
          return clip;
        });
    }
  }

  // If it doesn't need processing, return as is
  return Promise.resolve(clip);
}

// Fetch thumbnail URL for a clip from the server
function fetchThumbnailForClip(clipId) {
  // Get CSRF token
  const csrfToken = document.querySelector(
    'input[name="csrfmiddlewaretoken"]'
  )?.value;

  // Only proceed if we have a csrf token and clip ID
  if (!csrfToken || !clipId) {
    console.error("Missing CSRF token or clip ID");
    return Promise.resolve(null);
  }

  // Make a fetch request to get clip details
  // Try different possible paths to the thumbnail API
  const urls = [
    `/api/clip/${clipId}/thumbnail/`, // Direct API path
    `/api/api/clip/${clipId}/thumbnail/`, // Through videos app
  ];

  // Try the first URL, if it fails, try the second
  return fetch(urls[0], {
    method: "GET",
    headers: {
      "X-CSRFToken": csrfToken,
    },
  })
    .then((response) => {
      if (response.ok) {
        return response.json();
      }
      // If first URL fails, try the second URL
      console.log(`First URL failed, trying ${urls[1]}...`);
      return fetch(urls[1], {
        method: "GET",
        headers: {
          "X-CSRFToken": csrfToken,
        },
      });
    })
    .then((response) => {
      // Handle the response - it could be from the first or second fetch
      if (response.ok) {
        return response.json();
      }
      if (response instanceof Response) {
        throw new Error(`Failed to fetch thumbnail: ${response.status}`);
      }
      return response; // It's already parsed JSON from the first fetch
    })
    .then((data) => {
      if (data && data.thumbnail_url) {
        return data.thumbnail_url;
      }
      return null;
    })
    .catch((error) => {
      console.error("Thumbnail fetch error:", error);
      return null;
    });
}

// Remove clip from collection
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

// Check if collection is empty and update UI
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

// Show notification toast
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
      notification.remove();
    }, 300);
  }, 3000);
}

// Render collection
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

  // Show loading state
  collectionGrid.innerHTML = `<div class="loading">Loading your collection...</div>`;

  // Process each clip (handling thumbnails that might need fetching)
  const processPromises = favorites.map((clip) => processThumbnail(clip));

  // Once all thumbnails are processed, render the clips
  Promise.all(processPromises)
    .then((processedClips) => {
      // Clear the loading message
      collectionGrid.innerHTML = "";

      // Render each clip
      processedClips.forEach((clip) => {
        // Skip items without an id
        if (!clip.id) return;

        // Create clip card
        const clipCard = document.createElement("div");
        clipCard.className = "clip";
        clipCard.innerHTML = `
          <img src="${clip.thumbnail}" alt="${clip.title || "Video"}">
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
        clipCard
          .querySelector(".remove")
          .addEventListener("click", function () {
            removeFromCollection(clip.id, this);
          });
      });
    })
    .catch((error) => {
      console.error("Error rendering collection:", error);
      collectionGrid.innerHTML = `
        <div class="error">
          <p>There was an error loading your collection. Please try again later.</p>
        </div>
      `;
    });
}

// initialize
document.addEventListener("DOMContentLoaded", () => {
  clearStaleLibraryData();
  renderCollection();
});
