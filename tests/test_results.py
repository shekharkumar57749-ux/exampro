import os
import unittest
from app import create_app
from models.exam_model import create_attempt, save_answer
from services.evaluation_service import evaluate_exam_submission, calculate_grade
from services.certificate_service import generate_pdf_certificate, generate_result_report_pdf
from models.result_model import get_result_by_id, get_certificate_by_code
from config import Config

class TestResults(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_grade_calculation(self):
        """Test grade boundary calculations."""
        self.assertEqual(calculate_grade(95), 'A+')
        self.assertEqual(calculate_grade(85), 'A')
        self.assertEqual(calculate_grade(75), 'B')
        self.assertEqual(calculate_grade(65), 'C')
        self.assertEqual(calculate_grade(55), 'D')
        self.assertEqual(calculate_grade(45), 'E')
        self.assertEqual(calculate_grade(30), 'F')

    def test_evaluation_and_certificate_issuance(self):
        """Test complete submission evaluation and automatic certificate generation."""
        # Create attempt for student Rahul (id 3) on DBMS Exam (id 2)
        attempt_id = create_attempt(exam_id=2, student_id=3)
        
        # Save correct answers for questions 9, 10, 11 (2.5 marks each = 7.5 / 10 = 75%)
        # Q9: Atomicity (opt 23)
        save_answer(attempt_id, question_id=9, selected_option_ids='23')
        # Q10: True (opt 27)
        save_answer(attempt_id, question_id=10, selected_option_ids='27')
        # Q11: PRIMARY KEY (opt 29)
        save_answer(attempt_id, question_id=11, selected_option_ids='29')

        result_id = evaluate_exam_submission(attempt_id)
        self.assertIsNotNone(result_id)

        result = get_result_by_id(result_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'pass')
        self.assertGreaterEqual(result['score'], 7.5)

        # Verify ReportLab PDF Generation
        pdf_path = generate_result_report_pdf(result_id)
        self.assertTrue(os.path.exists(os.path.join(Config.BASE_DIR, pdf_path.lstrip('/'))))

        cert_pdf_path = generate_pdf_certificate(result_id)
        self.assertTrue(os.path.exists(os.path.join(Config.BASE_DIR, cert_pdf_path.lstrip('/'))))

if __name__ == '__main__':
    unittest.main()

