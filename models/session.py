"""
User session – holds the currently logged-in user's info.
Import and use `session` singleton throughout the app.
Persists session to a local file so login is skipped on restart.
"""

import json
import os

SESSION_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".session")


class UserSession:
    """Stores current user state after login."""

    def __init__(self):
        self._user = None

    def login(self, user_dict):
        """Set the active user (dict from DB row) and persist."""
        self._user = user_dict
        self._save()

    def logout(self):
        self._user = None
        self._clear()

    def restore(self, db):
        """Try to restore session from file. Returns True if successful."""
        if not os.path.exists(SESSION_FILE):
            return False
        try:
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
            user_id = data.get("user_id")
            if not user_id:
                return False
            user = db.fetch_one(
                "SELECT * FROM users WHERE id = %s AND is_active = TRUE", (user_id,)
            )
            if user:
                self._user = user
                return True
            self._clear()
            return False
        except Exception:
            self._clear()
            return False

    def _save(self):
        """Persist user_id to file."""
        if self._user:
            try:
                with open(SESSION_FILE, "w") as f:
                    json.dump({"user_id": self._user["id"]}, f)
            except Exception:
                pass

    def _clear(self):
        """Remove session file."""
        try:
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)
        except Exception:
            pass

    @property
    def is_logged_in(self):
        return self._user is not None

    @property
    def user(self):
        return self._user

    @property
    def user_id(self):
        return self._user["id"] if self._user else None

    @property
    def username(self):
        return self._user["username"] if self._user else None

    @property
    def full_name(self):
        return self._user["full_name"] if self._user else None

    @property
    def role(self):
        return self._user["role"] if self._user else None

    @property
    def is_admin(self):
        return self.role == "Admin"


# Singleton instance
session = UserSession()
