"""
User session – holds the currently logged-in user's info.
Import and use `session` singleton throughout the app.
"""


class UserSession:
    """Stores current user state after login."""

    def __init__(self):
        self._user = None

    def login(self, user_dict):
        """Set the active user (dict from DB row)."""
        self._user = user_dict

    def logout(self):
        self._user = None

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
