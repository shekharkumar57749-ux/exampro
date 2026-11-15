import os
import unittest
from app import create_app
from database.initialize_db import initialize_database
from database.connection import query_db

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_student_login_success(self):
        """Test valid student authentication."""
        response = self.client.post('/login', data={
            'identifier': 'student@exampro.com',
            'password': 'Student@123'
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/student/dashboard', response.headers.get('Location', ''))

    def test_student_login_invalid_password(self):
        """Test login with wrong password."""
        response = self.client.post('/login', data={
            'identifier': 'student@exampro.com',
            'password': 'WrongPassword999'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid login credentials', response.data)

    def test_admin_login(self):
        """Test admin login portal."""
        response = self.client.post('/auth/admin-login', data={
            'identifier': 'admin@exampro.com',
            'password': 'Admin@123'
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/dashboard', response.headers.get('Location', ''))

    def test_teacher_login(self):
        """Test teacher login portal."""
        response = self.client.post('/auth/teacher-login', data={
            'identifier': 'teacher@exampro.com',
            'password': 'Teacher@123'
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/teacher/dashboard', response.headers.get('Location', ''))

    def test_unauthorized_access(self):
        """Test protected routes redirect to login when unauthenticated."""
        response = self.client.get('/student/dashboard', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/student-login', response.headers.get('Location', ''))

if __name__ == '__main__':
    unittest.main()

