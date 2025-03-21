document.addEventListener("DOMContentLoaded", function () {


    const filesToLoad = [
        { url: "./navigation_internal.html", targetId: "header" },
        { url: "./footer.html", targetId: "footer" }
    ];
    
    Promise.all(filesToLoad.map(file =>
        fetch(file.url)
            .then(response => response.text())
            .then(data => {
                document.getElementById(file.targetId).innerHTML = data;
            })
            .catch(error => console.error(`Error loading ${file.url}:`, error))
    ));



    // 处理颜色选择器
    let colorInput = document.getElementById("themeColor");
    let colorPreview = document.getElementById("colorPreview");

    colorPreview.addEventListener("click", function () {
        colorInput.style.display = "block";
        colorInput.click();
    });

    colorInput.addEventListener("change", function () {
        colorPreview.style.background = colorInput.value;
    });

   


      // 获取 DOM 元素
      const fileInput = document.getElementById("file-input"); // Logo input
      const uploadBox = document.getElementById("upload-box"); // 点击区域
      const previewContainer = document.getElementById("preview-container"); // 预览容器
  
      // 点击上传框，打开文件选择框
      uploadBox.addEventListener("click", () => fileInput.click());
  
      // 监听文件选择，生成预览
      fileInput.addEventListener("change", handleImagePreview);
  
      function handleImagePreview(event) {
          const file = event.target.files[0]; // 获取用户选择的文件
          if (!file) return;
  
          const reader = new FileReader();
          reader.onload = (e) => {
              previewContainer.innerHTML = `
                  <img src="${e.target.result}" alt="Logo" style="max-width: 100px; height: auto;">
                  <button class="remove-btn" onclick="removePreview()">×</button>
              `;
          };
          reader.readAsDataURL(file);
      }
  
      // 删除 Logo 预览
      window.removePreview = function () {
          previewContainer.innerHTML = "";
          fileInput.value = ""; // 清空已选择的文件
      };

    
    // 处理 Category 图片预览
    let categoryImageInput = document.getElementById("categoryImage");
    let categoryImagePreview = document.getElementById("imagePreview");

    categoryImageInput.addEventListener("change", function (event) {
        let file = event.target.files[0];
        if (file) {
            let reader = new FileReader();
            reader.onload = function (e) {
                categoryImagePreview.src = e.target.result;
                categoryImagePreview.style.display = "block";
            };
            reader.readAsDataURL(file);
        }
    });
});

// 打开弹窗
function openCategoryModal() {
    document.getElementById("categoryModal").style.display = "block";
}

// 关闭弹窗
function closeCategoryModal() {
    document.getElementById("categoryModal").style.display = "none";
    document.getElementById("categoryName").value = "";
    document.getElementById("categoryDescription").value = "";
    document.getElementById("errorText").innerText = "";
}

// 添加分类
function addCategory() {
    let name = document.getElementById("categoryName").value.trim();
    let description = document.getElementById("categoryDescription").value.trim();
    let imagePreview = document.getElementById("imagePreview");

    if (!name || !description || imagePreview.src === "") {
        document.getElementById("errorText").innerText = "All fields are required!";
        return;
    }

    let categoryList = document.getElementById("categoryList");

    // 创建分类元素
    let categoryItem = document.createElement("div");
    categoryItem.classList.add("category-item");

    let img = document.createElement("img");
    img.src = imagePreview.src; 
    img.onload = function () {
        console.log("Image loaded successfully");
    };
    img.onerror = function () {
        console.error("Failed to load image");
    };

    let title = document.createElement("div");
    title.classList.add("category-name");
    title.innerText = name;

    let desc = document.createElement("div");
    desc.classList.add("category-desc");
    desc.innerText = description;

    let deleteBtn = document.createElement("button");
    deleteBtn.classList.add("delete-btn");
    deleteBtn.innerHTML = "✖️";
    deleteBtn.onclick = function () {
        categoryList.removeChild(categoryItem);
    };

    categoryItem.appendChild(img);
    categoryItem.appendChild(title);
    categoryItem.appendChild(desc);
    categoryItem.appendChild(deleteBtn);
    categoryList.appendChild(categoryItem);

    // 关闭弹窗
    closeCategoryModal();
}
