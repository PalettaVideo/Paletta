
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
