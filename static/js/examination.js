/**
 * ExamPro - Advanced Examination Management System
 * Interactive Examination Room Controller
 * Auto-Save, Countdown Timer, Security Proctoring, and Question Palette
 */

class ExaminationEngine {
    constructor(config) {
        this.attemptId = config.attemptId;
        this.examId = config.examId;
        this.questions = config.questions || [];
        this.answersMap = config.answersMap || {};
        this.remainingSeconds = config.remainingSeconds || 3600;
        this.currentIndex = 0;
        this.autoSaveTimer = null;
        this.violationCount = 0;
        this.maxViolations = 3;
        this.isSubmitted = false;

        this.init();
    }

    init() {
        if (this.questions.length === 0) return;

        this.renderQuestion(0);
        this.startTimer();
        this.bindEvents();
        this.initProctoring();
        this.updatePaletteSummary();
    }

    bindEvents() {
        // Navigation buttons
        const btnPrev = document.getElementById('btn-prev');
        const btnNext = document.getElementById('btn-next');
        const btnClear = document.getElementById('btn-clear');
        const btnReview = document.getElementById('btn-review');
        const btnSubmit = document.getElementById('btn-submit-exam');

        if (btnPrev) btnPrev.addEventListener('click', () => this.navigate(this.currentIndex - 1));
        if (btnNext) btnNext.addEventListener('click', () => this.navigate(this.currentIndex + 1));
        if (btnClear) btnClear.addEventListener('click', () => this.clearCurrentAnswer());
        if (btnReview) btnReview.addEventListener('click', () => this.toggleMarkForReview());
        if (btnSubmit) btnSubmit.addEventListener('click', () => this.promptSubmit());

        // Keyboard Shortcuts
        document.addEventListener('keydown', (e) => {
            if (this.isSubmitted) return;
            // Don't trigger if focus is on descriptive textarea or text input
            if (['input', 'textarea'].includes(document.activeElement.tagName.toLowerCase())) return;

            if (e.key === 'ArrowRight' || e.key === 'n') {
                if (this.currentIndex < this.questions.length - 1) this.navigate(this.currentIndex + 1);
            } else if (e.key === 'ArrowLeft' || e.key === 'p') {
                if (this.currentIndex > 0) this.navigate(this.currentIndex - 1);
            } else if (e.key === 'm') {
                this.toggleMarkForReview();
            }
        });

        // Fullscreen Toggle
        const fsBtn = document.getElementById('btn-fullscreen');
        if (fsBtn) {
            fsBtn.addEventListener('click', () => this.toggleFullscreen());
        }
    }

    /* ========================================================
       Question Rendering & Selection Logic
       ======================================================== */
    renderQuestion(index) {
        if (index < 0 || index >= this.questions.length) return;

        // Auto-save previous answer before switching
        this.triggerSave();

        this.currentIndex = index;
        const q = this.questions[index];
        const ans = this.answersMap[q.id] || { selected_option_ids: '', text_answer: '', is_marked_for_review: 0, is_answered: 0 };
        
        // Mark as visited
        ans.is_visited = 1;
        this.answersMap[q.id] = ans;

        // Update header info
        const qNumEl = document.getElementById('q-number-display');
        const qTotalEl = document.getElementById('q-total-display');
        const qTypeEl = document.getElementById('q-type-badge');
        const qMarksEl = document.getElementById('q-marks-display');
        const qNegEl = document.getElementById('q-negative-display');
        const qTextEl = document.getElementById('q-text-display');
        const optionsContainer = document.getElementById('q-options-container');

        if (qNumEl) qNumEl.textContent = `Question ${index + 1}`;
        if (qTotalEl) qTotalEl.textContent = `of ${this.questions.length}`;
        if (qTypeEl) qTypeEl.textContent = q.question_type.replace('_', ' ').toUpperCase();
        if (qMarksEl) qMarksEl.textContent = `+${q.marks || 1} Marks`;
        if (qNegEl) qNegEl.textContent = q.negative_marks > 0 ? `-${q.negative_marks} Neg` : 'No Negative';
        if (qTextEl) qTextEl.innerHTML = q.question_text;

        // Optional image
        const imgContainer = document.getElementById('q-image-container');
        if (imgContainer) {
            if (q.image_url) {
                imgContainer.innerHTML = `<img src="${q.image_url}" class="question-image" alt="Question Diagram" />`;
                imgContainer.style.display = 'block';
            } else {
                imgContainer.style.display = 'none';
            }
        }

        // Render input format based on question type
        this.renderOptions(q, ans, optionsContainer);

        // Update button states
        const btnPrev = document.getElementById('btn-prev');
        const btnNext = document.getElementById('btn-next');
        if (btnPrev) btnPrev.disabled = (index === 0);
        if (btnNext) {
            btnNext.textContent = (index === this.questions.length - 1) ? 'Review & Submit' : 'Next Question';
            btnNext.onclick = (index === this.questions.length - 1) ? () => this.promptSubmit() : () => this.navigate(this.currentIndex + 1);
        }

        // Update palette active highlight
        this.updatePaletteButton(q.id);
        this.updateProgressBar();
    }

