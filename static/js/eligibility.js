/**
 * eligibility.js - Interactive Eligibility Guidance Tool Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('eligibilityForm');
  const qualificationSelect = document.getElementById('qualification');
  const branchContainer = document.getElementById('branchContainer');
  const resultCard = document.getElementById('eligibilityResultCard');
  const resultContent = document.getElementById('eligibilityResultContent');
  const submitBtn = document.getElementById('btnCheckEligibility');
  const saveBtn = document.getElementById('btnSaveEligibility');

  let currentRawReport = '';

  // Show/hide branch field dynamically based on qualification
  if (qualificationSelect && branchContainer) {
    qualificationSelect.addEventListener('change', () => {
      const val = qualificationSelect.value;
      if (val === 'B.Tech / B.E. (Engineering)' || val === 'Diploma / Polytechnic') {
        branchContainer.style.display = 'block';
      } else {
        branchContainer.style.display = 'none';
        const branchInput = document.getElementById('branch');
        if (branchInput) branchInput.value = 'N/A';
      }
    });
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const qualification = qualificationSelect ? qualificationSelect.value : '';
      if (!qualification) {
        showToast('Please select your highest qualification.', 'warning');
        return;
      }

      const studyStatus = document.getElementById('study_status')?.value || 'Completed';
      const branch = document.getElementById('branch')?.value || 'N/A';
      const age = parseInt(document.getElementById('age')?.value || '21', 10);
      const state = document.getElementById('state')?.value || 'All India';
      const department = document.getElementById('department')?.value || 'Any';
      const careerPreference = document.getElementById('career_preference')?.value || 'Both Technical and Non-Technical';

      // UI Loading state
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Analyzing Career Eligibility...';
      }

      if (resultCard) {
        resultCard.style.display = 'block';
        resultContent.innerHTML = `
          <div class="text-center py-5">
            <div class="spinner-grow text-primary mb-3" role="status"></div>
            <h5 class="fw-bold">Evaluating Recruitment Opportunities</h5>
            <p class="text-muted small">Cross-referencing qualification rules, central & state age criteria, and exams...</p>
          </div>
        `;
        resultCard.scrollIntoView({ behavior: 'smooth' });
      }

      try {
        const response = await fetch('/api/eligibility', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            qualification,
            study_status: studyStatus,
            branch,
            age,
            state,
            department,
            career_preference: careerPreference
          })
        });

        const data = await response.json();

        if (response.ok && data && data.report) {
          currentRawReport = data.report;
          let html = '';
          if (typeof marked !== 'undefined' && typeof DOMPurify !== 'undefined') {
            html = DOMPurify.sanitize(marked.parse(data.report));
          } else {
            html = escapeHTML(data.report).replace(/\n/g, '<br>');
          }

          resultContent.innerHTML = `
            <div class="markdown-body">
              ${html}
            </div>
          `;

          if (saveBtn) {
            saveBtn.style.display = 'inline-flex';
            saveBtn.innerHTML = '<i class="bi bi-bookmark-plus me-1"></i> Save Recommendation';
            saveBtn.disabled = false;
          }
        } else {
          resultContent.innerHTML = `
            <div class="alert alert-danger">
              <i class="bi bi-exclamation-triangle-fill me-2"></i>
              ${escapeHTML(data.error || 'Failed to generate eligibility report. Please try again.')}
            </div>
          `;
        }
      } catch (err) {
        console.error('Error fetching eligibility report:', err);
        resultContent.innerHTML = `
          <div class="alert alert-danger">
            <i class="bi bi-wifi-off me-2"></i>
            Network error. Unable to connect to career evaluation service.
          </div>
        `;
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<i class="bi bi-compass me-2"></i> Analyze My Eligibility';
        }
      }
    });
  }

  // Save report action
  if (saveBtn) {
    saveBtn.addEventListener('click', () => {
      if (!currentRawReport) return;
      const title = `Eligibility Guidance (${qualificationSelect ? qualificationSelect.value : 'Profile'})`;
      saveGuidanceItem(title, 'Eligibility Tool', currentRawReport, saveBtn);
    });
  }
});
