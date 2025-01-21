// 初始化 Clips 数据
function loadClips() {
    const clips = [
      { id: 1, title: "Drone upwards from UCL Quad", image: "placeholder1.jpg", price: 10.99 },
      { id: 2, title: "Drone/Aquatic Centre", image: "placeholder2.jpg", price: 12.99 },
      { id: 3, title: "Gower Street Sign", image: "placeholder3.jpg", price: 8.99 },
      { id: 4, title: "High angle shot of UCL East Campus", image: "placeholder4.jpg", price: 11.99 },
      { id: 5, title: "Slow Zoom into IOE From UCL Quad", image: "placeholder5.jpg", price: 9.99 },
    ];
  
    const clipsGrid = document.querySelector(".clips-grid");
    clipsGrid.innerHTML = ""; // 清空内容
  
    clips.forEach((clip) => {
      const clipCard = document.createElement("div");
      clipCard.className = "clip-card";
  
      clipCard.innerHTML = `
        <img src="${clip.image}" alt="${clip.title}">
        <h2>${clip.title}</h2>
        <p>Price: £${clip.price.toFixed(2)}</p>
        <div class="actions">
          <button class="like">♥</button>
          <button class="add-to-cart" data-id="${clip.id}">🛒 Add to Cart</button>
        </div>
      `;
  
      clipsGrid.appendChild(clipCard);
    });
  
    // 为每个购物车按钮添加事件监听
    document.querySelectorAll(".add-to-cart").forEach((button) => {
      button.addEventListener("click", () => {
        const clipId = parseInt(button.getAttribute("data-id"), 10);
        addToCart(clips.find((clip) => clip.id === clipId));
      });
    });
  }
  
  // 将 Clip 添加到购物车并存储到 localStorage
  function addToCart(clip) {
    let cart = JSON.parse(localStorage.getItem("cart")) || []; // 从 localStorage 获取购物车数据
  
    const existingItem = cart.find((item) => item.id === clip.id);
    if (existingItem) {
      existingItem.quantity += 1; // 如果商品已存在，增加数量
    } else {
      cart.push({ ...clip, quantity: 1 }); // 新商品加入购物车
    }
  
    localStorage.setItem("cart", JSON.stringify(cart)); // 更新 localStorage
    alert(`${clip.title} has been added to your cart!`);
  }
  
  // 页面加载时初始化 Clips
  document.addEventListener("DOMContentLoaded", () => {
    loadClips();
  });
  