    renderOptions(q, ans, container) {
        if (!container) return;
        container.innerHTML = '';

        const selectedSet = new Set((ans.selected_option_ids || '').split(',').map(s => s.trim()));

        if (q.question_type === 'single_choice' || q.question_type === 'true_false') {
            const list = document.createElement('div');
            list.className = 'options-list';

            (q.options || []).forEach(opt => {
                const card = document.createElement('div');
                const isSelected = selectedSet.has(String(opt.id));
                card.className = `option-card ${isSelected ? 'selected' : ''}`;
                card.innerHTML = `
                    <div class="option-indicator">
                        ${isSelected ? '<i class="fas fa-check" style="font-size:0.65rem;"></i>' : ''}
                    </div>
                    <div class="option-label">${opt.option_text}</div>
                `;
                card.addEventListener('click', () => {
                    this.selectSingleOption(q.id, opt.id);
                });
                list.appendChild(card);
            });
            container.appendChild(list);

        } else if (q.question_type === 'multiple_choice') {
            const list = document.createElement('div');
            list.className = 'options-list';

            (q.options || []).forEach(opt => {
                const card = document.createElement('div');
                const isSelected = selectedSet.has(String(opt.id));
                card.className = `option-card ${isSelected ? 'selected' : ''}`;
                card.innerHTML = `
                    <div class="option-indicator" style="border-radius:var(--radius-sm);">
                        ${isSelected ? '<i class="fas fa-check" style="font-size:0.65rem;"></i>' : ''}
                    </div>
                    <div class="option-label">${opt.option_text}</div>
                `;
                card.addEventListener('click', () => {
                    this.toggleMultiOption(q.id, opt.id);
                });
                list.appendChild(card);
            });
            container.appendChild(list);

        } else if (q.question_type === 'fill_blank') {
            const inputWrapper = document.createElement('div');
            inputWrapper.className = 'form-group';
            inputWrapper.innerHTML = `
                <label class="form-label">Type your answer below (case-insensitive):</label>
                <input type="text" id="fill-blank-input" class="form-control" style="font-size:1.1rem; max-width:400px;" value="${escapeHtml(ans.text_answer || '')}" placeholder="Type your answer here..." />
            `;
            container.appendChild(inputWrapper);

            const inputEl = document.getElementById('fill-blank-input');
            inputEl.addEventListener('input', (e) => {
                this.updateTextAnswer(q.id, e.target.value);
            });

        } else if (q.question_type === 'descriptive') {
            const areaWrapper = document.createElement('div');
            areaWrapper.className = 'form-group';
            areaWrapper.innerHTML = `
                <label class="form-label">Provide your detailed response below:</label>
                <textarea id="descriptive-input" class="form-control" style="min-height:180px; font-size:1rem;" placeholder="Type your comprehensive explanation here...">${escapeHtml(ans.text_answer || '')}</textarea>
            `;
            container.appendChild(areaWrapper);

            const areaEl = document.getElementById('descriptive-input');
            areaEl.addEventListener('input', (e) => {
                this.updateTextAnswer(q.id, e.target.value);
            });
        }
    }

    selectSingleOption(questionId, optionId) {
        let ans = this.answersMap[questionId] || {};
        ans.selected_option_ids = String(optionId);
        ans.is_answered = 1;
        this.answersMap[questionId] = ans;

        this.renderQuestion(this.currentIndex);
        this.triggerSave();
    }

    toggleMultiOption(questionId, optionId) {
        let ans = this.answersMap[questionId] || {};
        let set = new Set((ans.selected_option_ids || '').split(',').filter(x => x.trim().length > 0));
        
        const optStr = String(optionId);
        if (set.has(optStr)) {
            set.delete(optStr);
        } else {
            set.add(optStr);
        }

        ans.selected_option_ids = Array.from(set).join(',');
        ans.is_answered = set.size > 0 ? 1 : 0;
        this.answersMap[questionId] = ans;

        this.renderQuestion(this.currentIndex);
        this.triggerSave();
    }

