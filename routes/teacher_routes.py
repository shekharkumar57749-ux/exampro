import logging
import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from routes import role_required
from models.exam_model import get_all_exams, get_exam_by_id, get_courses, get_subjects
from models.question_model import (
    get_all_questions,
    get_question_by_id,
    create_question,
    update_question,
    delete_question,
    attach_questions_to_exam
)
from models.result_model import get_all_results
from database.connection import query_db

logger = logging.getLogger('exampro.routes.teacher')
teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

@teacher_bp.before_request
@role_required(['teacher', 'admin'])
def teacher_auth():
    pass

@teacher_bp.route('/dashboard')
def dashboard():
    """Educator command center."""
    teacher_id = session.get('user_id')

    # Real DB statistics for this teacher
    stats = query_db("""
        SELECT
            (SELECT COUNT(*) FROM exams WHERE created_by = %s) as my_exams,
            (SELECT COUNT(*) FROM questions WHERE created_by = %s) as my_questions,
            (SELECT COUNT(ea.id) FROM exam_attempts ea JOIN exams e ON ea.exam_id = e.id WHERE e.created_by = %s AND ea.status IN ('submitted', 'auto_submitted')) as submissions_count,
            (SELECT COALESCE(ROUND(AVG(r.percentage), 1), 0.0) FROM results r JOIN exams e ON r.exam_id = e.id WHERE e.created_by = %s) as avg_class_score
    """, (teacher_id, teacher_id, teacher_id, teacher_id), one=True)

    my_exams = get_all_exams(created_by=teacher_id)
    recent_submissions = query_db("""
        SELECT r.*, e.title as exam_title, u.full_name as student_name, stu.student_id as student_code
        FROM results r
        JOIN exams e ON r.exam_id = e.id
        JOIN students stu ON r.student_id = stu.id
        JOIN users u ON stu.user_id = u.id
        WHERE e.created_by = %s
        ORDER BY r.id DESC
        LIMIT 6
    """, (teacher_id,))

    return render_template(
        'teacher/dashboard.html',
        stats=stats,
        exams=my_exams,
        recent_submissions=recent_submissions
    )

@teacher_bp.route('/exams')
def exams():
    """Manage exams created by teacher."""
    teacher_id = session.get('user_id')
    status_filter = request.args.get('status')
    search = request.args.get('search')
    exams_list = get_all_exams(status=status_filter, created_by=teacher_id, search=search)
    return render_template('teacher/exams.html', exams=exams_list)

@teacher_bp.route('/exams/create', methods=['GET', 'POST'])
def exam_create():
    """Multi-step exam creation view."""
    subjects = get_subjects()
    questions = get_all_questions(limit=300)
    return render_template('teacher/exam_create.html', subjects=subjects, questions=questions)

@teacher_bp.route('/questions')
def questions():
    """Manage question bank."""
    subject_id = request.args.get('subject_id')
    difficulty = request.args.get('difficulty')
    qtype = request.args.get('qtype')
    search = request.args.get('search')

    all_q = get_all_questions(subject_id=subject_id, difficulty=difficulty, qtype=qtype, search=search)
    subjects = get_subjects()

    return render_template(
        'teacher/questions.html',
        questions=all_q,
        subjects=subjects,
        selected_subject=subject_id,
        selected_difficulty=difficulty,
        selected_type=qtype,
        search_query=search
    )

