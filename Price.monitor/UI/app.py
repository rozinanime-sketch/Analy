from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt


class LoginDialog(QDialog):
    """Диалог входа — первый запуск создаёт пароль, потом проверяет."""

    def __init__(self, auth, is_first: bool, theme: str):
        super().__init__()
        self.auth = auth
        self.is_first = is_first
        self.setWindowTitle("Price Monitor — Вход")
        self.setFixedSize(340, 230)
        self.setStyleSheet(theme)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(28, 28, 28, 28)

        title = QLabel("📈 Price Monitor")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        hint = QLabel(
            "Придумайте пароль (>8 символов + цифра)"
            if self.is_first else "Введите пароль"
        )
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.pwd = QLineEdit()
        self.pwd.setPlaceholderText("Пароль")
        self.pwd.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.pwd)

        if self.is_first:
            self.pwd2 = QLineEdit()
            self.pwd2.setPlaceholderText("Повторите пароль")
            self.pwd2.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(self.pwd2)

        btn = QPushButton("Создать" if self.is_first else "Войти")
        btn.clicked.connect(self._submit)
        self.pwd.returnPressed.connect(self._submit)
        layout.addWidget(btn)

    def _submit(self):
        pwd = self.pwd.text()
        if self.is_first:
            if pwd != self.pwd2.text():
                QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
                return
            if not self.auth.set_password(pwd):
                QMessageBox.warning(
                    self, "Слабый пароль",
                    "Нужно больше 8 символов и хотя бы одна цифра"
                )
                return
        else:
            if not self.auth.verify(pwd):
                QMessageBox.warning(self, "Ошибка", "Неверный пароль")
                return
        self.accept()


class AddStockDialog(QDialog):
    """Диалог добавления новой акции по тикеру."""

    def __init__(self, theme: str):
        super().__init__()
        self.setWindowTitle("Добавить акцию")
        self.setFixedSize(320, 140)
        self.setStyleSheet(theme)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 24, 24, 24)

        layout.addWidget(QLabel("Тикер (например: AAPL, TSLA, SBER.ME)"))

        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("AAPL")
        layout.addWidget(self.ticker_input)

        btn = QPushButton("Добавить")
        btn.clicked.connect(self._submit)
        self.ticker_input.returnPressed.connect(self._submit)
        layout.addWidget(btn)

    def _submit(self):
        if not self.ticker_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите тикер")
            return
        self.accept()

    def get_ticker(self) -> str:
        return self.ticker_input.text().strip().upper()