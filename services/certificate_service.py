import os
import logging
from config import Config
from database.connection import query_db

logger = logging.getLogger('exampro.services.certificate')

def generate_pdf_certificate(result_id):
    """
    Creates an authentic, high-resolution PDF certificate using ReportLab.
    Saves to static/certificates/cert_<result_id>.pdf
    """
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfgen import canvas

    sql = """
        SELECT c.*, r.score, r.total_marks, r.percentage, r.grade,
               e.title as exam_title, e.exam_code, s.subject_name,
               stu.student_id as student_code, u.full_name as student_name, stu.college
        FROM certificates c
        JOIN results r ON c.result_id = r.id
        JOIN exams e ON c.exam_id = e.id
        JOIN subjects s ON e.subject_id = s.id
        JOIN students stu ON c.student_id = stu.id
        JOIN users u ON stu.user_id = u.id
        WHERE c.result_id = %s
    """
    cert_data = query_db(sql, (result_id,), one=True)
    if not cert_data:
        raise ValueError("Certificate record not found.")

    os.makedirs(Config.CERTIFICATES_FOLDER, exist_ok=True)
    pdf_filename = f"cert_{result_id}.pdf"
    pdf_path = os.path.join(Config.CERTIFICATES_FOLDER, pdf_filename)

    # Use landscape letter
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    class CertificateBackground(canvas.Canvas):
        """Custom canvas for drawing decorative certificate border and watermark."""
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.pages = []

        def showPage(self):
            self.pages.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            for page in self.pages:
                self.__dict__.update(page)
                self.draw_decorations()
                super().showPage()
            super().save()

        def draw_decorations(self):
            width, height = landscape(letter)
            # Outer border
            self.setStrokeColor(colors.HexColor('#1E3A8A')) # Dark Navy
            self.setLineWidth(5)
            self.rect(20, 20, width - 40, height - 40)
            
            # Inner thin border
            self.setStrokeColor(colors.HexColor('#3B82F6')) # Blue
            self.setLineWidth(1.5)
            self.rect(26, 26, width - 52, height - 52)

            # Golden corner accents
            self.setStrokeColor(colors.HexColor('#F59E0B')) # Amber
            self.setLineWidth(3)
            corner_len = 30
            # Top-left
            self.line(32, height - 32, 32 + corner_len, height - 32)
            self.line(32, height - 32, 32, height - 32 - corner_len)
            # Top-right
            self.line(width - 32, height - 32, width - 32 - corner_len, height - 32)
            self.line(width - 32, height - 32, width - 32, height - 32 - corner_len)
            # Bottom-left
            self.line(32, 32, 32 + corner_len, 32)
            self.line(32, 32, 32, 32 + corner_len)
            # Bottom-right
            self.line(width - 32, 32, width - 32 - corner_len, 32)
            self.line(width - 32, 32, width - 32, 32 + corner_len)

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1 # Center
    )

    subtitle_style = ParagraphStyle(
        'CertSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#4B5563'),
        alignment=1
    )

    recipient_style = ParagraphStyle(
        'CertRecipient',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=30,
        textColor=colors.HexColor('#111827'),
        alignment=1
    )

    body_style = ParagraphStyle(
        'CertBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=20,
        textColor=colors.HexColor('#374151'),
        alignment=1
    )

    badge_style = ParagraphStyle(
        'CertBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#047857'),
        alignment=1
    )

    story = [
        Spacer(1, 15),
        Paragraph("EXAMPRO ACADEMIC ASSESSMENT SYSTEM", subtitle_style),
        Spacer(1, 6),
        Paragraph("CERTIFICATE OF ACHIEVEMENT", title_style),
        Spacer(1, 10),
        Paragraph("This is to certify that", subtitle_style),
        Spacer(1, 10),
        Paragraph(f"<b>{cert_data['student_name']}</b>", recipient_style),
        Paragraph(f"Student ID: <b>{cert_data['student_code']}</b> &nbsp;|&nbsp; {cert_data['college']}", subtitle_style),
        Spacer(1, 14),
        Paragraph(
            f"has successfully completed and cleared the proctored examination for<br/>"
            f"<b>{cert_data['exam_title']}</b> ({cert_data['subject_name']})<br/>"
            f"with an aggregate score of <b>{cert_data['score']} / {cert_data['total_marks']}</b> "
            f"({cert_data['percentage']}%) and awarded Grade <b>{cert_data['grade']}</b>.",
            body_style
        ),
        Spacer(1, 20),
        Paragraph("★ VERIFIED AUTHENTIC CREDENTIAL ★", badge_style),
        Spacer(1, 20)
    ]

    # Footer table with signatures and verification code
    footer_data = [
        [
            Paragraph(f"<b>Certificate Code:</b><br/>{cert_data['certificate_code']}", subtitle_style),
            Paragraph(f"<b>Date of Issue:</b><br/>{cert_data['issue_date']}", subtitle_style),
            Paragraph("<b>Controller of Examinations</b><br/>ExamPro Academic Board", subtitle_style)
        ]
    ]
    t = Table(footer_data, colWidths=[240, 240, 240])
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t)

    doc.build(story, canvasmaker=CertificateBackground)
    logger.info(f"Certificate PDF generated at: {pdf_path}")
    return f"/static/certificates/{pdf_filename}"

