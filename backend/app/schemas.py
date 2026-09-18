from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class WarehouseBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(default="", max_length=50)
    location: str = Field(default="", max_length=200)
    description: str = Field(default="", max_length=500)


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    code: Optional[str] = Field(default=None, max_length=50)
    location: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=500)


class ChemicalBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    cas: str = Field(default="", max_length=40)
    purchase_date: Optional[str] = None
    expiration_date: Optional[str] = None
    status: str = Field(default="良好", max_length=30)
    quantity: float = Field(default=0, ge=0)
    unit: str = Field(default="g", max_length=20)
    low_stock_threshold: float = Field(default=0, ge=0)
    warehouse_id: Optional[int] = None
    room: str = Field(default="", max_length=100)
    cabinet: str = Field(default="", max_length=100)
    shelf: str = Field(default="", max_length=100)
    supplier: str = Field(default="", max_length=200)
    brand: str = Field(default="", max_length=200)
    batch_no: str = Field(default="", max_length=100)
    storage_condition: str = Field(default="", max_length=200)
    notes: str = Field(default="", max_length=2000)


class ChemicalCreate(ChemicalBase):
    pass


class ChemicalUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    cas: Optional[str] = Field(default=None, max_length=40)
    purchase_date: Optional[str] = None
    expiration_date: Optional[str] = None
    status: Optional[str] = Field(default=None, max_length=30)
    unit: Optional[str] = Field(default=None, max_length=20)
    low_stock_threshold: Optional[float] = Field(default=None, ge=0)
    warehouse_id: Optional[int] = None
    room: Optional[str] = Field(default=None, max_length=100)
    cabinet: Optional[str] = Field(default=None, max_length=100)
    shelf: Optional[str] = Field(default=None, max_length=100)
    supplier: Optional[str] = Field(default=None, max_length=200)
    brand: Optional[str] = Field(default=None, max_length=200)
    batch_no: Optional[str] = Field(default=None, max_length=100)
    storage_condition: Optional[str] = Field(default=None, max_length=200)
    notes: Optional[str] = Field(default=None, max_length=2000)


class StockMovementCreate(BaseModel):
    chemical_id: int
    movement_type: Literal["in", "out", "return"]
    quantity: float = Field(gt=0)
    operator: str = Field(default="", max_length=100)
    purpose: str = Field(default="", max_length=300)
    reference_no: str = Field(default="", max_length=100)
    notes: str = Field(default="", max_length=1000)
