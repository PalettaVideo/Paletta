
    const addToCartButton = document.getElementById('addToCartButton');
    const popupOverlay = document.getElementById('popupOverlay');
    const confirmAddToCart = document.getElementById('confirmAddToCart');

    addToCartButton.addEventListener('click', () => {
      popupOverlay.style.display = 'flex';
    });

    confirmAddToCart.addEventListener('click', () => {
      alert('Item added to cart!');
      popupOverlay.style.display = 'none';
    });

    popupOverlay.addEventListener('click', (event) => {
      if (event.target === popupOverlay) {
        popupOverlay.style.display = 'none';
      }
    });
