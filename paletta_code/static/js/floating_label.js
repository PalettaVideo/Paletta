function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    const floatingLabel = document.getElementById("floating-label");
  
    if (sidebar.classList.contains("active")) {
      closeSidebar();
    } else {
      sidebar.classList.add("active");
      overlay.style.opacity = "1";
      overlay.style.visibility = "visible";
      floatingLabel.style.display = "none"; // floating-label
    }
  }
  
  function closeSidebar() {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    const floatingLabel = document.getElementById("floating-label");
  
    sidebar.classList.remove("active");
    overlay.style.opacity = "0";
    overlay.style.visibility = "hidden";
    floatingLabel.style.display = "block"; // floating-label
  }
  