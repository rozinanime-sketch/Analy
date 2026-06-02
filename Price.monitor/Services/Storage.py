import os
import sys
import sqlite3
import shutil
import hashlib
from datetime import datetime, timedelta

# Корень проекта (на уровень выше папки Services)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.stock import Stock, PriceRecord

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'stocks.db')


class Storage:
    def __init__(self):
        os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
        self.db_path = os.path.abspath(DB_PATH)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    password_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    target_price REAL DEFAULT 0,
                    retention_days INTEGER DEFAULT 30
                );
                CREATE TABLE IF NOT EXISTS prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_id INTEGER NOT NULL,
                    price REAL NOT NULL,
                    recorded_at TEXT NOT NULL,
                    FOREIGN KEY (stock_id) REFERENCES stocks(id)
                );
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    detail TEXT,
                    created_at TEXT NOT NULL
                );
            """)

    # --- Backup & Integrity ---

    def backup(self):
        if os.path.exists(self.db_path):
            shutil.copy(self.db_path, self.db_path + '.bak')

    def get_checksum(self) -> str:
        with open(self.db_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def verify_integrity(self, saved_checksum: str) -> bool:
        return self.get_checksum() == saved_checksum

    # --- Logs ---

    def log(self, action: str, detail: str = ''):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO logs (action, detail, created_at) VALUES (?, ?, ?)",
                (action, detail, datetime.now().isoformat())
            )

    # --- Auth (интерфейс для AuthService) ---

    def get_user(self) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users LIMIT 1").fetchone()
            return dict(row) if row else None

    def set_user_password(self, password_hash: str):
        self.backup()
        with self._connect() as conn:
            conn.execute("DELETE FROM users")
            conn.execute("INSERT INTO users (password_hash) VALUES (?)", (password_hash,))
        self.log('set_password')

    # --- Stocks ---

    def get_all_stocks(self) -> list[Stock]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM stocks").fetchall()
            return [Stock(r['id'], r['ticker'], r['name'], r['target_price'], r['retention_days']) for r in rows]

    def add_stock(self, ticker: str, name: str, target_price: float = 0, retention_days: int = 30):
        self.backup()
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO stocks (ticker, name, target_price, retention_days) VALUES (?, ?, ?, ?)",
                (ticker.upper(), name, target_price, retention_days)
            )
        self.log('add_stock', ticker)

    def delete_stock(self, stock_id: int):
        self.backup()
        with self._connect() as conn:
            conn.execute("DELETE FROM prices WHERE stock_id = ?", (stock_id,))
            conn.execute("DELETE FROM stocks WHERE id = ?", (stock_id,))
        self.log('delete_stock', str(stock_id))

    def update_stock(self, stock_id: int, target_price: float, retention_days: int):
        self.backup()
        with self._connect() as conn:
            conn.execute(
                "UPDATE stocks SET target_price=?, retention_days=? WHERE id=?",
                (target_price, retention_days, stock_id)
            )
        self.log('update_stock', str(stock_id))

    # --- Prices ---

    def add_price(self, stock_id: int, price: float):
        self.backup()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO prices (stock_id, price, recorded_at) VALUES (?, ?, ?)",
                (stock_id, price, datetime.now().isoformat())
            )
        self.log('add_price', f"stock_id={stock_id} price={price}")

    def get_prices(self, stock_id: int) -> list[PriceRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM prices WHERE stock_id=? ORDER BY recorded_at ASC",
                (stock_id,)
            ).fetchall()
            return [PriceRecord(r['stock_id'], r['price'], r['recorded_at']) for r in rows]

    def delete_old_prices(self, stock_id: int, retention_days: int):
        cutoff = (datetime.now() - timedelta(days=retention_days)).isoformat()
        self.backup()
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM prices WHERE stock_id=? AND recorded_at < ?",
                (stock_id, cutoff)
            )
        self.log('delete_old_prices', f"stock_id={stock_id} cutoff={cutoff}")