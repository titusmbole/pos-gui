import hashlib

from database.connection import Database


class UserModel:
    """Data operations for users."""

    def __init__(self, db: Database):
        self.db = db

    def authenticate(self, username, password):
        """Verify credentials. Returns user dict or None."""
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        user = self.db.fetch_one(
            "SELECT * FROM users WHERE username = %s AND password_hash = %s AND is_active = TRUE",
            (username, pw_hash),
        )
        return user

    def get_all(self):
        return self.db.fetch_all(
            "SELECT id, username, email, full_name, role, is_active, created_at "
            "FROM users ORDER BY created_at"
        )

    def add(self, username, email, password, full_name, role="Cashier"):
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        return self.db.execute_query(
            "INSERT INTO users (username, email, password_hash, full_name, role) "
            "VALUES (%s, %s, %s, %s, %s)",
            (username, email, pw_hash, full_name, role),
        )

    def update(self, user_id, username, email, full_name, role):
        self.db.execute_query(
            "UPDATE users SET username=%s, email=%s, full_name=%s, role=%s WHERE id=%s",
            (username, email, full_name, role, user_id),
        )

    def change_password(self, user_id, new_password):
        pw_hash = hashlib.sha256(new_password.encode()).hexdigest()
        self.db.execute_query(
            "UPDATE users SET password_hash=%s WHERE id=%s", (pw_hash, user_id)
        )

    def deactivate(self, user_id):
        self.db.execute_query(
            "UPDATE users SET is_active=FALSE WHERE id=%s", (user_id,)
        )
