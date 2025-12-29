import glob
import os
import pandas as pd
from typing import Tuple, List
from dotenv import load_dotenv
from pdf_loader import load_pdf_text
from parser import parse_invoice_from_text
from mock_data import mock_invoice
from memory_bank import MemoryBank
from schema import Invoice

load_dotenv()

USE_LLM = os.getenv("USE_LLM", "false").strip().lower() == "true"
memory = MemoryBank("memory_bank.json")


def _build_vendor_context(memory: MemoryBank, vendor_name: str) -> str:
    """Build vendor context message for flagged vendors."""
    flagged_info = memory.data.get("flagged_vendors", {}).get(vendor_name, {})
    return (
        f"Vendor '{vendor_name}' was previously flagged {flagged_info.get('count', 0)} time(s). "
        f"Last issue: {flagged_info.get('last_reason', 'unknown')}. "
        f"Be extra careful when extracting data from this vendor."
    )


def _parse_invoice_with_memory(text: str, memory: MemoryBank) -> Invoice:
    """Parse invoice with memory context for flagged vendors."""
    temp_inv = parse_invoice_from_text(text)
    
    if temp_inv.vendor_name and memory.is_flagged_vendor(temp_inv.vendor_name):
        vendor_context = _build_vendor_context(memory, temp_inv.vendor_name)
        return parse_invoice_from_text(
            text,
            vendor_name=temp_inv.vendor_name,
            vendor_context=vendor_context
        )
    
    return temp_inv


def _invoice_to_rows(invoice: Invoice, filename: str) -> List[dict]:
    """Convert invoice to row data structure."""
    rows = []
    base_data = {
        "file": filename,
        "vendor_name": invoice.vendor_name,
        "invoice_date": str(invoice.invoice_date) if invoice.invoice_date else None,
        "invoice_number": invoice.invoice_number,
        "currency": invoice.currency,
        "bill_to": invoice.bill_to,
        "status": invoice.status,
    }
    
    if invoice.line_items:
        for line_item in invoice.line_items:
            rows.append({
                **base_data,
                "description": line_item.description,
                "quantity": line_item.quantity,
                "rate": line_item.unit_price,
                "amount": line_item.amount,
            })
    else:
        rows.append({
            **base_data,
            "description": None,
            "quantity": None,
            "rate": None,
            "amount": invoice.total_amount,
        })
    
    return rows


def _process_single_file(path: str, memory: MemoryBank) -> Tuple[List[dict], bool]:
    """Process a single PDF file and return rows and success status."""
    fname = os.path.basename(path)
    print("Processing:", fname)
    
    try:
        if USE_LLM:
            text = load_pdf_text(path)
            inv = _parse_invoice_with_memory(text, memory)
        else:
            inv = mock_invoice()
        
        memory.apply_vendor_policy(inv)
        rows = _invoice_to_rows(inv, fname)
        
        memory.record_result(
            fname,
            used_llm=USE_LLM,
            vendor_name=inv.vendor_name,
            invoice_number=inv.invoice_number,
            invoice_date=str(inv.invoice_date) if inv.invoice_date else None,
            total_amount=inv.total_amount,
            currency=inv.currency,
            status=inv.status,
            review_reason=inv.review_reason,
            error=None,
        )
        
        return rows, True
        
    except Exception as e:
        error_msg = repr(e)
        print("ERROR:", fname, error_msg)
        
        memory.record_result(
            fname,
            used_llm=USE_LLM,
            vendor_name=None,
            invoice_number=None,
            invoice_date=None,
            total_amount=None,
            currency=None,
            status="ERROR",
            review_reason=None,
            error=error_msg,
        )
        
        return [], False


def _save_results(rows: List[dict]) -> None:
    """Save processing results to Excel file."""
    try:
        df = pd.DataFrame(rows)
        df.to_excel("invoices.xlsx", index=False, engine='openpyxl')
        print("Saved: invoices.xlsx")
    except Exception as e:
        print(f"Error saving Excel file: {e}")
        raise


def process_files(pdf_paths: List[str], memory: MemoryBank = None, start_new_run: bool = True) -> Tuple[List[dict], MemoryBank]:
    """Process PDF invoice files and extract data."""
    if memory is None:
        memory = MemoryBank("memory_bank.json")
    
    if start_new_run:
        memory.start_run({
            "use_llm": USE_LLM,
            "parser_version": "v1",
            "app": "invoice_extractor",
        })
    
    all_rows = []
    for path in pdf_paths:
        rows, _ = _process_single_file(path, memory)
        all_rows.extend(rows)
    
    _save_results(all_rows)
    memory.end_run()
    
    return all_rows, memory


def main():
    """Batch process all PDF invoices."""
    global memory
    pdf_paths = sorted(glob.glob("pdf/*.pdf"))
    rows, memory = process_files(pdf_paths, memory, start_new_run=True)
    print(memory.summary_text())


if __name__ == "__main__":
    print("USE_LLM =", USE_LLM)
    main()
