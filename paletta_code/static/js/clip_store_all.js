const tagsFilterButton = document.getElementById('tagsFilterButton');
const tagsFilterPopup = document.getElementById('tagsFilterPopup');
const applyTagsFilterButton = document.getElementById('applyTagsFilter');
const sortByButton = document.getElementById('sortByButton');
const sortByPopup = document.getElementById('sortByPopup');
const tagsCount = document.getElementById('tagsCount');

const clips = [
{ id: 1, title: "Drone upwards from UCL Quad", tags: ["Drone", "UCL"], image: "../picture/All title.png", price: 10, time: 1 ,catagory:"building"},
{ id: 2, title: "Drone/Aquatic Centre", tags: ["Drone"], image: "../picture/All title.png", price: 10.99,  time: 2 ,catagory:"building"},
{ id: 3, title: "Gower Street Sign", tags: ["UCL"], image: "../picture/All title.png",price: 10.99,  time: 3 ,catagory:"building"},
{ id: 4, title: "High angle shot of UCL East Campus", tags: ["UCL", "IOE"], image: "../picture/All title.png",  price: 10.99, time: 4 ,catagory:"building"},
{ id: 5, title: "Slow Zoom into IOE From UCL Quad", tags: ["Drone", "IOE"], image: "../picture/All title.png",  price: 10.99, time: 5 ,catagory:"building"},
];

let openPopup = null;

// initialize
document.addEventListener("DOMContentLoaded", () => {
renderClips(clips);
});

// list of the videos
function renderClips(data) {
const clipsGrid = document.querySelector(".clips-grid");
clipsGrid.innerHTML = '';
data.forEach((clip) => {
 const clipCard = document.createElement("div");
 clipCard.className = "clip";
 clipCard.innerHTML = `
   <img src="${clip.image}" alt="${clip.title}">
   <h2>${clip.title}</h2>
   <div class="clipactions">
     <button class="like" data-id="${clip.id}">
       <svg viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg"><rect fill="none" height="256" width="256"/><path d="M224.6,51.9a59.5,59.5,0,0,0-43-19.9,60.5,60.5,0,0,0-44,17.6L128,59.1l-7.5-7.4C97.2,28.3,59.2,26.3,35.9,47.4a59.9,59.9,0,0,0-2.3,87l83.1,83.1a15.9,15.9,0,0,0,22.6,0l81-81C243.7,113.2,245.6,75.2,224.6,51.9Z"/></svg>
       <span>add to collection</span>
     </button>
     <button class="add-to-cart" data-id="${clip.id}"> 
       <svg baseProfile="tiny" height="24px" version="1.2" viewBox="0 0 24 24" width="24px" xml:space="preserve" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><g id="Layer_1"><g>
         <path d="M20.756,5.345C20.565,5.126,20.29,5,20,5H6.181L5.986,3.836C5.906,3.354,5.489,3,5,3H2.75c-0.553,0-1,0.447-1,1    s0.447,1,1,1h1.403l1.86,11.164c0.008,0.045,0.031,0.082,0.045,0.124c0.016,0.053,0.029,0.103,0.054,0.151    c0.032,0.066,0.075,0.122,0.12,0.179c0.031,0.039,0.059,0.078,0.095,0.112c0.058,0.054,0.125,0.092,0.193,0.13    c0.038,0.021,0.071,0.049,0.112,0.065C6.748,16.972,6.87,17,6.999,17C7,17,18,17,18,17c0.553,0,1-0.447,1-1s-0.447-1-1-1H7.847    l-0.166-1H19c0.498,0,0.92-0.366,0.99-0.858l1-7C21.031,5.854,20.945,5.563,20.756,5.345z M18.847,7l-0.285,2H15V7H18.847z M14,7    v2h-3V7H14z M14,10v2h-3v-2H14z M10,7v2H7C6.947,9,6.899,9.015,6.852,9.03L6.514,7H10z M7.014,10H10v2H7.347L7.014,10z M15,12v-2    h3.418l-0.285,2H15z"/><circle cx="8.5" cy="19.5" r="1.5"/><circle cx="17.5" cy="19.5" r="1.5"/></g></g></svg>
        <span>add to cart</span>
     </button>
   </div>`;
 clipsGrid.appendChild(clipCard);
});

// add listener for each add to cart
document.querySelectorAll('.add-to-cart').forEach(button => {
 button.addEventListener('click', (event) => {
   const clipId = parseInt(event.currentTarget.getAttribute('data-id'));
   addToCart(clipId);
 });
});
}

