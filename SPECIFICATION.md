# Invoice Processing System - Specification

## Goal
Extract structured invoice data from PDF files using LangChain and AI, with persistent memory for learning and optimization.

## Entities

### Invoice
- Main entity representing an invoice document
- Contains vendor information, dates, amounts, and line items

### LineItem
- Individual item within an invoice
- Contains description, quantity, rate, and amount

### MemoryBank
- Persistent storage for processed files, vendor flags, and statistics
- Enables learning from past processing

## Schema

### Invoice Schema
```python
Invoice:
  - vendor_name: str (required)
  - invoice_date: date (optional)
  - invoice_number: str (optional)
  - total_amount: float (optional)
  - currency: Currency (USD|EUR|ILS, optional)
  - bill_to: str (optional)
  - line_items: List[LineItem] (default: [])
  - status: Literal["OK", "NEEDS_REVIEW", "ERROR"] (default: "OK")
  - review_reason: str (optional)
```

### LineItem Schema
```python
LineItem:
  - description: str (required)
  - quantity: float (optional)
  - unit_price: float (optional)
  - amount: float (optional)
```

## Constraints

1. **Schema Enforcement**: Must use Pydantic with `with_structured_output()` - no prompt-based JSON
2. **Document Loading**: Must use LangChain `DocumentLoader` (PyPDFLoader)
3. **Memory Integration**: Memory Bank must influence chain behavior (vendor context)
4. **Output Format**: Excel file with line items as separate rows
5. **Error Handling**: Graceful error handling with try-catch blocks

## Output

### Excel File Structure
- **File**: `invoices.xlsx`
- **Columns**: file, vendor_name, invoice_date, invoice_number, currency, bill_to, description, quantity, rate, amount, status
- **Rows**: One row per line item (same invoice metadata repeated for each item)

