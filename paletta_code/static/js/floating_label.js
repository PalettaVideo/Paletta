// Wait for the DOM to load
document.addEventListener("DOMContentLoaded", function () {
  // Initialize floating label functionality
  initFloatingUI();
});

// Initialize floating UI elements
function initFloatingUI() {
  // Check if elements exist
  const sidebar = document.getElementById("sidebar-floating");
  const overlay = document.getElementById("sidebar-floating-overlay");
  const floatingLabel = document.getElementById("floating-label");

  if (!sidebar || !overlay || !floatingLabel) {
    console.log("Floating sidebar elements not found on this page");
    return;
  }

  console.log("Floating sidebar initialized");

  // Make sure floating label is visible initially
  floatingLabel.style.display = "block";

  // Add click event listener to close when clicking outside sidebar
  document.addEventListener("click", function (event) {
    const sidebarComponent = document.getElementById("sidebar-component");

    // If sidebar is active and click is outside the sidebar component
    if (
      sidebar.classList.contains("active") &&
      sidebarComponent &&
      !sidebarComponent.contains(event.target)
    ) {
      closeSidebar();
    }
  });

  // Prevent clicks inside sidebar from closing it
  sidebar.addEventListener("click", function (event) {
    event.stopPropagation();
  });

  // Prevent clicks on floating label from triggering document click
  floatingLabel.addEventListener("click", function (event) {
    event.stopPropagation();
  });
}

// Toggle sidebar visibility
function toggleSidebar() {
  const sidebar = document.getElementById("sidebar-floating");
  const overlay = document.getElementById("sidebar-floating-overlay");
  const floatingLabel = document.getElementById("floating-label");

  if (!sidebar || !overlay || !floatingLabel) {
    console.error("Floating sidebar elements not found");
    return;
  }

  if (sidebar.classList.contains("active")) {
    closeSidebar();
  } else {
    sidebar.classList.add("active");
    overlay.style.opacity = "1";
    overlay.style.visibility = "visible";
    floatingLabel.style.display = "none"; // hide floating label
  }
}

// Close sidebar
function closeSidebar() {
  const sidebar = document.getElementById("sidebar-floating");
  const overlay = document.getElementById("sidebar-floating-overlay");
  const floatingLabel = document.getElementById("floating-label");

  if (!sidebar || !overlay || !floatingLabel) {
    console.error("Floating sidebar elements not found");
    return;
  }

  sidebar.classList.remove("active");
  overlay.style.opacity = "0";
  overlay.style.visibility = "hidden";
  floatingLabel.style.display = "block"; // show floating label
}
