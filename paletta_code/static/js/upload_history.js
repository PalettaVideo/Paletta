document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    setupSearch();
});

function loadHistory() {
    try {
        const history = JSON.parse(localStorage.getItem('uploadHistory')) || [];
        renderHistory(history);
    } catch (error) {
        console.error('Error loading history:', error);
        showEmptyState();
    }
}

function renderHistory(data) {
    const container = document.querySelector('.history-list');
    if (!data || data.length === 0) {
        showEmptyState();
        return;
    }

    container.innerHTML = data.map((item, index) => `
        <div class="history-item" data-id="${index}">
            <div class="thumbnail-container">
                <img src="${item.thumbnail}" class="video-thumbnail" alt="${item.title}">
            </div>
            <div class="video-info">
                <h3 class="video-title">${item.title}</h3>
                <div class="video-meta">
                    <p class="video-category">Category: ${item.category || 'N/A'}</p>
                    <p class="upload-time">Uploaded: ${formatDate(item.timestamp)}</p>
                </div>
            </div>
            <button class="delete-btn" onclick="deleteVideo(this)">Delete</button>
        </div>
    `).join('');
}

function deleteVideo(button) {
    const item = button.closest('.history-item');
    const itemId = parseInt(item.dataset.id);
    
    if (!confirm('Delete this video permanently?')) return;

    try {
        const history = JSON.parse(localStorage.getItem('uploadHistory'));
        const updatedHistory = history.filter((_, index) => index !== itemId);
        localStorage.setItem('uploadHistory', JSON.stringify(updatedHistory));
        item.remove();
        
        if (updatedHistory.length === 0) showEmptyState();
    } catch (error) {
        console.error('Error deleting video:', error);
    }
}

function formatDate(isoString) {
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(isoString).toLocaleString(undefined, options);
}

function formatSize(bytes) {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
}

function showEmptyState() {
    const container = document.querySelector('.history-list');
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-content">
                <p class="empty-text">There is no history, please 
                    <a href="upload.html" class="upload-link">upload</a> 
                    your first video!
                </p>
            </div>
        </div>
    `;
}

function setupSearch() {
    const searchInput = document.querySelector('.search-box');
    searchInput?.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const items = document.querySelectorAll('.history-item');
        
        items.forEach(item => {
            const title = item.querySelector('h3').textContent.toLowerCase();
            item.style.display = title.includes(searchTerm) ? '' : 'none';
        });
    });
}