    updateTextAnswer(questionId, textVal) {
        let ans = this.answersMap[questionId] || {};
        ans.text_answer = textVal;
        ans.is_answered = textVal.trim().length > 0 ? 1 : 0;
        this.answersMap[questionId] = ans;

        this.updatePaletteButton(questionId);
        this.updatePaletteSummary();

        // Debounce auto-save
        clearTimeout(this.autoSaveTimer);
        this.autoSaveTimer = setTimeout(() => this.triggerSave(), 800);
    }

    clearCurrentAnswer() {
        const q = this.questions[this.currentIndex];
        let ans = this.answersMap[q.id] || {};
        ans.selected_option_ids = '';
        ans.text_answer = '';
        ans.is_answered = 0;
        this.answersMap[q.id] = ans;

        this.renderQuestion(this.currentIndex);
        this.triggerSave();
        showToast('Answer cleared for this question.', 'info');
    }

    toggleMarkForReview() {
        const q = this.questions[this.currentIndex];
        let ans = this.answersMap[q.id] || {};
        ans.is_marked_for_review = ans.is_marked_for_review ? 0 : 1;
        this.answersMap[q.id] = ans;

        this.updatePaletteButton(q.id);
        this.updatePaletteSummary();
        this.triggerSave();

        const btn = document.getElementById('btn-review');
        if (btn) {
            btn.className = ans.is_marked_for_review ? 'btn btn-warning' : 'btn btn-secondary';
        }
    }

    navigate(newIndex) {
        if (newIndex >= 0 && newIndex < this.questions.length) {
            this.renderQuestion(newIndex);
        }
    }

    /* ========================================================
       Question Palette Navigation & States
       ======================================================== */
    updatePaletteButton(questionId) {
        const btn = document.querySelector(`.palette-btn[data-qid="${questionId}"]`);
        if (!btn) return;

        const ans = this.answersMap[questionId];
        btn.className = 'palette-btn';

        if (this.questions[this.currentIndex].id === questionId) {
            btn.classList.add('current');
        }

        if (!ans || !ans.is_visited) {
            btn.classList.add('not-visited');
        } else if (ans.is_marked_for_review) {
            btn.classList.add('review');
        } else if (ans.is_answered) {
            btn.classList.add('answered');
        } else {
            btn.classList.add('unanswered');
        }
    }

    updatePaletteSummary() {
        let answered = 0;
        let unanswered = 0;
        let review = 0;
        let notVisited = 0;

        this.questions.forEach(q => {
            const ans = this.answersMap[q.id];
            if (!ans || !ans.is_visited) {
                notVisited++;
            } else if (ans.is_marked_for_review) {
                review++;
            } else if (ans.is_answered) {
                answered++;
            } else {
                unanswered++;
            }
        });

        const elAns = document.getElementById('summary-answered');
        const elUnans = document.getElementById('summary-unanswered');
        const elRev = document.getElementById('summary-review');
        const elNot = document.getElementById('summary-not-visited');

        if (elAns) elAns.textContent = answered;
        if (elUnans) elUnans.textContent = unanswered;
        if (elRev) elRev.textContent = review;
        if (elNot) elNot.textContent = notVisited;
    }

    updateProgressBar() {
        let answered = 0;
        this.questions.forEach(q => {
            if (this.answersMap[q.id] && this.answersMap[q.id].is_answered) answered++;
        });

        const pct = Math.round((answered / this.questions.length) * 100);
        const fill = document.getElementById('exam-progress-fill');
        if (fill) fill.style.width = `${pct}%`;
    }

