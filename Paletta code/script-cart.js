// Load cart from localStorage
const cartItemsContainer = document.querySelector('.cart-items');
const totalContainer = document.querySelector('.total');

function renderCart() {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    cartItemsContainer.innerHTML = '';

    if (cart.length === 0) {
        cartItemsContainer.innerHTML = '<p>Your cart is empty</p>';
        totalContainer.textContent = 'Total: $0';
        return;
    }

    let total = 0;

    cart.forEach((item, index) => {
        total += item.price;

        const cartItem = document.createElement('div');
        cartItem.classList.add('cart-item');
        cartItem.innerHTML = `
            <span>${item.name} - $${item.price}</span>
            <button onclick="removeFromCart(${index})">Remove</button>
        `;
        cartItemsContainer.appendChild(cartItem);
    });

    totalContainer.textContent = `Total: $${total}`;
}

function removeFromCart(index) {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    cart.splice(index, 1);
    localStorage.setItem('cart', JSON.stringify(cart));
    renderCart();
}

// Initial render
renderCart();
