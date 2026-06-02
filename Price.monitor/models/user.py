import hashlib


class User:
    def __init__(self, id: int, password_hash: str):
        self.id = id
        self.password_hash = password_hash

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def is_strong_password(password: str) -> bool:
        if len(password) <= 8:
            return False
        if not any(c.isdigit() for c in password):
            return False
        return True

    def verify_password(self, password: str) -> bool:
        return self.password_hash == User.hash_password(password)

    def __repr__(self):
        return f"User(id={self.id})"
