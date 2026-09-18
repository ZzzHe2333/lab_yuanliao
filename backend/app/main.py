from __future__ import annotations

import re
import shutil
from datetime import date
from pathlib import Path
from typing import Literal

import qrcode
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .database import QR_DIR, SDS_DIR, get_db, init_db
from .schemas import (\n    ChemicalCreate,\n    ChemicalUpdate,\n    StockMovementCreate,\n    WarehouseCreate,\n    WarehouseUpdate,\n)

app = FastAPI(
    title="实验室原料管理系统 API",
    version="0.1.0",
    description="ChemTrack 风格的实验室原料、SDS、二维码和仓库管理后端。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


def chemical_with_meta(row) -> dict:
    item = dict(row)
    exp = item.get("expiration_date")
    item["is_expired"] = bool(exp and exp < date.today().isoformat())
    item["is_low_stock"] = bool(
        item.get("low_stock_threshold", 0) > 0
        and item.get("quantity", 0) <= item.get("low_stock_threshold", 0)
    )
    return item


def require_chemical(db, chemical_id: int):
    row = db.execute(
        """
        SELECT c.*, w.name AS warehouse_name
        FROM chemicals c
        LEFT JOIN warehouses w ON w.id = c.warehouse_id
        WHERE c.id = ?
        """,
        (chemical_id,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="原料不存在")
    return row


@app.get("/api/v1/health")
def health():
    return {"ok": True}


@app.get("/api/v1/dashboard/stats")
def dashboard_stats():
    today = date.today().isoformat()
    with get_db() as db:
        total = db.execute("SELECT COUNT(*) n FROM chemicals").fetchone()["n"]
        warehouses = db.execute("SELECT COUNT(*) n FROM warehouses").fetchone()["n"]
        expired = db.execute(
            "SELECT COUNT(*) n FROM chemicals WHERE expiration_date IS NOT NULL AND expiration_date != '' AND expiration_date < ?",
            (today,),
        ).fetchone()["n"]
        low_stock = db.execute(
            "SELECT COUNT(*) n FROM chemicals WHERE low_stock_threshold > 0 AND quantity <= low_stock_threshold"
        ).fetchone()["n"]
        recent = db.execute(
            """
            SELECT c.*, w.name AS warehouse_name
            FROM chemicals c
            LEFT JOIN warehouses w ON w.id = c.warehouse_id
            ORDER BY c.id DESC LIMIT 6
            """
        ).fetchall()
    return {
        "total_chemicals": total,
        "warehouses": warehouses,
        "expired": expired,
        "low_stock": low_stock,
        "recent": [chemical_with_meta(r) for r in recent],
    }


@app.get("/api/v1/warehouses")
def list_warehouses():
    with get_db() as db:
        rows = db.execute(
            """
            SELECT w.*, COUNT(c.id) AS chemical_count
            FROM warehouses w
            LEFT JOIN chemicals c ON c.warehouse_id = w.id
            GROUP BY w.id
            ORDER BY w.id
            """
        ).fetchall()
    return [dict(r) for r in rows]


@app.post("/api/v1/warehouses", status_code=201)
def create_warehouse(payload: WarehouseCreate):
    with get_db() as db:
        try:
            cur = db.execute(
                "INSERT INTO warehouses(name, code, location, description) VALUES (?, ?, ?, ?)",
                (payload.name, payload.code, payload.location, payload.description),
            )
        except Exception as exc:
            if "UNIQUE" in str(exc).upper():
                raise HTTPException(status_code=409, detail="仓库名称已存在") from exc
            raise
        row = db.execute("SELECT * FROM warehouses WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


@app.put("/api/v1/warehouses/{warehouse_id}")
def update_warehouse(warehouse_id: int, payload: WarehouseUpdate):
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")
    with get_db() as db:
        if not db.execute("SELECT id FROM warehouses WHERE id = ?", (warehouse_id,)).fetchone():
            raise HTTPException(status_code=404, detail="仓库不存在")
        sets = ", ".join(f"{key} = ?" for key in fields)
        values = list(fields.values()) + [warehouse_id]
        db.execute(f"UPDATE warehouses SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
        row = db.execute("SELECT * FROM warehouses WHERE id = ?", (warehouse_id,)).fetchone()
    return dict(row)


@app.delete("/api/v1/warehouses/{warehouse_id}")
def delete_warehouse(warehouse_id: int):
    with get_db() as db:
        count = db.execute(
            "SELECT COUNT(*) n FROM chemicals WHERE warehouse_id = ?", (warehouse_id,)
        ).fetchone()["n"]
        if count:
            raise HTTPException(status_code=409, detail="该仓库仍有原料，请先移动或删除相关原料")
        cur = db.execute("DELETE FROM warehouses WHERE id = ?", (warehouse_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="仓库不存在")
    return {"message": "仓库已删除"}


@app.get("/api/v1/chemicals")
def list_chemicals(
    search: str = "",
    warehouse_id: int | None = None,
    status: str = "",
    alert: Literal["", "expired", "low"] = "",
    sort: Literal["id", "name", "purchase_date", "expiration_date", "quantity"] = "id",
    order: Literal["asc", "desc"] = "desc",
):
    clauses = []
    args = []
    if search:
        clauses.append("(c.name LIKE ? OR c.cas LIKE ? OR c.batch_no LIKE ? OR c.supplier LIKE ?)")
        like = f"%{search}%"
        args.extend([like, like, like, like])
    if warehouse_id is not None:
        clauses.append("c.warehouse_id = ?")
        args.append(warehouse_id)
    if status:
        clauses.append("c.status = ?")
        args.append(status)
    if alert == "expired":
        clauses.append(
            "c.expiration_date IS NOT NULL AND c.expiration_date != '' AND c.expiration_date < ?"
        )
        args.append(date.today().isoformat())
    elif alert == "low":
        clauses.append("c.low_stock_threshold > 0 AND c.quantity <= c.low_stock_threshold")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    direction = "ASC" if order == "asc" else "DESC"
    with get_db() as db:
        rows = db.execute(
            f"""
            SELECT c.*, w.name AS warehouse_name
            FROM chemicals c
            LEFT JOIN warehouses w ON w.id = c.warehouse_id
            {where}
            ORDER BY c.{sort} {direction}
            """,
            args,
        ).fetchall()
    return [chemical_with_meta(r) for r in rows]


@app.get("/api/v1/chemicals/{chemical_id}")
def get_chemical(chemical_id: int):
    with get_db() as db:
        return chemical_with_meta(require_chemical(db, chemical_id))


@app.post("/api/v1/chemicals", status_code=201)
def create_chemical(payload: ChemicalCreate):
    data = payload.model_dump()
    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    with get_db() as db:
        if data.get("warehouse_id") is not None and not db.execute(
            "SELECT id FROM warehouses WHERE id = ?", (data["warehouse_id"],)
        ).fetchone():
            raise HTTPException(status_code=400, detail="指定仓库不存在")
        cur = db.execute(
            f"INSERT INTO chemicals ({columns}) VALUES ({placeholders})",
            list(data.values()),
        )
        chemical_id = cur.lastrowid
        if data["quantity"] > 0:
            db.execute(
                """
                INSERT INTO stock_movements(
                    chemical_id, chemical_name, unit, movement_type, quantity,
                    quantity_before, quantity_after, purpose, notes
                ) VALUES (?, ?, ?, 'in', ?, 0, ?, ?, ?)
                """,
                (
                    chemical_id,
                    data["name"],
                    data["unit"],
                    data["quantity"],
                    data["quantity"],
                    "建档初始库存",
                    "创建原料时自动记录",
                ),
            )
        row = require_chemical(db, chemical_id)
    return chemical_with_meta(row)


@app.put("/api/v1/chemicals/{chemical_id}")
def update_chemical(chemical_id: int, payload: ChemicalUpdate):
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")
    with get_db() as db:
        current = require_chemical(db, chemical_id)
        if (
            fields.get("unit")
            and fields["unit"] != current["unit"]
            and float(current["quantity"]) != 0
        ):
            raise HTTPException(
                status_code=409,
                detail="当前库存不为 0，不能直接修改计量单位；请先通过库存流水调整库存",
            )
        if fields.get("warehouse_id") is not None and not db.execute(
            "SELECT id FROM warehouses WHERE id = ?", (fields["warehouse_id"],)
        ).fetchone():
            raise HTTPException(status_code=400, detail="指定仓库不存在")
        sets = ", ".join(f"{key} = ?" for key in fields)
        values = list(fields.values()) + [chemical_id]
        db.execute(
            f"UPDATE chemicals SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )
        row = require_chemical(db, chemical_id)
    return chemical_with_meta(row)


@app.delete("/api/v1/chemicals/{chemical_id}")
def delete_chemical(chemical_id: int):
    with get_db() as db:
        row = require_chemical(db, chemical_id)
        db.execute("DELETE FROM chemicals WHERE id = ?", (chemical_id,))
    sds_filename = row["sds_filename"]
    if sds_filename:
        (SDS_DIR / sds_filename).unlink(missing_ok=True)
    (QR_DIR / f"{chemical_id}.png").unlink(missing_ok=True)
    return {"message": "原料已删除"}


def movement_with_meta(row) -> dict:
    item = dict(row)
    labels = {"in": "入库", "out": "领用", "return": "退库"}
    item["movement_label"] = labels.get(item["movement_type"], item["movement_type"])
    return item


@app.get("/api/v1/stock-movements")
def list_stock_movements(
    chemical_id: int | None = None,
    movement_type: Literal["", "in", "out", "return"] = "",
    search: str = "",
    limit: int = 200,
):
    clauses = []
    args = []
    if chemical_id is not None:
        clauses.append("m.chemical_id = ?")
        args.append(chemical_id)
    if movement_type:
        clauses.append("m.movement_type = ?")
        args.append(movement_type)
    if search:
        clauses.append(
            "(m.chemical_name LIKE ? OR m.operator LIKE ? OR m.purpose LIKE ? OR m.reference_no LIKE ?)"
        )
        like = f"%{search}%"
        args.extend([like, like, like, like])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    safe_limit = min(max(limit, 1), 1000)
    with get_db() as db:
        rows = db.execute(
            f"""
            SELECT m.*, c.name AS current_chemical_name
            FROM stock_movements m
            LEFT JOIN chemicals c ON c.id = m.chemical_id
            {where}
            ORDER BY m.id DESC
            LIMIT ?
            """,
            [*args, safe_limit],
        ).fetchall()
    return [movement_with_meta(row) for row in rows]


@app.post("/api/v1/stock-movements", status_code=201)
def create_stock_movement(payload: StockMovementCreate):
    with get_db() as db:
        chemical = require_chemical(db, payload.chemical_id)
        before = float(chemical["quantity"])
        amount = float(payload.quantity)

        if payload.movement_type == "out":
            if amount > before:
                raise HTTPException(
                    status_code=409,
                    detail=f"库存不足：当前仅有 {before:g} {chemical['unit']}",
                )
            after = before - amount
        else:
            after = before + amount

        db.execute(
            "UPDATE chemicals SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (after, payload.chemical_id),
        )
        cur = db.execute(
            """
            INSERT INTO stock_movements(
                chemical_id, chemical_name, unit, movement_type, quantity,
                quantity_before, quantity_after, operator, purpose, reference_no, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.chemical_id,
                chemical["name"],
                chemical["unit"],
                payload.movement_type,
                amount,
                before,
                after,
                payload.operator,
                payload.purpose,
                payload.reference_no,
                payload.notes,
            ),
        )
        row = db.execute(
            """
            SELECT m.*, c.name AS current_chemical_name
            FROM stock_movements m
            LEFT JOIN chemicals c ON c.id = m.chemical_id
            WHERE m.id = ?
            """,
            (cur.lastrowid,),
        ).fetchone()
    return movement_with_meta(row)


@app.get("/api/v1/chemicals/{chemical_id}/stock-movements")
def chemical_stock_movements(chemical_id: int, limit: int = 50):
    safe_limit = min(max(limit, 1), 500)
    with get_db() as db:
        require_chemical(db, chemical_id)
        rows = db.execute(
            """
            SELECT m.*, c.name AS current_chemical_name
            FROM stock_movements m
            LEFT JOIN chemicals c ON c.id = m.chemical_id
            WHERE m.chemical_id = ?
            ORDER BY m.id DESC
            LIMIT ?
            """,
            (chemical_id, safe_limit),
        ).fetchall()
    return [movement_with_meta(row) for row in rows]


def safe_name(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"}:
        raise HTTPException(status_code=400, detail="SDS 仅支持 PDF/DOC/DOCX/PNG/JPG")
    stem = re.sub(r"[^a-zA-Z0-9_-]+", "_", Path(filename).stem)[:80] or "sds"
    return f"{stem}{suffix}"


@app.post("/api/v1/files/sds/{chemical_id}")
def upload_sds(chemical_id: int, file: UploadFile = File(...)):
    with get_db() as db:
        row = require_chemical(db, chemical_id)
        old = row["sds_filename"]
        filename = f"{chemical_id}_{safe_name(file.filename or 'sds.pdf')}"
        target = SDS_DIR / filename
        with target.open("wb") as out:
            shutil.copyfileobj(file.file, out)
        db.execute(
            "UPDATE chemicals SET sds_filename = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (filename, chemical_id),
        )
    if old and old != filename:
        (SDS_DIR / old).unlink(missing_ok=True)
    return {"message": "SDS 已上传", "filename": filename}


@app.get("/api/v1/files/sds/{chemical_id}")
def get_sds(chemical_id: int):
    with get_db() as db:
        row = require_chemical(db, chemical_id)
    filename = row["sds_filename"]
    if not filename:
        raise HTTPException(status_code=404, detail="该原料尚未上传 SDS")
    path = SDS_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="SDS 文件不存在")
    return FileResponse(path, filename=filename)


@app.delete("/api/v1/files/sds/{chemical_id}")
def delete_sds(chemical_id: int):
    with get_db() as db:
        row = require_chemical(db, chemical_id)
        filename = row["sds_filename"]
        db.execute(
            "UPDATE chemicals SET sds_filename = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (chemical_id,),
        )
    if filename:
        (SDS_DIR / filename).unlink(missing_ok=True)
    return {"message": "SDS 已删除"}


@app.get("/api/v1/files/qrcode/{chemical_id}")
def get_qrcode(chemical_id: int):
    with get_db() as db:
        require_chemical(db, chemical_id)
    path = QR_DIR / f"{chemical_id}.png"
    if not path.exists():
        img = qrcode.make(f"LAB-YUANLIAO:{chemical_id}")
        img.save(path)
    return FileResponse(
        path,
        media_type="image/png",
        filename=f"chemical-{chemical_id}-qr.png",
    )
