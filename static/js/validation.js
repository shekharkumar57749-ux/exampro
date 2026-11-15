/**
 * ExamPro - Advanced Examination Management System
 * Client-Side Validation & Password Strength Engine
 */

document.addEventListener('DOMContentLoaded', () => {
    initPasswordStrength();
    initRegistrationValidation();
});

function initPasswordStrength() {
    const pwdInput = document.getElementById('reg-password');
    const strengthBar = document.getElementById('password-strength-fill');
    const strengthText = document.getElementById('password-strength-text');

    if (!pwdInput || !strengthBar) return;

    pwdInput.addEventListener('input', (e) => {
        const val = e.target.value;
        const score = computeStrength(val);

        let color = '#ef4444';
        let label = 'Weak';
        let width = '25%';

        if (score >= 4) {
            color = '#10b981';
            label = 'Strong';
            width = '100%';
        } else if (score >= 3) {
            color = '#3b82f6';
            label = 'Good';
            width = '75%';
        } else if (score >= 2) {
            color = '#f59e0b';
            label = 'Fair';
            width = '50%';
        }

        strengthBar.style.width = width;
        strengthBar.style.backgroundColor = color;
        if (strengthText) {
            strengthText.textContent = label;
            strengthText.style.color = color;
        }
    });
}

function computeStrength(pwd) {
    if (!pwd) return 0;
    let score = 0;
    if (pwd.length >= 8) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[^A-Za-z0-9]/.test(pwd)) score++;
    return score;
}

function initRegistrationValidation() {
    const form = document.getElementById('registration-form');
    if (!form) return;

    form.addEventListener('submit', (e) => {
        const pwd = document.getElementById('reg-password')?.value;
        const confirmPwd = document.getElementById('reg-confirm-password')?.value;

        if (pwd !== confirmPwd) {
            e.preventDefault();
            showToast('Passwords do not match. Please re-enter.', 'danger');
            return false;
        }

        if (pwd && pwd.length < 6) {
            e.preventDefault();
            showToast('Password must be at least 6 characters long.', 'danger');
            return false;
        }
    });
}

