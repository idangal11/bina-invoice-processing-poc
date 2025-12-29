from datetime import date
from itertools import count
from random import choice, randint, uniform
from schema import Invoice, LineItem

_counter = count(1)

VENDORS = [
    "TechNova Solutions",
    "QuickSupply IL",
    "Stratford & Oak Consulting",
    "Global Services Ltd",
    "Digital Innovations Inc",
]

BILL_TO_OPTIONS = [
    "Global Corp Ltd.\nAttn: Finance Dept.\nTel Aviv, Israel",
    "Acme Corporation\n123 Business St.\nNew York, NY 10001",
    "European Trading Co.\nBerlin, Germany",
    "Local Business Solutions\nJerusalem, Israel",
    "International Partners\nLondon, UK",
]

LINE_ITEM_DESCRIPTIONS = [
    "Cloud Server Hosting (AWS Reserved)",
    "API Gateway Usage - Tier 2",
    "Dedicated Support Plan (Monthly)",
    "Software License - Annual",
    "Consulting Services - 40 hours",
    "Data Storage - 1TB",
    "Network Bandwidth - Premium",
    "Security Monitoring Service",
    "Backup & Recovery Service",
    "Technical Support - Priority",
]

CURRENCIES = ["USD", "EUR", "ILS"]


def mock_invoice() -> Invoice:
    """Generate mock invoice data for testing."""
    i = next(_counter)
    currency = choice(CURRENCIES)
    num_items = randint(2, 4)
    line_items = []
    total = 0.0
    
    for _ in range(num_items):
        quantity = randint(1, 12)
        unit_price = round(uniform(20, 500), 2)
        amount = round(quantity * unit_price, 2)
        total += amount
        
        line_items.append(LineItem(
            description=choice(LINE_ITEM_DESCRIPTIONS),
            quantity=float(quantity),
            unit_price=unit_price,
            amount=amount,
        ))
    
    total = round(total, 2)

    return Invoice(
        vendor_name=choice(VENDORS),
        invoice_date=date(2024, 10, randint(1, 28)),
        invoice_number=f"INV-2024-{1000 + i:04d}",
        total_amount=total,
        currency=currency,
        bill_to=choice(BILL_TO_OPTIONS),
        line_items=line_items,
        status="OK",
    )
