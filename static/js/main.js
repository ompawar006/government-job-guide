/**
 * main.js - Core UI utilities, Toast notifications, and global helpers
 */

// Toast notification helper
function showToast(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container-custom';
    document.body.appendChild(container);
  }

  const bgClasses = {
    'success': 'bg-success text-white',
    'danger': 'bg-danger text-white',
    'warning': 'bg-warning text-dark',
    'info': 'bg-primary text-white'
  };

  const toastEl = document.createElement('div');
  toastEl.className = `toast align-items-center ${bgClasses[type] || bgClasses.info} border-0 shadow-lg`;
  toastEl.setAttribute('role', 'alert');
  toastEl.setAttribute('aria-live', 'assertive');
  toastEl.setAttribute('aria-atomic', 'true');

  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body py-3 px-3">
        <i class="bi bi-${type === 'success' ? 'check-circle-fill' : type === 'danger' ? 'exclamation-triangle-fill' : 'info-circle-fill'} me-2"></i>
        ${escapeHTML(message)}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  `;

  container.appendChild(toastEl);
  const bsToast = new bootstrap.Toast(toastEl, { delay: 4000 });
  bsToast.show();

  toastEl.addEventListener('hidden.bs.toast', () => {
    toastEl.remove();
  });
}

// HTML escape helper
function escapeHTML(str) {
  if (!str) return '';
  const p = document.createElement('p');
  p.appendChild(document.createTextNode(str));
  return p.innerHTML;
}

// Copy to clipboard helper
async function copyToClipboard(text, btnElement = null) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
    } else {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      document.execCommand('copy');
      textArea.remove();
    }

    if (btnElement) {
      const origHTML = btnElement.innerHTML;
      btnElement.innerHTML = '<i class="bi bi-check2"></i> Copied!';
      btnElement.classList.add('text-success');
      setTimeout(() => {
        btnElement.innerHTML = origHTML;
        btnElement.classList.remove('text-success');
      }, 2000);
    } else {
      showToast('Copied to clipboard!', 'success');
    }
  } catch (err) {
    console.error('Failed to copy: ', err);
    showToast('Failed to copy text.', 'danger');
  }
}

// Save guidance item to backend
async function saveGuidanceItem(title, category, content, btnElement = null) {
  try {
    const res = await fetch('/api/saved', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, category, content })
    });

    if (res.status === 401) {
      showToast('Please sign in to save guidance to your profile.', 'warning');
      return;
    }

    const data = await res.json();
    if (res.ok && data.success) {
      if (btnElement) {
        btnElement.innerHTML = '<i class="bi bi-bookmark-check-fill text-success"></i> Saved!';
        btnElement.disabled = true;
      }
      showToast('Guidance saved to your account!', 'success');
    } else {
      showToast(data.error || 'Failed to save guidance.', 'danger');
    }
  } catch (err) {
    console.error('Error saving guidance:', err);
    showToast('Network error while saving.', 'danger');
  }
}

// Initialize tooltips on load
document.addEventListener('DOMContentLoaded', () => {
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
});
