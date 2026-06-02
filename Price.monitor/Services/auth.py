import hashlib


class AuthService:
    def __init__(self, storage):
        self.storage = storage

    def _hash(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def is_strong_password(self, password: str) -> bool:
        if len(password) <= 8:
            return False
        if not any(c.isdigit() for c in password):
            return False
        return True

    def is_first_run(self) -> bool:
        return self.storage.get_user() is None

    def set_password(self, password: str) -> bool:
        if not self.is_strong_password(password):
            return False
        self.storage.set_user_password(self._hash(password))
        return True

    def verify(self, password: str) -> bool:
        user = self.storage.get_user()
        if not user:
            return False
        return user['password_hash'] == self._hash(password)
