"""Bot bazasi (SQLite): mijozlar, plaginlar, litsenziyalar, buyurtmalar, videolar."""
import secrets
import sqlite3
from datetime import datetime

# buyurtma holati
KUTILMOQDA = "kutilmoqda"
TASDIQLANDI = "tasdiqlandi"
RAD_ETILDI = "rad_etildi"

# buyurtma turi (eski bot): yangi xarid / qayta faollashtirish
YANGI = "yangi"
QAYTA = "qayta"

# litsenziya holati
FAOL = "faol"            # kompyuterga bog'langan, kod berilgan
BOSH = "bosh"            # kompyuterdan bo'shatilgan, yangi PC'ga to'lovsiz beriladi
BLOKLANGAN = "bloklangan"

# litsenziya manbai
XARID = "xarid"
ESKI = "eski"            # eski TZ- paroldan ko'chirilgan
ADMIN = "admin"          # admin qo'lda bergan

MAX_DEACT = 3            # jami ko'chirishlar soni; undan keyingi urinishda blok

PW_ALPHA = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def new_secret() -> str:
    return "".join(secrets.choice(PW_ALPHA + "abcdefghjkmnpqrstuvwxyz") for _ in range(32))


class DB:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._schema()

    # ------------------------------------------------------------ sxema
    def _schema(self):
        c = self.conn
        c.execute(
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
        # eski bazaga yangi ustunlar (eski buyurtmalarda plugin = NULL, ya'ni TZ- tizimi)
        cols = {r["name"] for r in c.execute("PRAGMA table_info(orders)")}
        if "plugin" not in cols:
            c.execute("ALTER TABLE orders ADD COLUMN plugin TEXT")
        if "license_id" not in cols:
            c.execute("ALTER TABLE orders ADD COLUMN license_id INTEGER")

        c.execute(
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS plugins (
                prefix TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                price TEXT NOT NULL,
                zip_file_id TEXT,
                zip_name TEXT,
                secret TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plugin TEXT NOT NULL,
                mid TEXT,
                code TEXT,
                status TEXT NOT NULL,
                source TEXT NOT NULL,
                deact_count INTEGER NOT NULL DEFAULT 0,
                last_deact_at TEXT,
                order_id INTEGER,
                created_at TEXT NOT NULL,
                activated_at TEXT
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS deactivations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                mid TEXT,
                reason TEXT NOT NULL,
                confirmed INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                file_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        c.commit()

    # ------------------------------------------------------------ mijozlar
    def get_user(self, user_id: int):
        return self.conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()

    def save_user(self, user_id: int, username, name: str, phone: str):
        self.conn.execute(
            "INSERT INTO users (user_id, username, name, phone, created_at) VALUES (?, ?, ?, ?, ?)"
            " ON CONFLICT(user_id) DO UPDATE SET username = excluded.username,"
            " name = excluded.name, phone = excluded.phone",
            (user_id, username, name, phone, now()),
        )
        self.conn.commit()

    # ------------------------------------------------------------ plaginlar
    def add_plugin(self, prefix: str, name: str, price: str, description: str = "",
                   secret: str | None = None) -> str:
        secret = secret or new_secret()
        self.conn.execute(
            "INSERT INTO plugins (prefix, name, description, price, secret, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (prefix, name, description, price, secret, now()),
        )
        self.conn.commit()
        return secret

    def get_plugin(self, prefix: str):
        return self.conn.execute("SELECT * FROM plugins WHERE prefix = ?", (prefix,)).fetchone()

    def plugins(self, only_active: bool = True):
        q = "SELECT * FROM plugins" + (" WHERE active = 1" if only_active else "") + " ORDER BY created_at, prefix"
        return self.conn.execute(q).fetchall()

    def prefixes(self) -> list[str]:
        return [r["prefix"] for r in self.conn.execute("SELECT prefix FROM plugins")]

    def update_plugin(self, prefix: str, **fields) -> bool:
        allowed = {"name", "description", "price", "zip_file_id", "zip_name", "active"}
        fields = {k: v for k, v in fields.items() if k in allowed}
        if not fields:
            return False
        sets = ", ".join(f"{k} = ?" for k in fields)
        cur = self.conn.execute(f"UPDATE plugins SET {sets} WHERE prefix = ?", (*fields.values(), prefix))
        self.conn.commit()
        return cur.rowcount == 1

    # ------------------------------------------------------------ buyurtmalar
    def add_order(self, user_id, username, name, phone, machine_code, kind, receipt_file_id,
                  plugin: str | None = None) -> int:
        cur = self.conn.execute(
            "INSERT INTO orders (user_id, username, name, phone, machine_code, kind,"
            " receipt_file_id, created_at, plugin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, name, phone, machine_code, kind, receipt_file_id, now(), plugin),
        )
        self.conn.commit()
        return cur.lastrowid

    def get(self, order_id: int):
        return self.conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    def decide(self, order_id: int, status: str, password: str | None = None,
               license_id: int | None = None) -> bool:
        """Faqat kutilayotgan buyurtmani o'zgartiradi. O'zgargan bo'lsa True."""
        cur = self.conn.execute(
            "UPDATE orders SET status = ?, password = ?, license_id = ?, decided_at = ?"
            " WHERE id = ? AND status = ?",
            (status, password, license_id, now(), order_id, KUTILMOQDA),
        )
        self.conn.commit()
        return cur.rowcount == 1

    def pending_order(self, user_id: int, plugin: str, mid: str):
        return self.conn.execute(
            "SELECT * FROM orders WHERE user_id = ? AND plugin = ? AND machine_code = ? AND status = ?",
            (user_id, plugin, mid, KUTILMOQDA),
        ).fetchone()

    def has_approved(self, user_id: int) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM orders WHERE user_id = ? AND status = ? LIMIT 1",
            (user_id, TASDIQLANDI),
        ).fetchone()
        return row is not None

    def recent(self, limit: int = 30):
        return self.conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

    def stats(self) -> dict:
        rows = self.conn.execute("SELECT status, COUNT(*) n FROM orders GROUP BY status").fetchall()
        return {r["status"]: r["n"] for r in rows}

    def legacy_order(self, machine_code: str):
        """Eski TZ- tizimidagi tasdiqlangan buyurtma (oxirgisi)."""
        return self.conn.execute(
            "SELECT * FROM orders WHERE plugin IS NULL AND machine_code = ? AND status = ?"
            " ORDER BY id DESC LIMIT 1",
            (machine_code, TASDIQLANDI),
        ).fetchone()

    # ------------------------------------------------------------ litsenziyalar
    def get_license(self, license_id: int):
        return self.conn.execute("SELECT * FROM licenses WHERE id = ?", (license_id,)).fetchone()

    def user_licenses(self, user_id: int, plugin: str | None = None):
        q, args = "SELECT * FROM licenses WHERE user_id = ?", [user_id]
        if plugin:
            q += " AND plugin = ?"
            args.append(plugin)
        return self.conn.execute(q + " ORDER BY id", args).fetchall()

    def create_license(self, user_id: int, plugin: str, source: str, mid: str | None = None,
                       code: str | None = None, order_id: int | None = None) -> int:
        status = FAOL if mid else BOSH
        cur = self.conn.execute(
            "INSERT INTO licenses (user_id, plugin, mid, code, status, source, order_id, created_at,"
            " activated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, plugin, mid, code, status, source, order_id, now(), now() if mid else None),
        )
        self.conn.commit()
        return cur.lastrowid

    def bind_license(self, license_id: int, mid: str, code: str) -> bool:
        """Bo'sh litsenziyani yangi kompyuterga bog'lash."""
        cur = self.conn.execute(
            "UPDATE licenses SET mid = ?, code = ?, status = ?, activated_at = ? WHERE id = ? AND status = ?",
            (mid, code, FAOL, now(), license_id, BOSH),
        )
        self.conn.commit()
        return cur.rowcount == 1

    def deact_check(self, lic) -> str | None:
        """Ko'chirish mumkinmi. Mumkin bo'lsa None, aks holda sabab:
        'holat' (faol emas), 'bugun' (kuniga 1 marta), 'limit' (3 tadan oshdi -> blok)."""
        if lic["status"] != FAOL:
            return "holat"
        if lic["last_deact_at"] and lic["last_deact_at"][:10] == today():
            return "bugun"
        if lic["deact_count"] >= MAX_DEACT:
            return "limit"
        return None

    def block_license(self, license_id: int):
        self.conn.execute("UPDATE licenses SET status = ? WHERE id = ?", (BLOKLANGAN, license_id))
        self.conn.commit()

    def deactivate(self, license_id: int, reason: str, confirmed: bool) -> bool:
        lic = self.get_license(license_id)
        if lic is None or self.deact_check(lic) is not None:
            return False
        self.conn.execute(
            "UPDATE licenses SET status = ?, mid = NULL, code = NULL, deact_count = deact_count + 1,"
            " last_deact_at = ? WHERE id = ?",
            (BOSH, now(), license_id),
        )
        self.conn.execute(
            "INSERT INTO deactivations (license_id, user_id, mid, reason, confirmed, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (license_id, lic["user_id"], lic["mid"], reason, int(confirmed), now()),
        )
        self.conn.commit()
        return True

    def unblock(self, license_id: int) -> bool:
        cur = self.conn.execute(
            "UPDATE licenses SET status = ?, mid = NULL, code = NULL, deact_count = 0 WHERE id = ? AND status = ?",
            (BOSH, license_id, BLOKLANGAN),
        )
        self.conn.commit()
        return cur.rowcount == 1

    def licenses(self, status: str | None = None, plugin: str | None = None, limit: int = 30):
        q = "SELECT l.*, u.name AS uname, u.phone AS uphone FROM licenses l LEFT JOIN users u ON u.user_id = l.user_id"
        conds, args = [], []
        if status:
            conds.append("l.status = ?")
            args.append(status)
        if plugin:
            conds.append("l.plugin = ?")
            args.append(plugin)
        if conds:
            q += " WHERE " + " AND ".join(conds)
        return self.conn.execute(q + " ORDER BY l.id DESC LIMIT ?", (*args, limit)).fetchall()

    def legacy_migrated(self, order_id: int) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM licenses WHERE source = ? AND order_id = ? LIMIT 1", (ESKI, order_id)
        ).fetchone()
        return row is not None

    def license_counts(self) -> dict:
        rows = self.conn.execute("SELECT plugin, status, COUNT(*) n FROM licenses GROUP BY plugin, status")
        out: dict = {}
        for r in rows:
            out.setdefault(r["plugin"], {})[r["status"]] = r["n"]
        return out

    # ------------------------------------------------------------ videolar
    def add_video(self, title: str, file_id: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO videos (title, file_id, created_at) VALUES (?, ?, ?)", (title, file_id, now())
        )
        self.conn.commit()
        return cur.lastrowid

    def videos(self):
        return self.conn.execute("SELECT * FROM videos ORDER BY id").fetchall()

    def get_video(self, video_id: int):
        return self.conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()

    def delete_video(self, video_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        self.conn.commit()
        return cur.rowcount == 1
