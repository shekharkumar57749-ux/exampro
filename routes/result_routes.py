import os
import logging
from flask import Blueprint, send_file, flash, redirect, url_for, render_template, abort
from models.result_model import get_result_by_id, get_certificate_by_code
from services.certificate_service import generate_pdf_certificate, generate_result_report_pdf
from config import Config

logger = logging.getLogger('exampro.routes.result')
result_bp = Blueprint('result', __name__)

@result_bp.route('/results/<int:result_id>/download-pdf')
def download_result_pdf(result_id):
    """Download official examination scorecard as PDF."""
    result = get_result_by_id(result_id)
    if not result:
        flash('Result not found.', 'danger')
        return redirect(url_for('student.results'))

    try:
        pdf_rel_path = generate_result_report_pdf(result_id)
        filename = f"report_{result_id}.pdf"
        abs_path = os.path.join(Config.REPORTS_FOLDER, filename)
        return send_file(abs_path, as_attachment=True, download_name=f"ExamPro_Scorecard_{result['exam_code']}_{result['student_code']}.pdf")
    except Exception as e:
        logger.error(f"Error generating result scorecard PDF: {e}")
        flash('Failed to generate result scorecard PDF.', 'danger')
        return redirect(url_for('student.result_detail', result_id=result_id))

@result_bp.route('/certificates/<int:result_id>/download')
def download_certificate(result_id):
    """Download verified certificate of excellence as PDF."""
    result = get_result_by_id(result_id)
    if not result:
        flash('Result not found.', 'danger')
        return redirect(url_for('student.certificates'))

    if result['status'] != 'pass':
        flash('Certificates are only issued for passed examinations.', 'warning')
        return redirect(url_for('student.results'))

    try:
        pdf_rel_path = generate_pdf_certificate(result_id)
        filename = f"cert_{result_id}.pdf"
        abs_path = os.path.join(Config.CERTIFICATES_FOLDER, filename)
        return send_file(abs_path, as_attachment=True, download_name=f"ExamPro_Certificate_{result['exam_code']}.pdf")
    except Exception as e:
        logger.error(f"Error downloading certificate PDF: {e}")
        flash('Failed to download certificate PDF.', 'danger')
        return redirect(url_for('student.certificates'))

@result_bp.route('/verify-certificate/<certificate_code>')
def verify_certificate(certificate_code):
    """
    Public portal to verify credential authenticity.
    Accessible without logging in.
    """
    cert = get_certificate_by_code(certificate_code)
    return render_template('verify_certificate.html', cert=cert, code=certificate_code)

