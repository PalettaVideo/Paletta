// Wait for the DOM to load
document.addEventListener("DOMContentLoaded", function () {
  const floatingLabel = document.getElementById("floating-label");
  const sidebar = document.getElementById("sidebar-floating");
  const closeBtn = document.getElementById("close-sidebar-btn");
  const overlay = document.getElementById("sidebar-floating-overlay");

  // ensure all required elements are present on the page
  if (!floatingLabel || !sidebar || !closeBtn || !overlay) {
    return;
  }

  // open the sidebar
  const openSidebar = () => {
    sidebar.classList.add("active");
    overlay.classList.add("active");
    floatingLabel.style.display = "none";
  };

  // close the sidebar
  const closeSidebar = () => {
    sidebar.classList.remove("active");
    overlay.classList.remove("active");
    floatingLabel.style.display = "block";
  };

  // event listeners
  floatingLabel.addEventListener("click", (e) => {
    e.stopPropagation();
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
