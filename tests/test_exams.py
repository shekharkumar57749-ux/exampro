import unittest
from app import create_app
from database.connection import query_db
from models.exam_model import get_all_exams, get_exam_by_id, create_attempt, save_answer, get_attempt_answers_map

class TestExams(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_get_all_exams(self):
        """Test retrieving all active exams."""
        exams = get_all_exams()
        self.assertGreater(len(exams), 0)
        self.assertEqual(exams[0]['status'], 'active')

    def test_exam_retrieval_by_id(self):
        """Test retrieving single exam with details."""
        exam = get_exam_by_id(1)
        self.assertIsNotNone(exam)
        self.assertEqual(exam['id'], 1)
        self.assertIn('Python', exam['title'])

    def test_attempt_and_answer_saving(self):
        """Test creating attempt and updating student answers."""
        # Use student Priya Patel (id 2) to test attempt creation
        attempt_id = create_attempt(exam_id=2, student_id=2)
        self.assertIsNotNone(attempt_id)

        # Save an answer
        save_answer(
            attempt_id=attempt_id,
            question_id=9,
            selected_option_ids='23',
            is_marked_for_review=True,
            is_visited=True,
            time_spent_seconds=45
        )

        answers_map = get_attempt_answers_map(attempt_id)
        self.assertIn(9, answers_map)
        self.assertEqual(answers_map[9]['selected_option_ids'], '23')
        self.assertEqual(answers_map[9]['is_marked_for_review'], 1)

if __name__ == '__main__':
    unittest.main()

