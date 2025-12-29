from __future__ import annotations
import os
from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from schema import Invoice


def _build_system_message(vendor_context: Optional[str] = None) -> str:
    """Build system message for LLM."""
    base_msg = (
        "You extract structured invoice data from raw PDF text. "
        "Return only fields defined in the schema. "
        "If a field is missing, set it to null.\n\n"
        "IMPORTANT FIELD CLARIFICATIONS:\n"
        "- vendor_name: The supplier/vendor who issued the invoice (the seller).\n"
        "- bill_to: The customer/client who receives the invoice (the buyer). "
        "This is NOT the vendor's address. Look for 'Bill To', 'Ship To', 'Customer', or 'Client' sections. "
        "If no bill_to information is found, set it to null.\n"
        "- Do NOT confuse vendor address with bill_to address."
    )
    
    if vendor_context:
        base_msg += f"\n\nIMPORTANT CONTEXT FROM MEMORY:\n{vendor_context}\n\nBe extra careful when extracting data from this vendor."
    
    return base_msg


def parse_invoice_from_text(
    text: str, 
    vendor_name: Optional[str] = None,
    vendor_context: Optional[str] = None
) -> Invoice:
    """Parse invoice from PDF text using LLM."""
    model_name = os.getenv("LLM_MODEL", "").strip()
    if not model_name:
        raise RuntimeError("LLM_MODEL is not set. Please set it in the environment variables.")

    system_msg = _build_system_message(vendor_context)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("human", "Extract invoice fields from this text:\n\n{text}")
    ])

    try:
        llm = ChatAnthropic(
            model=model_name,
            temperature=0
        ).with_structured_output(Invoice)

        chain = prompt | llm
        return chain.invoke({"text": text})
    except Exception as e:
        raise RuntimeError(f"LLM parsing failed: {e}") from e
