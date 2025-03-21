/* script.js */
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


    
    const modal = document.getElementById("adminModal");
    const addAdminBtn = document.getElementById("addAdmin");
    const closeModal = document.querySelector(".close");
    const confirmAddBtn = document.getElementById("confirmAdd");
    
    addAdminBtn.addEventListener("click", function () {
        modal.style.display = "flex";
    });
    
    closeModal.addEventListener("click", function () {
        modal.style.display = "none";
    });
    
    window.addEventListener("click", function (event) {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    });
    
    confirmAddBtn.addEventListener("click", function () {
        const name = document.getElementById("adminName").value;
        const email = document.getElementById("adminEmail").value;
        
        if (name.trim() === "" || email.trim() === "") {
            alert("Please fill out all fields.");
            return;
        }
        
        const adminList = document.getElementById("adminList");
        const newAdmin = document.createElement("div");
        newAdmin.classList.add("admin-card");
        newAdmin.innerHTML = `
            <p><strong>Name:</strong> ${name}</p>
            <p><strong>Email:</strong> ${email}</p>
            <p><strong>Library Name:</strong> N/A</p>
            <button class="revoke">Revoke Admin Privileges</button>
        `;
        
        adminList.appendChild(newAdmin);
        modal.style.display = "none";
        document.getElementById("adminName").value = "";
        document.getElementById("adminEmail").value = "";
    });
});
