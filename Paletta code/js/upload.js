// DOM元素引用
const uploadBox = document.getElementById('upload-box');
const fileInput = document.getElementById('file-input');
const selectFile = document.getElementById('select-file');
const tagsInputWrapper = document.getElementById('tags-input-wrapper');
const tagsReference = document.getElementById('tags-reference');
const titleInput = document.getElementById('title');
const descriptionInput = document.getElementById('description');
const titleWordCount = document.getElementById('title-word-count');
const descriptionWordCount = document.getElementById('description-word-count');

let selectedTags = [];

// 事件监听器（保持不变）
uploadBox.addEventListener('click', (event) => {
    if (event.target === uploadBox) fileInput.click();
});

selectFile.addEventListener('click', () => fileInput.click());

tagsReference.addEventListener('click', (event) => {
    event.stopPropagation();
    if (event.target.classList.contains('tag')) {
        addTag(event.target.textContent.trim());
    }
});

// 标签管理功能（保持不变）
function addTag(tag) {
    if (selectedTags.length < 10 && !selectedTags.includes(tag)) {
        selectedTags.push(tag);
        renderTags();
    }
}

function renderTags() {
    tagsInputWrapper.innerHTML = '';
    selectedTags.forEach((tag, index) => {
        const tagElement = document.createElement('span');
        tagElement.className = 'tag';
        tagElement.innerHTML = `${tag} <button class="delete-btn" onclick="deleteTag(${index})">×</button>`;
        tagsInputWrapper.appendChild(tagElement);
    });
    
    const inputElement = document.createElement('input');
    inputElement.type = 'text';
    inputElement.className = 'tags-input';
    inputElement.placeholder = 'Choose a tag or create a new tag (Type and press enter)';
    tagsInputWrapper.appendChild(inputElement);
    
    inputElement.addEventListener('keypress', (event) => {
        if (event.key === 'Enter' && inputElement.value.trim() !== '') {
            event.preventDefault();
            addTag(inputElement.value.trim());
            inputElement.value = '';
        }
    });
}

function deleteTag(index) {
    selectedTags.splice(index, 1);
    renderTags();
}

// 字数统计（保持不变）
function updateWordCount(input, countElement, maxWords) {
    const words = input.value.trim().split(/\s+/).filter(word => word.length > 0);
    countElement.textContent = `${words.length}/${maxWords} words`;
}

titleInput.addEventListener('input', () => updateWordCount(titleInput, titleWordCount, 25));
descriptionInput.addEventListener('input', () => updateWordCount(descriptionInput, descriptionWordCount, 100));

// 上传功能（主要修改部分）
const uploadButton = document.getElementById('upload-button');
uploadButton.addEventListener('click', async (event) => {
    event.preventDefault();

    // 增强的验证逻辑
    const validationErrors = validateForm();
    if (validationErrors.length > 0) {
        alert(validationErrors.join('\n'));
        return;
    }

    try {
        const historyData = await prepareUploadData();
        saveUploadHistory(historyData);
        resetForm();
        alert('Upload successful!');
    } catch (error) {
        alert(`Upload failed: ${error.message}`);
    }
});

// 改进的验证函数
function validateForm() {
    const errors = [];
    const elements = {
        fileInput: document.getElementById('file-input'),
        title: document.getElementById('title'),
        description: document.getElementById('description'),
        category: document.getElementById('category'),
        attributes: document.querySelectorAll('.attribute-group input'),
        tags: tagsInputWrapper.querySelectorAll('.tag')
    };

    // 文件验证
    if (!elements.fileInput.files[0]) {
        errors.push('⚠️ Please select a video file');
    }

    // 文本字段验证
    if (!elements.title.value.trim()) {
        errors.push('⚠️ Title is required');
    }
    if (!elements.description.value.trim()) {
        errors.push('⚠️ Description is required');
    }

    // 分类验证
    if (elements.category.value === '') {
        errors.push('⚠️ Please select a category');
    }

    // 属性验证
    Array.from(elements.attributes).forEach((input, index) => {
        if (!input.value.trim()) {
            const fieldName = input.previousElementSibling?.textContent || `Attribute ${index+1}`;
            errors.push(`⚠️ ${fieldName} is required`);
        }
    });

    // 标签验证
    if (elements.tags.length === 0) {
        errors.push('⚠️ At least one tag is required');
    }

    return errors;
}