@teacher_bp.route('/questions/add', methods=['POST'])
def question_add():
    """Add a new question with options."""
    data = request.form
    subject_id = int(data.get('subject_id'))
    topic = data.get('topic', 'General').strip()
    qtype = data.get('question_type', 'single_choice')
    difficulty = data.get('difficulty', 'medium')
    marks = float(data.get('marks', 1.0))
    negative_marks = float(data.get('negative_marks', 0.0))
    explanation = data.get('explanation', '').strip()
    question_text = data.get('question_text', '').strip()

    # Parse options
    options = []
    if qtype in ('single_choice', 'true_false'):
        opt_texts = request.form.getlist('option_text[]')
        correct_idx = int(data.get('correct_option', 0))
        for idx, text in enumerate(opt_texts):
            if text.strip():
                options.append({
                    'text': text.strip(),
                    'is_correct': (idx == correct_idx),
                    'order': idx + 1
                })
    elif qtype == 'multiple_choice':
        opt_texts = request.form.getlist('option_text[]')
        correct_indices = [int(x) for x in request.form.getlist('correct_options[]')]
        for idx, text in enumerate(opt_texts):
            if text.strip():
                options.append({
                    'text': text.strip(),
                    'is_correct': (idx in correct_indices),
                    'order': idx + 1
                })
    elif qtype == 'fill_blank':
        ans_text = data.get('fill_blank_answer', '').strip()
        if ans_text:
            options.append({'text': ans_text, 'is_correct': True, 'order': 1})
    elif qtype == 'descriptive':
        sample_ans = data.get('descriptive_sample', '').strip()
        options.append({'text': sample_ans or 'Descriptive answer guide.', 'is_correct': True, 'order': 1})

    q_data = {
        'subject_id': subject_id,
        'topic': topic,
        'question_text': question_text,
        'question_type': qtype,
        'difficulty': difficulty,
        'marks': marks,
        'negative_marks': negative_marks,
        'explanation': explanation,
        'created_by': session['user_id']
    }

    try:
        create_question(q_data, options)
        flash('Question added to Question Bank successfully!', 'success')
    except Exception as e:
        flash(f"Error adding question: {e}", 'danger')

    return redirect(url_for('teacher.questions'))

@teacher_bp.route('/questions/<int:question_id>/delete', methods=['POST'])
def question_delete(question_id):
    """Delete question from question bank."""
    try:
        delete_question(question_id)
        flash('Question deleted successfully.', 'success')
    except Exception as e:
        flash(f"Error deleting question: {e}", 'danger')
    return redirect(url_for('teacher.questions'))

@teacher_bp.route('/questions/import-csv', methods=['POST'])
def questions_import_csv():
    """Bulk import questions via CSV file."""
    if 'csv_file' not in request.files:
        flash('No file uploaded.', 'danger')
        return redirect(url_for('teacher.questions'))

    file = request.files['csv_file']
    if file.filename == '':
        flash('Please select a CSV file.', 'danger')
        return redirect(url_for('teacher.questions'))

    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)
        imported_count = 0

        # Required columns: subject_id, topic, question_text, question_type, difficulty, marks, option1, option2, option3, option4, correct_option_index
        for row in reader:
            if not row.get('question_text'):
                continue

            q_data = {
                'subject_id': int(row.get('subject_id', 1)),
                'topic': row.get('topic', 'General'),
                'question_text': row.get('question_text'),
                'question_type': row.get('question_type', 'single_choice'),
                'difficulty': row.get('difficulty', 'medium'),
                'marks': float(row.get('marks', 1.0)),
                'negative_marks': float(row.get('negative_marks', 0.0)),
                'explanation': row.get('explanation', ''),
                'created_by': session['user_id']
            }

            options = []
            corr_idx = int(row.get('correct_option_index', 1))
            for i in range(1, 5):
                opt_key = f"option{i}"
                if row.get(opt_key):
                    options.append({
                        'text': row[opt_key].strip(),
                        'is_correct': (i == corr_idx),
                        'order': i
                    })

            create_question(q_data, options)
            imported_count += 1

        flash(f"Successfully imported {imported_count} questions from CSV!", 'success')
    except Exception as e:
        logger.error(f"CSV import error: {e}")
        flash(f"Failed to import CSV: {str(e)}", 'danger')

    return redirect(url_for('teacher.questions'))

@teacher_bp.route('/results')
def results():
    """View student submissions and performance."""
    results_list = get_all_results()
    return render_template('teacher/results.html', results=results_list)

