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

uploadBox.addEventListener('click', () => fileInput.click());
selectFile.addEventListener('click', () => fileInput.click());

tagsReference.addEventListener('click', (event) => {
    if (event.target.classList.contains('tag')) {
        addTag(event.target.textContent.trim());
    }
});

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
    inputElement.id = 'tags';
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

function updateWordCount(input, countElement, maxWords) {
    const words = input.value.trim().split(/\s+/).filter(word => word.length > 0);
    countElement.textContent = `${words.length}/${maxWords} words`;
}

titleInput.addEventListener('input', () => {
    updateWordCount(titleInput, titleWordCount, 25);
});

descriptionInput.addEventListener('input', () => {
    updateWordCount(descriptionInput, descriptionWordCount, 100);
});



    const uploadButton = document.getElementById('upload-button');

    uploadButton.addEventListener('click', (event) => {
        event.preventDefault(); // 阻止默认表单提交行为

        const fileInput = document.getElementById('file-input');
        const title = document.getElementById('title');
        const description = document.getElementById('description');
        const category = document.getElementById('category');
        const attributes = document.querySelectorAll('.attribute-group input');
        const selectedTags = tagsInputWrapper.querySelectorAll('.tag'); // 获取已添加的标签

        let isValid = true;

        // 检查文件是否选择
        if (!fileInput.value) {
            alert('Please select a video file.');
            isValid = false;
        }

        // 检查标题是否填写
        if (!title.value.trim()) {
            alert('Please enter a title.');
            isValid = false;
        }

        // 检查描述是否填写
        if (!description.value.trim()) {
            alert('Please enter a description.');
            isValid = false;
        }

        // 检查类别是否选择
        if (!category.value) {
            alert('Please select a category.');
            isValid = false;
        }

        // 检查属性是否填写
        attributes.forEach(attribute => {
            if (!attribute.value.trim()) {
                alert('Please fill out all attributes.');
                isValid = false;
            }
        });

        // 检查标签是否填写
        if (selectedTags.length === 0) {
            alert('Please add at least one tag.');
            isValid = false;
        }

        if (isValid) {
            alert('Form submitted successfully!');
        }
    });

