// Wait for the DOM to load
document.addEventListener("DOMContentLoaded", function () {
  const floatingLabel = document.getElementById("floating-label");
  const sidebar = document.getElementById("sidebar-floating");
  const closeBtn = document.getElementById("close-sidebar-btn");
  const overlay = document.getElementById("sidebar-floating-overlay");

  // Ensure all required elements are present on the page
  if (!floatingLabel || !sidebar || !closeBtn || !overlay) {
    return;
  }

  // Function to open the sidebar
  const openSidebar = () => {
    sidebar.classList.add("active");
    overlay.classList.add("active");
    floatingLabel.style.display = "none";
  };

  // Function to close the sidebar
  const closeSidebar = () => {
    sidebar.classList.remove("active");
    overlay.classList.remove("active");
    floatingLabel.style.display = "block";
  };

  // Event listeners
  floatingLabel.addEventListener("click", (e) => {
    e.stopPropagation(); // Prevent the click from bubbling up to the document
    openSidebar();
  });

  closeBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    closeSidebar();
  });

  overlay.addEventListener("click", (e) => {
    e.stopPropagation();
    closeSidebar();
  });
});
