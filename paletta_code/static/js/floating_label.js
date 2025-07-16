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

  // Get user role from meta tag or data attribute
  function getUserRole() {
    const metaUserRole = document.querySelector('meta[name="user-role"]');
    return metaUserRole ? metaUserRole.getAttribute("content") : "user";
  }

  // Check if user has admin/owner permissions
  function hasAdminPermissions() {
    const userRole = getUserRole();
    return userRole === "owner" || userRole === "admin";
  }

  // Show permission denied popup
  function showPermissionDeniedPopup() {
    alert(
      "Only Library Admin or Owner can access these pages. Enjoy exploring other libraries!"
    );
  }

  // Add permission checks to admin navigation buttons
  function addPermissionChecks() {
    const adminButtons = document.querySelectorAll(".admin-nav-btn a");

    adminButtons.forEach((link) => {
      link.addEventListener("click", function (e) {
        if (!hasAdminPermissions()) {
          e.preventDefault();
          e.stopPropagation();
          showPermissionDeniedPopup();
          return false;
        }
        // If they have permission, let the navigation proceed normally
      });
    });
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

  // Initialize permission checks when DOM is loaded
  addPermissionChecks();
});
