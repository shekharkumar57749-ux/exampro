import os
import sqlite3
import logging
from config import Config

logger = logging.getLogger('exampro.db')
logging.basicConfig(level=logging.INFO)

# Global flag to track which DB engine is actively being used
DB_ENGINE = None  # 'mysql' or 'sqlite'

def try_mysql_connection():
    """Attempt connecting to MySQL using mysql.connector or pymysql."""
    # Try mysql.connector first
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            autocommit=False,
            connect_timeout=3
        )
        return conn, 'mysql.connector'
    except Exception as e1:
        # Try PyMySQL as alternate
        try:
            import pymysql
            import pymysql.cursors
            conn = pymysql.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
                connect_timeout=3
            )
            return conn, 'pymysql'
        except Exception as e2:
            return None, f"mysql.connector failed: {e1} | pymysql failed: {e2}"

def get_connection():
    """
    Returns an active database connection.
    Attempts MySQL first; falls back smoothly to SQLite if MySQL is unreachable.
    """
    global DB_ENGINE
    
    # 1. Try MySQL
    conn, info = try_mysql_connection()
    if conn is not None:
        DB_ENGINE = 'mysql'
        return conn
    
    # 2. Smooth Fallback to SQLite
    DB_ENGINE = 'sqlite'
    os.makedirs(os.path.dirname(Config.SQLITE_DB_PATH), exist_ok=True)
    sqlite_conn = sqlite3.connect(Config.SQLITE_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_conn.execute("PRAGMA foreign_keys = ON")
    return sqlite_conn

class DictRow(dict):
    """Allows both dict key and attribute style access."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

def query_db(query, args=(), one=False, commit=False):
    """
    Universal database query runner that works identically across MySQL and SQLite.
    Returns list of dicts (or single dict if one=True), or lastrowid on INSERT with commit=True.
    """
    global DB_ENGINE
    conn = get_connection()
    is_sqlite = (DB_ENGINE == 'sqlite')
    
    # Translate query syntax if running on SQLite
    executed_query = query
    if is_sqlite:
        executed_query = query.replace('%s', '?')
        # Replace MySQL specific date/enum/functions if needed
        executed_query = executed_query.replace('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', 'CURRENT_TIMESTAMP')
    
    try:
        cursor = None
        if is_sqlite:
            cursor = conn.cursor()
            cursor.execute(executed_query, args)
            if commit:
                conn.commit()
                last_id = cursor.lastrowid
                cursor.close()
                conn.close()
                return last_id
            
            rows = cursor.fetchall()
            result = [DictRow(dict(r)) for r in rows]
            cursor.close()
            conn.close()
            return (result[0] if result else None) if one else result
        else:
            # MySQL branch
            # Check if cursor supports dictionary mode
            try:
                cursor = conn.cursor(dictionary=True)
            except TypeError:
                cursor = conn.cursor()
                
            cursor.execute(executed_query, args)
            
            if commit:
                conn.commit()
                last_id = cursor.lastrowid
                cursor.close()
                conn.close()
                return last_id
                
            rows = cursor.fetchall()
            # If not dictionary cursor, build dict from description
            if rows and not isinstance(rows[0], dict):
                columns = [col[0] for col in cursor.description]
                result = [DictRow(dict(zip(columns, r))) for r in rows]
            else:
                result = [DictRow(r) for r in rows]
                
            cursor.close()
            conn.close()
            return (result[0] if result else None) if one else result
            
    except Exception as e:
        logger.error(f"Database Query Error: {e} | Query: {executed_query} | Args: {args}")
        if commit and conn:
            try:
                conn.rollback()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        raise e

def execute_commit(query, args=()):
    """Helper to execute an INSERT/UPDATE/DELETE query with commit."""
    return query_db(query, args, commit=True)

