
document.getElementById('application-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission behavior
    alert('Thank you for your application! We will contact you via email.');
    this.reset(); // Reset the form after submission
});

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
