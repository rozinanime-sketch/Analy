import sys
import os

# Добавляем корень проекта в путь чтобы импорты работали
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QHeaderView,
    QInputDialog, QMessageBox, QDialog, QLabel, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from Services.Storage import Storage
from Services.analytics import Analytics
from Services.Stock import StockParser
from Services.auth import AuthService
from UI.app import LoginDialog, AddStockDialog

# ─── Темы ────────────────────────────────────────────────────────────────────

DARK = """
QMainWindow, QWidget  { background: #1e1e2e; color: #cdd6f4; }
QTableWidget          { background: #313244; border: 1px solid #45475a;
                        gridline-color: #45475a; color: #cdd6f4; border-radius: 8px; }
QTableWidget::item:selected { background: #45475a; }
QHeaderView::section  { background: #1e1e2e; color: #89b4fa;
                        border: none; padding: 8px; font-weight: bold; }
QPushButton           { background: #89b4fa; color: #1e1e2e; border: none;
                        border-radius: 6px; padding: 8px 16px; font-weight: bold; }
QPushButton:hover     { background: #74c7ec; }
QPushButton#danger    { background: #f38ba8; }
QPushButton#secondary { background: #45475a; color: #cdd6f4; }
QPushButton#secondary:hover { background: #585b70; }
QLineEdit             { background: #313244; border: 1px solid #45475a;
                        border-radius: 6px; padding: 6px; color: #cdd6f4; }
QLabel#title          { font-size: 20px; font-weight: bold; color: #89b4fa; }
QLabel#status         { color: #6c7086; font-size: 12px; }
"""

LIGHT = """
QMainWindow, QWidget  { background: #eff1f5; color: #4c4f69; }
QTableWidget          { background: #ffffff; border: 1px solid #bcc0cc;
                        gridline-color: #dce0e8; color: #4c4f69; border-radius: 8px; }
QTableWidget::item:selected { background: #dce0e8; }
QHeaderView::section  { background: #eff1f5; color: #1e66f5;
                        border: none; padding: 8px; font-weight: bold; }
QPushButton           { background: #1e66f5; color: #fff; border: none;
                        border-radius: 6px; padding: 8px 16px; font-weight: bold; }
QPushButton:hover     { background: #04a5e5; }
QPushButton#danger    { background: #d20f39; color: #fff; }
QPushButton#secondary { background: #dce0e8; color: #4c4f69; }
QPushButton#secondary:hover { background: #bcc0cc; }
QLineEdit             { background: #fff; border: 1px solid #bcc0cc;
                        border-radius: 6px; padding: 6px; color: #4c4f69; }
QLabel#title          { font-size: 20px; font-weight: bold; color: #1e66f5; }
QLabel#status         { color: #9ca0b0; font-size: 12px; }
"""


# ─── Фоновый поток для парсинга ───────────────────────────────────────────────

class FetchThread(QThread):
    price_ready = pyqtSignal(str, float)  # ticker, price
    fetch_error = pyqtSignal(str)         # ticker

    def __init__(self, tickers: list[str], parser: StockParser):
        super().__init__()
        self.tickers = tickers
        self.parser = parser

    def run(self):
        for ticker in self.tickers:
            try:
                price = self.parser.get_price(ticker)
                if price:
                    self.price_ready.emit(ticker, price)
                else:
                    self.fetch_error.emit(ticker)
            except Exception:
                self.fetch_error.emit(ticker)


