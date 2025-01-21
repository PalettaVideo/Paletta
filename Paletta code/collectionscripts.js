// 从 localStorage 加载收藏和购物车
function getFavorites() {
    return JSON.parse(localStorage.getItem('favorites')) || [];
  }
  
  function getCart() {
    return JSON.parse(localStorage.getItem('cart')) || [];
  }
  
  function saveFavorites(favorites) {
    localStorage.setItem('favorites', JSON.stringify(favorites));
  }
  
  function saveCart(cart) {
    localStorage.setItem('cart', JSON.stringify(cart));
  }
  
  // 渲染收藏界面
  function renderCollection() {
    const favorites = getFavorites();
    const collectionGrid = document.querySelector('.clips-grid');
    collectionGrid.innerHTML = '';
  
    if (favorites.length === 0) {
      collectionGrid.innerHTML = `
        <div class="empty-collection">
          <p>Your collection is empty. Browse and add clips from the <a href="clip-store.html">Clip Store</a>.</p>
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
      });
    
      setupCollectionListeners();
    }
  
  // 设置按钮点击事件
  function setupCollectionListeners() {
    document.querySelectorAll('.add-to-cart').forEach(button => {
      button.addEventListener('click', (event) => {
        const clipId = parseInt(event.target.getAttribute('data-id'));
        addToCart(clipId);
      });
    });
  
    document.querySelectorAll('.remove').forEach(button => {
      button.addEventListener('click', (event) => {
        const clipId = parseInt(event.target.getAttribute('data-id'));
        removeFromFavorites(clipId);
      });
    });
  }
  
  // 从收藏中移除
  function removeFromFavorites(clipId) {
    let favorites = getFavorites();
    favorites = favorites.filter(clip => clip.id !== clipId);
    saveFavorites(favorites);
    renderCollection();
  }
  
  // 加入购物车
  function addToCart(clipId) {
    const favorites = getFavorites();
    const cart = getCart();
  
    const clip = favorites.find(clip => clip.id === clipId);
    if (!clip) return;
  
    if (!cart.some(item => item.id === clipId)) {
      cart.push(clip);
      saveCart(cart);
      alert(`${clip.title} has been added to your cart!`);
    } else {
      alert(`${clip.title} is already in your cart.`);
    }
  }
  
  // 初始化收藏界面
  document.addEventListener('DOMContentLoaded', renderCollection);
  