document.addEventListener("DOMContentLoaded", function () {


        fetch("./footer.html")
            .then(response => response.text())
            .then(data => {
                document.getElementById("footer").innerHTML = data;
            })
            .catch(error => console.error("Error loading footer:", error));


    let colorInput = document.getElementById("themeColor");
    colorInput.addEventListener("change", function () {
        document.body.style.backgroundColor = colorInput.value;
    });

    let logoUpload = document.getElementById("logoUpload");
    let libraryLogo = document.getElementById("libraryLogo");
    
    document.querySelector(".change-btn").addEventListener("click", function () {
        logoUpload.click();
    });

    logoUpload.addEventListener("change", function (event) {
        let file = event.target.files[0];
        if (!file) return;

        let reader = new FileReader();
        reader.onload = (e) => {
            libraryLogo.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });

    function toggleEdit(fieldId, button) {
        let field = document.getElementById(fieldId);

        if (field.hasAttribute('readonly')) {
            field.removeAttribute('readonly');
            field.focus();
            button.textContent = "Save";
        } else {
            field.setAttribute('readonly', true);
            console.log(`Updated ${fieldId}:`, field.value);
            button.textContent = "Edit";
        }
    }
    window.toggleEdit = toggleEdit;

    let editingCategory = null;

    window.openCategoryModal = function () {
        document.getElementById("categoryModalTitle").innerText = "add a category";
        document.getElementById("categoryName").value = "";
        document.getElementById("categoryDescription").value = "";
        document.getElementById("imagePreview").src = "";
        document.getElementById("imagePreview").style.display = "none";
        document.getElementById("saveCategoryBtn").innerText = "add";
        editingCategory = null;
    
        document.getElementById("categoryModal").style.display = "block";
    };
    
    window.closeCategoryModal = function () {
        document.getElementById("categoryModal").style.display = "none";
    };
    
    window.editCategoryModal = function (event, categoryItem) {
        if (event.target.classList.contains("delete-btn")) {
            return;
        }

        editingCategory = categoryItem;
    
        document.getElementById("categoryModalTitle").innerText = "Edit Category";
        document.getElementById("categoryName").value = categoryItem.querySelector(".category-name").innerText;
        document.getElementById("categoryDescription").value = categoryItem.querySelector(".category-desc").innerText;
    
        let img = categoryItem.querySelector("img");
        if (img) {
            document.getElementById("imagePreview").src = img.src;
            document.getElementById("imagePreview").style.display = "block";
        }
    
        document.getElementById("saveCategoryBtn").innerText = "Save";
        document.getElementById("categoryModal").style.display = "block";
    };
    
    document.getElementById("categoryImage").addEventListener("change", function (event) {
        let file = event.target.files[0];
        if (file) {
            let reader = new FileReader();
            reader.onload = function (e) {
                document.getElementById("imagePreview").src = e.target.result;
                document.getElementById("imagePreview").style.display = "block";
            };
            reader.readAsDataURL(file);
        }
    });
    
    window.saveCategory = function () {
        let name = document.getElementById("categoryName").value.trim();
        let description = document.getElementById("categoryDescription").value.trim();
        let imagePreview = document.getElementById("imagePreview");
    
        if (!name || !description || imagePreview.src === "") {
            alert("All fields are required!");
            return;
        }
    
        if (editingCategory) {
            editingCategory.querySelector(".category-name").innerText = name;
            editingCategory.querySelector(".category-desc").innerText = description;
            if (imagePreview.src) {
                editingCategory.querySelector("img").src = imagePreview.src;
            }
        } else {
            let categoryList = document.getElementById("categoryList");
            let categoryItem = document.createElement("div");
            categoryItem.classList.add("category-item");
            categoryItem.onclick = function (event) { editCategoryModal(event, categoryItem); };
    
            let img = document.createElement("img");
            img.src = imagePreview.src;
            
    
            let title = document.createElement("div");
            title.classList.add("category-name");
            title.innerText = name;
    
            let desc = document.createElement("div");
            desc.classList.add("category-desc");
            desc.innerText = description;
    
            let deleteBtn = document.createElement("button");
            deleteBtn.classList.add("delete-btn");
            deleteBtn.innerHTML = "✖️";
            deleteBtn.onclick = function (event) {
                event.stopPropagation();
                categoryList.removeChild(categoryItem);
            };
    
            categoryItem.appendChild(img);
            categoryItem.appendChild(title);
            categoryItem.appendChild(desc);
            categoryItem.appendChild(deleteBtn);
            categoryList.appendChild(categoryItem);
        }
    
        closeCategoryModal();
    };



    window.openContributorModal = function() {
        document.getElementById("contributorModal").style.display = "block";
        document.getElementById("modalOverlay").style.display = "block";
    };
    
    window.closeContributorModal = function() {
        document.getElementById("contributorModal").style.display = "none";
        document.getElementById("modalOverlay").style.display = "none";
    };
    
    window.addContributor = function() {
        let name = document.getElementById("contributorName").value;
        let email = document.getElementById("contributorEmail").value;
        if (!name || !email) {
            alert("Please fill in all fields");
            return;
        }
    
        let contributorList = document.getElementById("contributorList");
        let contributorItem = document.createElement("div");
        contributorItem.classList.add("contributor-item");
        contributorItem.innerHTML = `
            <span>Name: ${name} | Email: ${email}</span>
            <button class="delete-btn" onclick="this.parentElement.remove()">Remove</button>
        `;
        contributorList.appendChild(contributorItem);
    
        document.getElementById("contributorName").value = "";
        document.getElementById("contributorEmail").value = "";
        closeContributorModal();
    };
    
    



});