def generate_result_report_pdf(result_id):
    """
    Generates a comprehensive PDF result card / scorecard for a student attempt.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from models.result_model import get_result_detailed_breakdown

    result, questions = get_result_detailed_breakdown(result_id)
    if not result:
        raise ValueError("Result record not found.")

    os.makedirs(Config.REPORTS_FOLDER, exist_ok=True)
    pdf_filename = f"report_{result_id}.pdf"
    pdf_path = os.path.join(Config.REPORTS_FOLDER, pdf_filename)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    header_style = ParagraphStyle('RepHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=colors.HexColor('#1E3A8A'))
    sub_style = ParagraphStyle('RepSub', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor('#4B5563'))
    th_style = ParagraphStyle('RepTh', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=12, textColor=colors.HexColor('#111827'))
    td_style = ParagraphStyle('RepTd', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12, textColor=colors.HexColor('#374151'))
    score_style = ParagraphStyle('RepScore', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor('#059669'))

    story = [
        Paragraph("EXAMPRO EXAMINATION SYSTEM", sub_style),
        Paragraph("Official Examination Scorecard & Analytics", header_style),
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1E3A8A'), spaceAfter=15)
    ]

    # Student & Exam Info Table
    info_data = [
        [Paragraph(f"<b>Candidate:</b> {result['student_name']}", td_style), Paragraph(f"<b>Exam:</b> {result['exam_title']}", td_style)],
        [Paragraph(f"<b>Student ID:</b> {result['student_code']}", td_style), Paragraph(f"<b>Subject:</b> {result['subject_name']}", td_style)],
        [Paragraph(f"<b>Date:</b> {result['published_at']}", td_style), Paragraph(f"<b>Status:</b> {result['status'].upper()} (Grade: {result['grade']})", td_style)]
    ]
    info_table = Table(info_data, colWidths=[260, 260])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F3F4F6')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB'))
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))

    # Metrics Summary Table
    metrics_data = [
        [
            Paragraph("Total Score", th_style),
            Paragraph("Percentage", th_style),
            Paragraph("Correct", th_style),
            Paragraph("Incorrect", th_style),
            Paragraph("Skipped", th_style),
            Paragraph("Accuracy", th_style)
        ],
        [
            Paragraph(f"{result['score']} / {result['total_marks']}", score_style),
            Paragraph(f"{result['percentage']}%", score_style),
            Paragraph(f"{result['correct_count']}", td_style),
            Paragraph(f"{result['incorrect_count']}", td_style),
            Paragraph(f"{result['skipped_count']}", td_style),
            Paragraph(f"{result['accuracy']}%", td_style)
        ]
    ]
    metrics_table = Table(metrics_data, colWidths=[90, 90, 85, 85, 85, 85])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E5E7EB')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#9CA3AF'))
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("<b>Question-wise Performance Breakdown:</b>", th_style))
    story.append(Spacer(1, 6))

    # Questions breakdown table
    q_data = [
        [
            Paragraph("#", th_style),
            Paragraph("Question", th_style),
            Paragraph("Type", th_style),
            Paragraph("Marks", th_style),
            Paragraph("Awarded", th_style),
            Paragraph("Status", th_style)
        ]
    ]

    for idx, q in enumerate(questions, 1):
        status_label = "Skipped" if not q['is_answered'] else ("Correct" if q['is_correct'] else "Incorrect")
        clean_text = (q['question_text'][:70] + '...') if len(q['question_text']) > 70 else q['question_text']
        q_data.append([
            Paragraph(str(idx), td_style),
            Paragraph(clean_text, td_style),
            Paragraph(q['question_type'], td_style),
            Paragraph(str(q['max_marks']), td_style),
            Paragraph(str(q['marks_awarded'] or 0.0), td_style),
            Paragraph(status_label, td_style)
        ])

    q_table = Table(q_data, colWidths=[25, 275, 75, 45, 55, 55])
    q_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('PADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9FAFB')])
    ]))
    story.append(q_table)

    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>This computer-generated score report is certified by ExamPro Academic Operations.</i>", sub_style))

    doc.build(story)
    return f"/static/reports/{pdf_filename}"

