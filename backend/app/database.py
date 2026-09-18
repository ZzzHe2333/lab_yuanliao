from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "lab_yuanliao.db"
SDS_DIR = DATA_DIR / "sds"
QR_DIR = DATA_DIR / "qrcodes"


def ensure_data_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SDS_DIR.mkdir(parents=True, exist_ok=True)
    QR_DIR.mkdir(parents=True, exist_ok=True)


def connect() -> sqlite3.Connection:
    ensure_data_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    ensure_data_dirs()
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS warehouses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                code TEXT NOT NULL DEFAULT '',
                location TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chemicals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                cas TEXT NOT NULL DEFAULT '',
                purchase_date TEXT,
                expiration_date TEXT,
                status TEXT NOT NULL DEFAULT '良好',
                quantity REAL NOT NULL DEFAULT 0,
                unit TEXT NOT NULL DEFAULT 'g',
                low_stock_threshold REAL NOT NULL DEFAULT 0,
                warehouse_id INTEGER,
                room TEXT NOT NULL DEFAULT '',
                cabinet TEXT NOT NULL DEFAULT '',
                shelf TEXT NOT NULL DEFAULT '',
                supplier TEXT NOT NULL DEFAULT '',
                brand TEXT NOT NULL DEFAULT '',
                batch_no TEXT NOT NULL DEFAULT '',
                storage_condition TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                sds_filename TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chemical_id INTEGER,
                chemical_name TEXT NOT NULL,
                unit TEXT NOT NULL,
                movement_type TEXT NOT NULL CHECK (movement_type IN ('in', 'out', 'return')),
                quantity REAL NOT NULL CHECK (quantity > 0),
                quantity_before REAL NOT NULL,
                quantity_after REAL NOT NULL,
                operator TEXT NOT NULL DEFAULT '',
                purpose TEXT NOT NULL DEFAULT '',
                reference_no TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chemical_id) REFERENCES chemicals(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_chemicals_name ON chemicals(name);
            CREATE INDEX IF NOT EXISTS idx_chemicals_cas ON chemicals(cas);
            CREATE INDEX IF NOT EXISTS idx_chemicals_warehouse ON chemicals(warehouse_id);
            CREATE INDEX IF NOT EXISTS idx_chemicals_expiration ON chemicals(expiration_date);
            CREATE INDEX IF NOT EXISTS idx_stock_movements_chemical ON stock_movements(chemical_id);
            CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements(movement_type);
            CREATE INDEX IF NOT EXISTS idx_stock_movements_created ON stock_movements(created_at);
            """
        )

        # 为升级前已经存在的库存建立基准流水，避免启用流水功能后历史从空白开始。
        db.execute(
            """
            INSERT INTO stock_movements(
                chemical_id, chemical_name, unit, movement_type, quantity,
                quantity_before, quantity_after, purpose, notes
            )
            SELECT
                c.id, c.name, c.unit, 'in', c.quantity,
                0, c.quantity, '系统迁移初始库存', '启用库存流水功能时自动建立基准'
            FROM chemicals c
            WHERE c.quantity > 0
              AND NOT EXISTS (
                  SELECT 1 FROM stock_movements m WHERE m.chemical_id = c.id
              )
            """
        )

        count = db.execute("SELECT COUNT(*) AS n FROM warehouses").fetchone()["n"]
        if count == 0:
            db.execute(
                "INSERT INTO warehouses(name, code, location, description) VALUES (?, ?, ?, ?)",
                ("主仓库", "MAIN", "", "系统默认仓库"),
            )