# ─── Главное окно ─────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, storage: Storage,
                 auth: AuthService, analytics: Analytics, parser: StockParser):
        super().__init__()
        self.storage = storage
        self.auth = auth
        self.analytics = analytics
        self.parser = parser
        self.dark_mode = True

        self.setWindowTitle("📈 Price Monitor v1.0")
        self.setMinimumSize(950, 580)
        self._build()
        self._apply_theme()
        self.refresh_table()

        # Автообновление каждые 60 секунд
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_all_prices)
        self.timer.start(60_000)

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        # Шапка
        header = QHBoxLayout()
        title = QLabel("📈 Price Monitor")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()

        self.theme_btn = QPushButton("☀️ Светлая")
        self.theme_btn.setObjectName("secondary")
        self.theme_btn.clicked.connect(self._toggle_theme)
        header.addWidget(self.theme_btn)
        root.addLayout(header)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Тикер", "Название", "Тек. цена", "Среднее", "Мин", "Макс"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(
            lambda: self.del_btn.setEnabled(bool(self.table.selectedItems()))
        )
        root.addWidget(self.table)

        # Кнопки
        btns = QHBoxLayout()

        self.update_btn = QPushButton("🔄 Обновить все цены")
        self.update_btn.clicked.connect(self.update_all_prices)
        btns.addWidget(self.update_btn)

        add_btn = QPushButton("+ Добавить акцию")
        add_btn.clicked.connect(self.add_new_stock)
        btns.addWidget(add_btn)

        self.del_btn = QPushButton("🗑 Удалить")
        self.del_btn.setObjectName("danger")
        self.del_btn.setEnabled(False)
        self.del_btn.clicked.connect(self.delete_stock)
        btns.addWidget(self.del_btn)

        btns.addStretch()

        self.status = QLabel("Готово")
        self.status.setObjectName("status")
        btns.addWidget(self.status)

        root.addLayout(btns)

    def _apply_theme(self):
        self.setStyleSheet(DARK if self.dark_mode else LIGHT)
        self.theme_btn.setText("☀️ Светлая" if self.dark_mode else "🌙 Тёмная")

    def _toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self._apply_theme()

    def refresh_table(self):
        stocks = self.storage.get_all_stocks()
        self.table.setRowCount(len(stocks))

        for i, stock in enumerate(stocks):
            records = self.storage.get_prices(stock.id)
            prices = [r.price for r in records]
            stats = self.analytics.calculate(prices)

            self.table.setItem(i, 0, QTableWidgetItem(stock.ticker))
            self.table.setItem(i, 1, QTableWidgetItem(stock.name))
            self.table.setItem(i, 2, QTableWidgetItem(
                f"${prices[-1]}" if prices else "—"
            ))

            if stats:
                self.table.setItem(i, 3, QTableWidgetItem(f"${stats['avg']}"))
                self.table.setItem(i, 4, QTableWidgetItem(f"${stats['min']}"))
                self.table.setItem(i, 5, QTableWidgetItem(f"${stats['max']}"))
            else:
                for col in range(3, 6):
                    self.table.setItem(i, col, QTableWidgetItem("—"))

    def add_new_stock(self):
        ticker, ok = QInputDialog.getText(
            self, "Добавить акцию", "Введите тикер (например AAPL, SBER.ME):"
        )
        if not ok or not ticker.strip():
            return

        ticker = ticker.strip().upper()
        self.status.setText(f"⏳ Проверяем {ticker}...")

        name = self.parser.get_name(ticker)
        self.storage.add_stock(ticker, name, 0.0)
        self.refresh_table()
        self.status.setText(f"✅ {ticker} добавлен")

    def delete_stock(self):
        row = self.table.currentRow()
        if row < 0:
            return
        ticker = self.table.item(row, 0).text()
        reply = QMessageBox.question(self, "Удалить", f"Удалить {ticker}?")
        if reply == QMessageBox.StandardButton.Yes:
            stocks = self.storage.get_all_stocks()
            self.storage.delete_stock(stocks[row].id)
            self.refresh_table()

    def update_all_prices(self):
        stocks = self.storage.get_all_stocks()
        if not stocks:
            return

        self.status.setText("⏳ Загружаем цены...")
        self.update_btn.setEnabled(False)

        tickers = [s.ticker for s in stocks]
        self.thread = FetchThread(tickers, self.parser)
        self.thread.price_ready.connect(self._on_price)
        self.thread.fetch_error.connect(self._on_error)
        self.thread.finished.connect(self._on_done)
        self.thread.start()

    def _on_price(self, ticker: str, price: float):
        stocks = self.storage.get_all_stocks()
        for stock in stocks:
            if stock.ticker == ticker:
                self.storage.add_price(stock.id, price)
                self.storage.delete_old_prices(stock.id, stock.retention_days)
                break

    def _on_error(self, ticker: str):
        self.status.setText(f"⚠️ Не удалось получить: {ticker}")

    def _on_done(self):
        self.refresh_table()
        self.update_btn.setEnabled(True)
        self.status.setText("✅ Обновлено")


# ─── Запуск ───────────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 11))

    # Storage сам создаёт SQLite — Database.py не нужен
    storage = Storage()
    auth = AuthService(storage)
    analytics = Analytics()
    parser = StockParser()

    # Вход
    login = LoginDialog(auth, auth.is_first_run(), DARK)
    if login.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)

    # Главное окно
    window = MainWindow(storage, auth, analytics, parser)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()