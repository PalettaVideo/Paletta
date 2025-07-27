// Functions to handle the request modal
function openRequestModal(detailId) {
  document.getElementById("detail-id").value = detailId;
  document.getElementById("requestModal").style.display = "flex";
}

function closeRequestModal() {
  document.getElementById("requestModal").style.display = "none";
}

function confirmRequest() {
  const detailId = document.getElementById("detail-id").value;
  const reason = document.querySelector("textarea").value;
  // Get CSRF token from the form or meta tag
  const csrfToken =
    document.querySelector("[name=csrfmiddlewaretoken]")?.value ||
    document.querySelector('meta[name="csrf-token"]')?.content ||
    "";

  // Get URL by constructing it with the detail ID
  const url = `/api/orders/request-download/`;

  // Send request to server to reprocess the download
  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify({
      reason: reason,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert("Your request has been submitted. We will process it shortly.");
        closeRequestModal();
        window.location.reload();
      } else {
        alert("Error: " + data.message);
      }
    })
    .catch(() => {
      alert("An error occurred while submitting your request.");
    });
}
