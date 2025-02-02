
function openRequestModal() {
    document.getElementById('requestModal').style.display = 'block';
}

function closeRequestModal() {
    document.getElementById('requestModal').style.display = 'none';
}

function confirmRequest() {
    alert('The clip link has been sent to your email.');
    closeRequestModal();
}