// 数据准备函数（保持不变）
async function prepareUploadData() {
    const videoFile = document.getElementById('file-input').files[0];
    const previewImg = document.querySelector('#preview-container img');
    
    let thumbnail = previewImg?.src;
    if (!thumbnail) {
        const video = document.querySelector('#video-preview-container video');
        thumbnail = await captureVideoThumbnail(video);
    }

    return {
        title: titleInput.value.trim(),
        description: descriptionInput.value.trim(),
        timestamp: new Date().toISOString(),
        thumbnail: thumbnail,
        tags: [...selectedTags],
        videoInfo: {
            name: videoFile.name,
            size: videoFile.size,
            type: videoFile.type,
            lastModified: videoFile.lastModified
        }
    };
}

// 保存历史（保持不变）
function saveUploadHistory(data) {
    const history = JSON.parse(localStorage.getItem('uploadHistory') || '[]');
    history.unshift(data);
    localStorage.setItem('uploadHistory', JSON.stringify(history));
}

// 缩略图生成（保持不变）
function captureVideoThumbnail(video) {
    return new Promise((resolve) => {
        const canvas = document.createElement('canvas');
        canvas.width = 160;
        canvas.height = 90;
        
        setTimeout(() => {
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            resolve(canvas.toDataURL());
        }, 500);
    });
}

// 改进的表单重置
function resetForm() {
    const form = document.getElementById('upload-form');
    form.reset();
    selectedTags = [];
    renderTags();
    
    // 手动清除文件预览
    document.getElementById('file-input').value = '';
    document.getElementById('preview-image').value = '';
    ['preview-container', 'video-preview-container'].forEach(id => {
        document.getElementById(id).innerHTML = '';
    });
}

// 预览功能（保持不变）
document.getElementById("preview-image").addEventListener("change", handleImagePreview);
document.getElementById("file-input").addEventListener("change", handleVideoPreview);

function handleImagePreview(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        const previewContainer = document.getElementById("preview-container");
        previewContainer.innerHTML = `
            <img src="${e.target.result}">
            <button class="remove-btn" onclick="this.parentElement.innerHTML=''">×</button>
        `;
    };
    reader.readAsDataURL(file);
}

function handleVideoPreview(event) {
    const file = event.target.files[0];
    if (!file) return;

    const maxSize = 300 * 1024 * 1024;
    if (file.size > maxSize) {
        alert("File size exceeds 300MB");
        event.target.value = null;
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        const previewContainer = document.getElementById("video-preview-container");
        previewContainer.innerHTML = '';

        const video = document.createElement("video");
        video.src = e.target.result;
        video.controls = true;
        video.width = 400;

        video.onloadedmetadata = () => {
            if (video.videoWidth > 1920 || video.videoHeight > 1080) {
                alert("Resolution exceeds 1920x1080");
                fileInput.value = null;
                previewContainer.innerHTML = '';
                return;
            }

            previewContainer.appendChild(video);
            previewContainer.innerHTML += `
                <button class="remove-btn" onclick="this.parentElement.innerHTML=''">×</button>
            `;
        };
    };
    reader.readAsDataURL(file);
}




// 在upload.js中添加表单验证
document.getElementById('upload-form').addEventListener('submit', function(e) {
    if (!this.checkValidity()) {
        e.preventDefault();
        // 显示自定义错误提示
        Array.from(this.elements).forEach(element => {
            if (!element.checkValidity()) {
                element.nextElementSibling?.classList.add('show-error');
            }
        });
    }
});

// 添加实时验证
document.querySelectorAll('input, select').forEach(element => {
    element.addEventListener('input', () => {
        element.nextElementSibling?.classList.toggle('show-error', !element.checkValidity());
    });
});