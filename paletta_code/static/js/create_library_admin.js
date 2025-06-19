document.addEventListener("DOMContentLoaded", function () {
  // Get CSRF token for Django form submissions
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const csrftoken = getCookie("csrftoken");

  // Handle color picker
  let colorInput = document.getElementById("themeColor");
  let colorPreview = document.getElementById("colorPreview");

  // Set initial color preview
  colorPreview.style.background = colorInput.value || "#86B049";

  // Toggle color picker when clicking on color preview
  window.toggleColorPicker = function () {
    colorInput.click();
  };

  // Update color preview when color changes
  window.updateColor = function () {
    colorPreview.style.background = colorInput.value;
  };

  // Handle logo upload
  const fileInput = document.getElementById("file-input");
  const uploadBox = document.getElementById("upload-box");
  const previewContainer = document.getElementById("preview-container");

  uploadBox.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", handleImagePreview);

  function handleImagePreview(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      previewContainer.innerHTML = `
                <img src="${e.target.result}" alt="Logo" style="max-width: 100px; height: auto;">
                <button type="button" class="remove-btn" onclick="removePreview()">×</button>
            `;
    };
    reader.readAsDataURL(file);
  }

  // Remove logo preview
  window.removePreview = function () {
    previewContainer.innerHTML = "";
    fileInput.value = "";
  };

  // Handle category source selection and preview updates
  const categorySourceRadios = document.querySelectorAll(
    'input[name="category_source"]'
  );
  const previewContent = document.getElementById("preview-content");

  // Category structure data
  const categoryStructures = {
    paletta_style: {
      title: "Paletta Style Categories",
      sections: [
        {
          label: "Paletta Categories",
          description:
            "People & Community, Buildings & Architecture, Classrooms & Learning Spaces, Field Trips & Outdoor Learning, Events & Conferences, Research & Innovation Spaces, Technology & Equipment, Everyday Campus Life, Urban & Natural Environments, Backgrounds & Abstracts",
          required: "1 per video",
        },
        {
          label: "Content Types",
          description:
            "Campus Life, Teaching & Learning, Research & Innovation, City & Environment, Aerial & Establishing Shots, People & Portraits, Culture & Events, Workspaces & Facilities, Cutaways & Abstracts, Historical & Archive",
          required: "1-3 per video",
        },
        {
          label: "Tags",
          description: "Optional custom tags for additional organization",
          required: "Optional",
        },
      ],
    },
    custom: {
      title: "Custom Academic Categories",
      sections: [
        {
          label: "Subject Areas",
          description:
            "Engineering Sciences, Mathematical & Physical Sciences, Medical Sciences, Life Sciences, Brain Sciences, Built Environment, Population Health, Arts & Humanities, Social & Historical Sciences, Education, Fine Art, Law, Business",
          required: "1 per video",
        },
        {
          label: "Content Types",
          description:
            "Campus Life, Teaching & Learning, Research & Innovation, City & Environment, Aerial & Establishing Shots, People & Portraits, Culture & Events, Workspaces & Facilities, Cutaways & Abstracts, Historical & Archive",
          required: "1-3 per video",
        },
        {
          label: "Tags",
          description: "Optional custom tags for additional organization",
          required: "Optional",
        },
      ],
    },
  };

  // Update preview when radio selection changes
  function updateCategoryPreview() {
    const selectedSource = document.querySelector(
      'input[name="category_source"]:checked'
    )?.value;

    if (!selectedSource || !categoryStructures[selectedSource]) return;

    const structure = categoryStructures[selectedSource];

    previewContent.innerHTML = `
      <h5>${structure.title}</h5>
      ${structure.sections
        .map(
          (section) => `
        <div class="preview-section">
          <strong>${section.label}:</strong> ${section.description}
          <span class="requirement">(${section.required})</span>
        </div>
      `
        )
        .join("")}
    `;
  }

  // Add event listeners to radio buttons
  categorySourceRadios.forEach((radio) => {
    radio.addEventListener("change", updateCategoryPreview);
  });

  // Initialize preview
  updateCategoryPreview();

  // Form submission handling
  const libraryForm = document.getElementById("library-form");
  if (libraryForm) {
    libraryForm.addEventListener("submit", async function (event) {
      event.preventDefault();

      // Validate form
      if (!validateForm()) {
        return;
      }

      // Create FormData object
      const formData = new FormData(libraryForm);

      // Debug form data
      console.log("Form submission data:");
      for (let pair of formData.entries()) {
        console.log(`${pair[0]}: ${pair[1]}`);
      }

      try {
        const response = await fetch(
          libraryForm.action || window.location.href,
          {
            method: "POST",
            headers: {
              "X-CSRFToken": csrftoken,
              // Don't set Content-Type here, FormData will set it with boundary
            },
            body: formData,
          }
        );

        // Debug response
        console.log("Response status:", response.status);

        if (
          response.headers.get("content-type")?.includes("application/json")
        ) {
          const data = await response.json();
          console.log("Response data:", data);

          if (data.status === "success") {
            // Show success message
            alert(data.message);
            // Redirect to manage libraries page
            window.location.href = data.redirect_url;
          } else {
            // Show error message
            alert("Error: " + JSON.stringify(data.message));
          }
        } else {
          // Handle non-JSON response (likely a redirect or HTML response)
          if (response.ok) {
            // Successful submission, redirect to manage libraries
            window.location.href = "/libraries/manage/";
          } else {
            const text = await response.text();
            console.error("Server response:", text);
            alert(
              "An error occurred while creating the library. Please check your input and try again."
            );
          }
        }
      } catch (error) {
        console.error("Error:", error);
        alert(
          "An error occurred while creating the library. Please try again."
        );
      }
    });
  }

  function validateForm() {
    const nameField = document.getElementById("id_name");
    const descriptionField = document.getElementById("id_description");
    const categorySourceField = document.querySelector(
      'input[name="category_source"]:checked'
    );

    if (!nameField.value.trim()) {
      alert("Please enter a library name");
      nameField.focus();
      return false;
    }

    if (!descriptionField.value.trim()) {
      alert("Please enter a library description");
      descriptionField.focus();
      return false;
    }

    if (!categorySourceField) {
      alert("Please select a category management option");
      return false;
    }

    return true;
  }
});
