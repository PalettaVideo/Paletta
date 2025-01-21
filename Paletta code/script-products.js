// Add products to cart and save to localStorage
document.querySelectorAll('.product button').forEach(button => {
    button.addEventListener('click', () => {
        const name = button.getAttribute('data-name');
        const price = parseFloat(button.getAttribute('data-price'));
        
        // Retrieve cart from localStorage or initialize it
        const cart = JSON.parse(localStorage.getItem('cart')) || [];

        // Add product to cart
        cart.push({ name, price });

        // Save updated cart to localStorage
        localStorage.setItem('cart', JSON.stringify(cart));

        alert(`${name} added to the cart!`);
    });
});
