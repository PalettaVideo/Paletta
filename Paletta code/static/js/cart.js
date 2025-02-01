
    // Load the cart items from localStorage
    function loadCart() {
      const cart = JSON.parse(localStorage.getItem('cart')) || [];
      const cartItemsContainer = document.querySelector('.cart-items');
      const cartTotalElement = document.getElementById('cart-total');
      const cartCountElement = document.getElementById('cart-count');

      cartItemsContainer.innerHTML = '';
      let total = 0;

     


      if (cart.length === 0) {
        cartItemsContainer.innerHTML = '<p>Your cart is empty. <a href="clip store all internal.html">Go to Clip Store</a></p>';
        cartCountElement.textContent = '0';
        cartTotalElement.textContent = '0.00';
        return;
      }

      cart.forEach((item, index) => {
        const cartItem = document.createElement('div');
        cartItem.className = 'cart-item';

        total += item.price * item.quantity;

        cartItem.innerHTML = `
          <img src="${item.image || 'placeholder.jpg'}" alt="${item.name}">
          <div class="cart-item-details">
            <h3>${item.name}</h3>
            <p>Resolution: 4K</p>
            <p>£${item.price.toFixed(2)} x ${item.quantity}</p>
          </div>
          <div class="cart-item-actions">
            <button onclick="removeFromCart(${index})">Remove</button>
          </div>
        `;

        cartItemsContainer.appendChild(cartItem);
      });

      cartCountElement.textContent = cart.length;
      cartTotalElement.textContent = total.toFixed(2);
    }

    function removeFromCart(index) {
      const cart = JSON.parse(localStorage.getItem('cart')) || [];
      cart.splice(index, 1);
      localStorage.setItem('cart', JSON.stringify(cart));
      loadCart();
    }

    document.addEventListener('DOMContentLoaded', loadCart);


    const centerButton = document.getElementById('centerButton');
    const popupMenu = document.getElementById('popupMenu');

    centerButton.addEventListener('click', (event) => {
      event.stopPropagation();
      popupMenu.style.display = popupMenu.style.display === 'block' ? 'none' : 'block';
    });

    document.addEventListener('click', () => {
      popupMenu.style.display = 'none';
    });

    popupMenu.addEventListener('click', (event) => {
      event.stopPropagation();
    });

  