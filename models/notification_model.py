import logging
from database.connection import query_db, execute_commit

logger = logging.getLogger('exampro.models.notification')

def get_user_notifications(user_id, unread_only=False, limit=15):
    """Retrieve notifications for a user."""
    sql = "SELECT * FROM notifications WHERE user_id = %s"
    params = [user_id]
    if unread_only:
        sql += " AND is_read = 0"
    sql += " ORDER BY id DESC LIMIT %s"
    params.append(limit)
    return query_db(sql, tuple(params))

def get_unread_count(user_id):
    """Get count of unread notifications."""
    res = query_db("SELECT COUNT(*) as cnt FROM notifications WHERE user_id = %s AND is_read = 0", (user_id,), one=True)
    return res['cnt'] if res else 0

def mark_as_read(notification_id, user_id):
    """Mark a single notification as read."""
    return execute_commit("UPDATE notifications SET is_read = 1 WHERE id = %s AND user_id = %s", (notification_id, user_id))

def mark_all_as_read(user_id):
    """Mark all notifications for a user as read."""
    return execute_commit("UPDATE notifications SET is_read = 1 WHERE user_id = %s", (user_id,))

def create_notification(user_id, title, message, notif_type='info', link=None):
    """Send an in-app notification to a user."""
    return execute_commit("""
        INSERT INTO notifications (user_id, title, message, type, is_read, link)
        VALUES (%s, %s, %s, %s, 0, %s)
    """, (user_id, title, message, notif_type, link))

def log_security_event(attempt_id, student_id, exam_id, event_type, details, severity='medium'):
    """Record an examination security violation event."""
    return execute_commit("""
        INSERT INTO security_logs (attempt_id, student_id, exam_id, event_type, details, severity)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (attempt_id, student_id, exam_id, event_type, details, severity))

def get_security_logs(exam_id=None, student_id=None, limit=100):
    """Retrieve security violation logs for admin dashboard."""
    sql = """
        SELECT sl.*, e.title as exam_title, u.full_name as student_name, stu.student_id as student_code
        FROM security_logs sl
        JOIN exams e ON sl.exam_id = e.id
        JOIN students stu ON sl.student_id = stu.id
        JOIN users u ON stu.user_id = u.id
        WHERE 1=1
    """
    params = []
    if exam_id and exam_id != 'all':
        sql += " AND sl.exam_id = %s"
        params.append(exam_id)
    if student_id and student_id != 'all':
        sql += " AND sl.student_id = %s"
        params.append(student_id)

    sql += " ORDER BY sl.id DESC LIMIT %s"
    params.append(limit)
    return query_db(sql, tuple(params))

