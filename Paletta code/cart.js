function loadCart() {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    const cartItemsContainer = document.querySelector('.cart-items');
    const cartTotalElement = document.getElementById('cart-total');
  
    cartItemsContainer.innerHTML = '';
    let total = 0;
  
    cart.forEach((item, index) => {
      const cartItem = document.createElement('div');
      cartItem.className = 'cart-item';
  
      total += item.price * item.quantity;
  
      cartItem.innerHTML = `
        <img src="placeholder.jpg" alt="${item.name}">
        <div class="cart-item-details">
          <h2>${item.name}</h2>
          <p>Resolution: <strong>4K</strong></p>
          <p>£${item.price.toFixed(2)} x ${item.quantity}</p>
        </div>
        <div class="cart-item-actions">
          <button onclick="addToCollection(${index})">Add to Collection</button>
          <button class="remove" onclick="removeFromCart(${index})">Remove</button>
        </div>
      `;
  
      cartItemsContainer.appendChild(cartItem);
    });
  
    cartTotalElement.textContent = total.toFixed(2);
  }
  
  function removeFromCart(index) {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    cart.splice(index, 1);
    localStorage.setItem('cart', JSON.stringify(cart));
    loadCart();
  }
  
  function checkout() {
    alert('Proceeding to checkout!');
    localStorage.removeItem('cart');
    loadCart();
  }
  
  function navigateToStore() {
    window.location.href = 'clip-store.html';
  }
  
  document.addEventListener('DOMContentLoaded', loadCart);
  