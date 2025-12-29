from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List, Literal


Currency = Literal["USD", "EUR", "ILS"]


class LineItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None


class Invoice(BaseModel):
    vendor_name: str = Field(..., description="Supplier / vendor name")
    invoice_date: Optional[date] = None
    invoice_number: Optional[str] = None
    total_amount: Optional[float] = None
    currency: Optional[Currency] = None
    bill_to: Optional[str] = Field(None, description="Customer/client who receives the invoice (the buyer). NOT the vendor address.")
    line_items: List[LineItem] = Field(default_factory=list)

    status: Literal["OK", "NEEDS_REVIEW", "ERROR"] = "OK"
    review_reason: Optional[str] = None
