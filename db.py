"""Buyurtmalar bazasi (SQLite)."""
import sqlite3
from datetime import datetime

KUTILMOQDA = "kutilmoqda"
TASDIQLANDI = "tasdiqlandi"
RAD_ETILDI = "rad_etildi"

YANGI = "yangi"
QAYTA = "qayta"


class DB:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                machine_code TEXT NOT NULL,
                kind TEXT NOT NULL DEFAULT 'yangi',
                receipt_file_id TEXT,
                status TEXT NOT NULL DEFAULT 'kutilmoqda',
                password TEXT,
                created_at TEXT NOT NULL,
                decided_at TEXT
            )"""
        )
        self.conn.commit()

    def add_order(self, user_id, username, name, phone, machine_code, kind, receipt_file_id) -> int:
        cur = self.conn.execute(
            "INSERT INTO orders (user_id, username, name, phone, machine_code, kind,"
            " receipt_file_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, name, phone, machine_code, kind, receipt_file_id,
             datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        self.conn.commit()
        return cur.lastrowid

    def get(self, order_id: int):
        return self.conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    def decide(self, order_id: int, status: str, password: str | None = None) -> bool:
        """Faqat kutilayotgan buyurtmani o'zgartiradi. O'zgargan bo'lsa True."""
        cur = self.conn.execute(
            "UPDATE orders SET status = ?, password = ?, decided_at = ?"
            " WHERE id = ? AND status = ?",
            (status, password, datetime.now().strftime("%Y-%m-%d %H:%M"), order_id, KUTILMOQDA),
        )
        self.conn.commit()
        return cur.rowcount == 1

    def has_approved(self, user_id: int) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM orders WHERE user_id = ? AND status = ? LIMIT 1",
            (user_id, TASDIQLANDI),
        ).fetchone()
        return row is not None

    def recent(self, limit: int = 30):
        return self.conn.execute(
            "SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()

    def stats(self) -> dict:
        rows = self.conn.execute("SELECT status, COUNT(*) n FROM orders GROUP BY status").fetchall()
        return {r["status"]: r["n"] for r in rows}