    /* ========================================================
       Backend Real-time Auto-Save (AJAX)
       ======================================================== */
    async triggerSave() {
        if (this.isSubmitted) return;
        const q = this.questions[this.currentIndex];
        if (!q) return;

        const ans = this.answersMap[q.id] || {};
        const statusEl = document.getElementById('autosave-status');
        if (statusEl) {
            statusEl.className = 'autosave-status saving';
            statusEl.innerHTML = '<span class="dot"></span> Saving draft...';
        }

        try {
            const res = await fetch(`/api/exam/attempt/${this.attemptId}/save-answer`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question_id: q.id,
                    selected_option_ids: ans.selected_option_ids || '',
                    text_answer: ans.text_answer || '',
                    is_marked_for_review: ans.is_marked_for_review || false,
                    is_visited: true,
                    time_spent_seconds: 5
                })
            });
            const data = await res.json();
            if (data.success && statusEl) {
                statusEl.className = 'autosave-status';
                statusEl.innerHTML = '<span class="dot"></span> Cloud Synced';
            }
        } catch (e) {
            if (statusEl) {
                statusEl.className = 'autosave-status saving';
                statusEl.innerHTML = '<span class="dot"></span> Offline cache';
            }
        }
    }

    /* ========================================================
       Countdown Timer & Expiration Handler
       ======================================================== */
    startTimer() {
        const timerDigits = document.getElementById('timer-digits');
        const timerWrapper = document.getElementById('timer-wrapper');

        const interval = setInterval(() => {
            if (this.isSubmitted) {
                clearInterval(interval);
                return;
            }

            this.remainingSeconds--;

            if (this.remainingSeconds <= 300 && timerWrapper) {
                timerWrapper.classList.add('danger');
            }

            if (this.remainingSeconds <= 0) {
                clearInterval(interval);
                this.remainingSeconds = 0;
                this.autoSubmitExam();
            }

            if (timerDigits) {
                const mins = Math.floor(this.remainingSeconds / 60);
                const secs = this.remainingSeconds % 60;
                timerDigits.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
            }
        }, 1000);
    }

    /* ========================================================
       Proctoring & Anti-Cheat Security System
       ======================================================== */
    initProctoring() {
        // Tab switch / Window blur detection
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && !this.isSubmitted) {
                this.recordViolation('tab_switch', 'Candidate switched browser tab or minimized window.');
            }
        });

        window.addEventListener('blur', () => {
            if (!this.isSubmitted) {
                this.recordViolation('window_blur', 'Window lost focus.');
            }
        });

        // Block Right-Click Context Menu
        document.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.recordViolation('right_click', 'Candidate attempted right-click context menu.');
            showToast('Right-click is disabled during proctored examinations.', 'warning');
        });

        // Block Copy / Paste
        document.addEventListener('copy', (e) => {
            e.preventDefault();
            this.recordViolation('copy_paste', 'Candidate attempted clipboard copy.');
            showToast('Copying content is strictly prohibited.', 'danger');
        });

        document.addEventListener('paste', (e) => {
            // Allow pasting inside text areas if needed, or monitor
            this.recordViolation('copy_paste', 'Candidate attempted clipboard paste.');
        });
    }

    async recordViolation(eventType, details) {
        this.violationCount++;
        // Display warning modal
        const alertModal = document.getElementById('security-alert-modal');
        const warningCountEl = document.getElementById('security-warning-count');
        const warningDescEl = document.getElementById('security-warning-desc');

        if (warningCountEl) warningCountEl.textContent = `${this.violationCount} / ${this.maxViolations}`;
        if (warningDescEl) warningDescEl.textContent = details;
        if (alertModal) alertModal.classList.add('active');

        // Log to backend database
        try {
            await fetch(`/api/exam/attempt/${this.attemptId}/log-security`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    event_type: eventType,
                    details: details,
                    severity: this.violationCount >= this.maxViolations ? 'high' : 'medium'
                })
            });
        } catch (e) {
            console.error('Failed to log violation:', e);
        }
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.warn(`Fullscreen error: ${err.message}`);
            });
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
        }
    }

    /* ========================================================
       Exam Final Submission
       ======================================================== */
    promptSubmit() {
        let unansweredCount = 0;
        this.questions.forEach(q => {
            if (!this.answersMap[q.id] || !this.answersMap[q.id].is_answered) {
                unansweredCount++;
            }
        });

        const unansEl = document.getElementById('modal-unanswered-count');
        if (unansEl) unansEl.textContent = unansweredCount;

        openModal('submit-confirm-modal');
    }

    async executeSubmit(isAuto = false) {
        if (this.isSubmitted) return;
        this.isSubmitted = true;

        closeModal('submit-confirm-modal');
        showToast('Submitting and evaluating your examination...', 'info');

        try {
            const res = await fetch(`/api/exam/attempt/${this.attemptId}/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_auto_submit: isAuto })
            });
            const data = await res.json();
            if (data.success) {
                showToast('Evaluation complete! Redirecting to your scorecard...', 'success');
                setTimeout(() => {
                    window.location.href = data.redirect_url;
                }, 1000);
            } else {
                showToast(data.error || 'Submission error. Please retry.', 'danger');
                this.isSubmitted = false;
            }
        } catch (e) {
            showToast('Network error during submission. Retrying...', 'danger');
            this.isSubmitted = false;
        }
    }

    autoSubmitExam() {
        showToast('Time expired! Your examination is being auto-submitted...', 'warning');
        this.executeSubmit(true);
    }
}

// Global hook
window.ExaminationEngine = ExaminationEngine;

