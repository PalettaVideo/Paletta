document.addEventListener('DOMContentLoaded', () => {
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
});

function initializeHeader() {
    setTimeout(() => {  // 添加 setTimeout 等待 DOM 解析
        const centerButton = document.getElementById('centerButton');
        const popupMenu = document.getElementById('popupMenu');
        const uploadButton = document.getElementById('uploadButton');
        const accountButton = document.getElementById('accountButton');

        console.log("Header initialized");
        console.log("centerButton:", centerButton);
        console.log("popupMenu:", popupMenu);
        console.log("uploadButton:", uploadButton);
        console.log("accountButton:", accountButton);

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

        if (uploadButton && accountButton) {
            uploadButton.addEventListener('click', () => {
                alert('Upload clicked');
            });
            accountButton.addEventListener('click', () => {
                alert('My Account clicked');
            });
        } else {
            console.error('Upload or Account button not found');
        }
    }, 500); // 延迟 500ms 确保 DOM 解析
}
