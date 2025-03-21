// index.js
document.addEventListener("DOMContentLoaded", function () {
    const filesToLoad = [
      { url: "./navigation_internal.html", targetId: "header" },
      { url: "./footer.html", targetId: "footer" }
    ];
  
    // 使用Promise.all来并行加载所有文件
    Promise.all(filesToLoad.map(file =>
      fetch(file.url)
        .then(response => {
          if (!response.ok) {
            throw new Error(`Failed to load ${file.url}: ${response.status} ${response.statusText}`);
          }
          return response.text();
        })
        .then(data => {
          document.getElementById(file.targetId).innerHTML = data;
          return file.targetId; // 返回已加载的ID，以便于后续处理
        })
    ))
    .then(loadedIds => {
      // 所有内容加载完成后，初始化header相关的事件
      if (loadedIds.includes('header')) {
        initializeHeader();  // 调用 initializeHeader()
      }
    })
    .catch(error => console.error('Error loading content:', error));
});

// 这里定义了 initializeHeader()
function initializeHeader() {
    const centerButton = document.getElementById('centerButton');
    const popupMenu = document.getElementById('popupMenu');
    
    if (centerButton && popupMenu) {
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
    } else {
        console.error('Header elements not found: centerButton or popupMenu missing');
    }
}
