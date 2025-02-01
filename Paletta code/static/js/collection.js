
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
  const collectionGrid = document.querySelector('.clips-grid');
  const favorites = getFavorites();
  collectionGrid.innerHTML = '';

  if (favorites.length === 0) {
    collectionGrid.innerHTML = `
      <div class="empty-collection">
        <p>Your collection is empty. Browse and add clips from the <a href="clip store all external.html">Clip Store</a>.</p>
      </div>
    `;
    return;
  }

  favorites.forEach(clip => {
    const tagsHTML = clip.tags.map(tag => `<span class="tag">${tag}</span>`).join('');
    const clipCard = document.createElement('div');
    clipCard.className = 'clip';
    clipCard.innerHTML = `
      <img src="${clip.image}" alt="${clip.title}">
      <div class="clip-details">
        <h2>${clip.title}</h2>
        <p>Category: ${clip.category || 'N/A'}</p>
        <div class="tags">${tagsHTML || 'No Tags'}</div>
        <button class="add-to-cart" data-id="${clip.id}">Add to cart</button>
        <button class="remove" data-id="${clip.id}">Remove</button>
      </div>
    `;
    collectionGrid.appendChild(clipCard);

    // add event listener
    clipCard.querySelector('.add-to-cart').addEventListener('click', () => {
      const cart = getCart();
      // print
      console.log("Current Cart:", cart);
      if (!cart.some(item => item.id === clip.id)) {
        cart.push(clip);
        saveCart(cart);
        alert("Added to cart!");
        console.log("Updated Cart:", cart);
      } else {
        alert("This clip is already in your cart!");
      }
    });

    clipCard.querySelector('.remove').addEventListener('click', () => {
      const updatedFavorites = favorites.filter(item => item.id !== clip.id);
      saveFavorites(updatedFavorites);
      renderCollection();
    });
  });
}

// initialize
document.addEventListener('DOMContentLoaded', () => {
  renderCollection();
});
