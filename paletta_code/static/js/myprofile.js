
function enableEdit() {
    document.getElementById('view-mode').style.display = 'none';
    document.getElementById('edit-mode').style.display = 'block';
}

function saveChanges() {
    const email = document.getElementById('email-input').value;
    const name = document.getElementById('name-input').value;
    const institutionText = document.getElementById('institution-text').value;

    if (!institutionText.trim()) {
        alert('Please fill out the institution name.');
        return;
    }

    document.getElementById('email-display').innerText = email;
    document.getElementById('name-display').innerText = name;
    document.getElementById('institution-display').innerText = institutionText;

    document.getElementById('view-mode').style.display = 'block';
    document.getElementById('edit-mode').style.display = 'none';
}

function togglePasswordVisibility(inputId, buttonId) {
    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);

    button.addEventListener('click', () => {
        if (input.type === 'password') {
            input.type = 'text';
            button.textContent = 'Hide';
        } else {
            input.type = 'password';
            button.textContent = 'Show';
        }
    });
}

function handleInstitutionChange() {
    document.getElementById('institution-text-container').style.display = 'block';
}

document.addEventListener('DOMContentLoaded', () => {
    togglePasswordVisibility('password-input', 'toggle-password');
    togglePasswordVisibility('confirm-password-input', 'toggle-confirm-password');
    document.querySelectorAll('input[name="institution"]').forEach(input => {
        input.addEventListener('change', handleInstitutionChange);
    });
});


