from fastapi import HTTPException

from app.database import get_db, init_db
from app.main import create_chemical, create_stock_movement
from app.schemas import ChemicalCreate, StockMovementCreate


def reset_tables() -> None:
    init_db()
    with get_db() as db:
        db.execute("DELETE FROM stock_movements")
        db.execute("DELETE FROM chemicals")


def main() -> None:
    reset_tables()

    ordinary = create_chemical(
        ChemicalCreate(name="普通原料测试", quantity=0, unit="g", is_new_material=False)
    )
    try:
        create_stock_movement(
            StockMovementCreate(
                chemical_id=ordinary["id"],
                movement_type="out",
                quantity=1,
                purpose="普通原料超领测试",
            )
        )
    except HTTPException as exc:
        assert exc.status_code == 409
    else:
        raise AssertionError("普通原料库存不足时必须拒绝领用")

    new_material = create_chemical(
        ChemicalCreate(name="新原料测试", quantity=0, unit="g", is_new_material=True)
    )
    outbound = create_stock_movement(
        StockMovementCreate(
            chemical_id=new_material["id"],
            movement_type="out",
            quantity=5,
            purpose="新原料配方消耗测试",
        )
    )
    assert outbound["quantity_before"] == 0
    assert outbound["quantity_after"] == -5
    assert outbound["allow_negative"] == 1

    inbound = create_stock_movement(
        StockMovementCreate(
            chemical_id=new_material["id"],
            movement_type="in",
            quantity=8,
            purpose="新原料补录入库测试",
        )
    )
    assert inbound["quantity_before"] == -5
    assert inbound["quantity_after"] == 3

    with get_db() as db:
        row = db.execute(
            "SELECT quantity, is_new_material FROM chemicals WHERE id = ?",
            (new_material["id"],),
        ).fetchone()
        assert row["quantity"] == 3
        assert row["is_new_material"] == 1

    print("stock rule smoke test passed")


if __name__ == "__main__":
    main()
