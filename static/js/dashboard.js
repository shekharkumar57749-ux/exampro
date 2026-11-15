/**
 * ExamPro - Advanced Examination Management System
 * Dashboard Interactions, Data Table Filters, and Multi-Step Wizard
 */

document.addEventListener('DOMContentLoaded', () => {
    initTableSearch();
    initMultiStepWizard();
    initDeleteConfirmations();
});

/* ========================================================
   Instant Table Search Filter
   ======================================================== */
function initTableSearch() {
    const searchInputs = document.querySelectorAll('.table-search-input');
    searchInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            const targetTableId = input.getAttribute('data-table');
            const table = document.getElementById(targetTableId);
            if (!table) return;

            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        });
    });
}

/* ========================================================
   Multi-Step Exam Creation Wizard
   ======================================================== */
function initMultiStepWizard() {
    const wizardForm = document.getElementById('exam-wizard-form');
    if (!wizardForm) return;

    let currentStep = 1;
    const totalSteps = 4;

    const stepElements = document.querySelectorAll('.wizard-step');
    const stepPanes = document.querySelectorAll('.wizard-pane');
    const btnNext = document.getElementById('wizard-btn-next');
    const btnPrev = document.getElementById('wizard-btn-prev');
    const btnSubmit = document.getElementById('wizard-btn-submit');

    function updateStepUI() {
        stepElements.forEach(el => {
            const stepNum = parseInt(el.getAttribute('data-step'));
            el.classList.remove('active', 'completed');
            if (stepNum === currentStep) el.classList.add('active');
            if (stepNum < currentStep) el.classList.add('completed');
        });

        stepPanes.forEach(pane => {
            const paneStep = parseInt(pane.getAttribute('data-step'));
            pane.style.display = (paneStep === currentStep) ? 'block' : 'none';
        });

        if (btnPrev) btnPrev.style.display = (currentStep > 1) ? 'inline-flex' : 'none';
        if (btnNext) btnNext.style.display = (currentStep < totalSteps) ? 'inline-flex' : 'none';
        if (btnSubmit) btnSubmit.style.display = (currentStep === totalSteps) ? 'inline-flex' : 'none';

        // Update preview in final step
        if (currentStep === totalSteps) {
            populateWizardPreview();
        }
    }

    if (btnNext) {
        btnNext.addEventListener('click', () => {
            if (validateStep(currentStep)) {
                currentStep++;
                updateStepUI();
            }
        });
    }

    if (btnPrev) {
        btnPrev.addEventListener('click', () => {
            if (currentStep > 1) {
                currentStep--;
                updateStepUI();
            }
        });
    }

    function validateStep(step) {
        if (step === 1) {
            const title = document.getElementById('exam-title-input').value.trim();
            const code = document.getElementById('exam-code-input').value.trim();
            if (!title || !code) {
                showToast('Please enter Examination Title and Exam Code.', 'warning');
                return false;
            }
        } else if (step === 2) {
            const selectedQ = document.querySelectorAll('input[name="selected_questions[]"]:checked');
            if (selectedQ.length === 0) {
                showToast('Please select at least 1 question for this examination.', 'warning');
                return false;
            }
        }
        return true;
    }

    function populateWizardPreview() {
        const titleEl = document.getElementById('preview-title');
        const codeEl = document.getElementById('preview-code');
        const countEl = document.getElementById('preview-count');
        const durEl = document.getElementById('preview-duration');

        const selectedQ = document.querySelectorAll('input[name="selected_questions[]"]:checked');
        if (titleEl) titleEl.textContent = document.getElementById('exam-title-input').value;
        if (codeEl) codeEl.textContent = document.getElementById('exam-code-input').value;
        if (countEl) countEl.textContent = selectedQ.length;
        if (durEl) durEl.textContent = document.getElementById('exam-duration-input').value + ' mins';
    }

    updateStepUI();
}

/* ========================================================
   Action Confirmations
   ======================================================== */
function initDeleteConfirmations() {
    document.querySelectorAll('[data-confirm]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const msg = btn.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
            if (!confirm(msg)) {
                e.preventDefault();
            }
        });
    });
}