// add into cart
function addToCart(clipId) {
const clip = clips.find(item => item.id === clipId);
if (!clip) return;

// get the data from the cart
const cart = JSON.parse(localStorage.getItem('cart')) || [];

// check whether exist in the cart
const existingItem = cart.find(item => item.id === clip.id);
if (existingItem) {
 existingItem.quantity += 1; // add one
} else {
 cart.push({ ...clip, quantity: 1 }); // add new clip
}

// update cart date to localStorage
localStorage.setItem('cart', JSON.stringify(cart));
alert(`${clip.title} has been added to the cart!`);
}

// initialize the pop up function
function togglePopup(button, popup) {
button.addEventListener('click', (event) => {
 event.stopPropagation();
 if (openPopup && openPopup !== popup) {
   openPopup.style.display = 'none';
 }
 popup.style.display = popup.style.display === 'block' ? 'none' : 'block';
 openPopup = popup.style.display === 'block' ? popup : null;
});
}

// Tags Filter popup
applyTagsFilterButton.addEventListener('click', () => {
const selectedTags = Array.from(tagsFilterPopup.querySelectorAll('input:checked')).map(input => input.value);
const filteredClips = selectedTags.length
 ? clips.filter(clip => clip.tags.some(tag => selectedTags.includes(tag)))
 : clips;
renderClips(filteredClips);
tagsCount.textContent = selectedTags.length; // count
closePopups();
});

// Sort By popup
sortByPopup.addEventListener('click', (event) => {
if (event.target.tagName === 'A') {
 const sortType = event.target.getAttribute('data-sort');
 const sortedClips = [...clips];
 if (sortType === 'asc') sortedClips.sort((a, b) => a.time - b.time);
 if (sortType === 'desc') sortedClips.sort((a, b) => b.time - a.time);
 if (sortType === 'title-asc') sortedClips.sort((a, b) => a.title - b.title);
 if (sortType === 'title-desc') sortedClips.sort((a, b) => b.title - a.title);
 renderClips(sortedClips);
 closePopups();
}
});

// do not close when clicking inside popup
tagsFilterPopup.addEventListener('click', (event) => event.stopPropagation());
sortByPopup.addEventListener('click', (event) => event.stopPropagation());

// close popup
document.addEventListener('click', closePopups);

function closePopups() {
if (openPopup) {
 openPopup.style.display = 'none';
 openPopup = null;
}
}

togglePopup(tagsFilterButton, tagsFilterPopup);
togglePopup(sortByButton, sortByPopup);








 // initialize collection function
function addToFavorites(clipId) {
const clip = clips.find(item => item.id === clipId);
if (!clip) return;

// get the list of favourites
const favorites = JSON.parse(localStorage.getItem('favorites')) || [];

// check whether exist in favourites
if (!favorites.some(item => item.id === clip.id)) {
 favorites.push(clip);
 localStorage.setItem('favorites', JSON.stringify(favorites));
 alert(`${clip.title} has been added to favorites!`);
} else {
 alert(`${clip.title} is already in your favorites.`);
}
}

// add listener to favourate
document.addEventListener('DOMContentLoaded', () => {
document.querySelectorAll('.like').forEach(button => {
 button.addEventListener('click', (event) => {
   const clipId = parseInt(event.currentTarget.getAttribute('data-id'));
   addToFavorites(clipId);
 });
});
});

// facourate content
function renderFavorites() {
const favorites = JSON.parse(localStorage.getItem('favorites')) || [];
const collectionGrid = document.querySelector(".clips-grid");
if (!collectionGrid) return;

collectionGrid.innerHTML = '';
favorites.forEach((clip) => {
 const clipCard = document.createElement("div");
 clipCard.className = "clip";
 clipCard.innerHTML = `
   <img src="${clip.image}" alt="${clip.title}">
   <h2>${clip.title}</h2>
   <p>Price: £${clip.price.toFixed(2)}</p>
 `;
 collectionGrid.appendChild(clipCard);
});
}


