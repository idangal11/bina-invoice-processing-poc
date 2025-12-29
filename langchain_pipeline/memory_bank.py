from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo


def _israel_now_iso() -> str:
    """Get current time in Israel timezone as ISO string."""
    return datetime.now(ZoneInfo("Asia/Jerusalem")).isoformat(timespec="seconds")


class MemoryBank:
    """Persistent memory bank for invoice processing."""

    def __init__(self, path: str = "memory_bank.json"):
        """Initialize memory bank."""
        self.path = path
        self.data: Dict[str, Any] = {
            "processed_files": {},
            "flagged_vendors": {},
            "stats": {
                "total_files_processed": 0,
                "total_runs": 0,
                "llm_used_files": 0,
                "needs_review_files": 0,
                "error_files": 0,
                "skipped_already_processed": 0,
            },
            "run_config": {},
            "schema_version": "invoice_v1",
        }
        self._load()

    def _load(self) -> None:
        """Load memory bank from JSON file."""
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                self.data.update(loaded)
                self.data.setdefault("processed_files", {})
                self.data.setdefault("flagged_vendors", {})
                self.data.setdefault("stats", {})
                self.data["stats"].setdefault("total_files_processed", 0)
                self.data["stats"].setdefault("total_runs", 0)
                self.data["stats"].setdefault("llm_used_files", 0)
                self.data["stats"].setdefault("needs_review_files", 0)
                self.data["stats"].setdefault("error_files", 0)
                self.data["stats"].setdefault("skipped_already_processed", 0)
                self.data.setdefault("run_config", {})
                self.data.setdefault("schema_version", "invoice_v1")
        except Exception:
            pass

    def _save(self) -> None:
        """Save memory bank to JSON file."""
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def start_run(self, run_config: Dict[str, Any]) -> None:
        """Start a new processing run."""
        self.data["stats"]["total_runs"] = int(self.data["stats"].get("total_runs", 0)) + 1
        self.data["run_config"] = {
            **run_config,
            "started_at_israel": _israel_now_iso(),
        }
        self._save()

    def end_run(self) -> None:
        """End current processing run."""
        self.data["run_config"]["ended_at_israel"] = _israel_now_iso()
        self._save()

    def seen(self, filename: str) -> bool:
        """Check if file was already processed."""
        return filename in self.data.get("processed_files", {})

    def mark_skipped(self, filename: str, reason: str = "already_processed") -> None:
        """Mark file as skipped."""
        self.data["stats"]["skipped_already_processed"] = int(
            self.data["stats"].get("skipped_already_processed", 0)
        ) + 1

        self.data["processed_files"].setdefault(filename, {})
        self.data["processed_files"][filename]["last_skipped_at_israel"] = _israel_now_iso()
        self.data["processed_files"][filename]["last_skip_reason"] = reason
        self._save()

    def record_result(
        self,
        filename: str,
        *,
        used_llm: bool,
        vendor_name: Optional[str],
        invoice_number: Optional[str],
        invoice_date: Optional[str],
        total_amount: Optional[float],
        currency: Optional[str],
        status: str,
        review_reason: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Record processing result for a file."""
        pf = self.data.setdefault("processed_files", {})
        pf[filename] = {
            "processed_at_israel": _israel_now_iso(),
            "used_llm": bool(used_llm),
            "vendor_name": vendor_name,
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "total_amount": total_amount,
            "currency": currency,
            "status": status,
            "review_reason": review_reason,
            "error": error,
        }

        self.data["stats"]["total_files_processed"] = int(
            self.data["stats"].get("total_files_processed", 0)
        ) + 1

        if used_llm:
            self.data["stats"]["llm_used_files"] = int(self.data["stats"].get("llm_used_files", 0)) + 1

        if status == "NEEDS_REVIEW":
            self.data["stats"]["needs_review_files"] = int(self.data["stats"].get("needs_review_files", 0)) + 1

        if status == "ERROR":
            self.data["stats"]["error_files"] = int(self.data["stats"].get("error_files", 0)) + 1

        if vendor_name and status in ("NEEDS_REVIEW", "ERROR"):
            self.flag_vendor(vendor_name, reason=review_reason or error or status)

        self._save()

    def is_flagged_vendor(self, vendor: str) -> bool:
        """Check if vendor is flagged."""
        return vendor in self.data.get("flagged_vendors", {})

    def flag_vendor(self, vendor: str, reason: str = "flagged") -> None:
        """Flag a vendor as problematic."""
        fv = self.data.setdefault("flagged_vendors", {})
        entry = fv.get(vendor, {"count": 0, "last_reason": None, "last_seen_israel": None})
        entry["count"] = int(entry.get("count", 0)) + 1
        entry["last_reason"] = reason
        entry["last_seen_israel"] = _israel_now_iso()
        fv[vendor] = entry
        self._save()

    def apply_vendor_policy(self, inv) -> None:
        """Apply vendor learning policy to invoice."""
        vendor = getattr(inv, "vendor_name", None)
        status = getattr(inv, "status", None)

        if not vendor:
            return
        if status == "ERROR":
            return

        if self.is_flagged_vendor(vendor) and status == "OK":
            inv.status = "NEEDS_REVIEW"
            inv.review_reason = "Vendor previously flagged (MemoryBank)"

    def summary_text(self) -> str:
        """Get summary statistics as text."""
        s = self.data.get("stats", {})
        return (
            "MemoryBank summary:\n"
            f"- total_runs: {s.get('total_runs', 0)}\n"
            f"- total_files_processed: {s.get('total_files_processed', 0)}\n"
            f"- llm_used_files: {s.get('llm_used_files', 0)}\n"
            f"- needs_review_files: {s.get('needs_review_files', 0)}\n"
            f"- error_files: {s.get('error_files', 0)}\n"
            f"- skipped_already_processed: {s.get('skipped_already_processed', 0)}\n"
            f"- flagged_vendors: {len(self.data.get('flagged_vendors', {}))}\n"
        )
    
    def last_status(self, filename: str) -> str | None:
        """Get last processing status for a file."""
        pf = self.data.get("processed_files", {})
        entry = pf.get(filename)
        if not entry:
            return None
        return entry.get("status")

