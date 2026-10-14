/**
 * auth.js - Client-side validation for Registration and Login forms
 */

document.addEventListener('DOMContentLoaded', () => {
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    const passwordInput = document.getElementById('password');
    const confirmInput = document.getElementById('confirm_password');
    const matchFeedback = document.getElementById('passwordMatchFeedback');

    function checkPasswords() {
      if (!confirmInput.value) {
        if (matchFeedback) matchFeedback.textContent = '';
        return;
      }
      if (passwordInput.value !== confirmInput.value) {
        confirmInput.classList.add('is-invalid');
        confirmInput.classList.remove('is-valid');
        if (matchFeedback) {
          matchFeedback.textContent = 'Passwords do not match';
          matchFeedback.className = 'invalid-feedback d-block';
        }
      } else {
        confirmInput.classList.remove('is-invalid');
        confirmInput.classList.add('is-valid');
        if (matchFeedback) {
          matchFeedback.textContent = 'Passwords match';
          matchFeedback.className = 'valid-feedback d-block';
        }
      }
    }

    if (passwordInput && confirmInput) {
      passwordInput.addEventListener('input', checkPasswords);
      confirmInput.addEventListener('input', checkPasswords);
    }

    registerForm.addEventListener('submit', (e) => {
      if (passwordInput.value !== confirmInput.value) {
        e.preventDefault();
        showToast('Passwords do not match. Please verify.', 'danger');
        confirmInput.focus();
        return false;
      }
      if (passwordInput.value.length < 6) {
        e.preventDefault();
        showToast('Password must be at least 6 characters long.', 'danger');
        passwordInput.focus();
        return false;
      }
    });
  }

  // Demo fill helper for easy testing
  const demoFillBtn = document.getElementById('demoFillBtn');
  if (demoFillBtn) {
    demoFillBtn.addEventListener('click', () => {
      const emailField = document.getElementById('email');
      const passField = document.getElementById('password');
      if (emailField && passField) {
        emailField.value = 'candidate@example.com';
        passField.value = 'Candidate@123';
        showToast('Test credentials filled!', 'info');
      }
    });
  }
});
