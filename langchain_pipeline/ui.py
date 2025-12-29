import os
import glob
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from dotenv import load_dotenv

from pdf_loader import load_pdf_text
from parser import parse_invoice_from_text
from memory_bank import MemoryBank

load_dotenv()
USE_LLM = True


class InvoiceProcessorUI:
    def __init__(self, root):
        """Initialize UI."""
        self.root = root
        self.root.title("Invoice Processing System")
        self.root.geometry("900x750")
        
        self.memory = MemoryBank("memory_bank.json")
        self.processing = False
        
        self.setup_ui()
        self.refresh_file_list()
    
    def setup_ui(self):
        """Setup UI components."""
        title_label = tk.Label(
            self.root, 
            text="Invoice Processing System", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        self.status_label = tk.Label(
            self.root, 
            text="Mode: LLM (Always)", 
            font=("Arial", 10)
        )
        self.status_label.pack(pady=5)
        
        file_frame = tk.LabelFrame(self.root, text="Select PDF Files", padx=10, pady=10)
        file_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        listbox_frame = tk.Frame(file_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(
            listbox_frame, 
            selectmode=tk.EXTENDED,
            yscrollcommand=scrollbar.set,
            font=("Arial", 10)
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        button_frame = tk.Frame(file_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        refresh_btn = tk.Button(
            button_frame, 
            text="Refresh List", 
            command=self.refresh_file_list,
            width=15
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        select_all_btn = tk.Button(
            button_frame, 
            text="Select All", 
            command=self.select_all,
            width=15
        )
        select_all_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(
            button_frame, 
            text="Clear Selection", 
            command=self.clear_selection,
            width=15
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.process_btn = tk.Button(
            self.root, 
            text="Process Selected Files", 
            command=self.process_selected_files,
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10
        )
        self.process_btn.pack(pady=10)
        
        self.progress_var = tk.StringVar(value="Ready")
        progress_label = tk.Label(self.root, textvariable=self.progress_var, font=("Arial", 10))
        progress_label.pack(pady=5)
        
        self.progress_bar = ttk.Progressbar(
            self.root, 
            mode='indeterminate',
            length=400
        )
        self.progress_bar.pack(pady=5)
        
        results_frame = tk.LabelFrame(self.root, text="Results & Logs", padx=10, pady=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.results_text = scrolledtext.ScrolledText(
            results_frame, 
            height=12,
            font=("Consolas", 9),
            wrap=tk.WORD
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        stats_btn = tk.Button(
            self.root, 
            text="View Memory Bank Stats", 
            command=self.show_memory_stats,
            width=20
        )
        stats_btn.pack(pady=5)
    
    def refresh_file_list(self):
        """Refresh file list."""
        self.file_listbox.delete(0, tk.END)
        pdf_files = sorted(glob.glob("pdf/*.pdf"))
        
        if not pdf_files:
            self.file_listbox.insert(0, "No PDF files found in pdf/ directory")
            return
        
        for pdf_file in pdf_files:
            filename = os.path.basename(pdf_file)
            if self.memory.seen(filename):
                status = self.memory.last_status(filename)
                if status and status != "OK":
                    display_name = f"{filename} [{status}]"
                else:
                    display_name = filename
            else:
                display_name = filename
            self.file_listbox.insert(tk.END, display_name)
    
    def select_all(self):
        """Select all files."""
        self.file_listbox.selection_set(0, tk.END)
    
    def clear_selection(self):
        """Clear selection."""
        self.file_listbox.selection_clear(0, tk.END)
    
    def get_selected_files(self):
        """Get selected files."""
        selected_indices = self.file_listbox.curselection()
        pdf_files = sorted(glob.glob("pdf/*.pdf"))
        
        if not pdf_files:
            return []
        
        selected_paths = []
        for idx in selected_indices:
            if idx < len(pdf_files):
                selected_paths.append(pdf_files[idx])
        
        return selected_paths
    
    def process_selected_files(self):
        """Process selected files."""
        if self.processing:
            messagebox.showwarning("Processing", "Files are already being processed. Please wait.")
            return
        
        selected_paths = self.get_selected_files()
        
        if not selected_paths:
            messagebox.showwarning("No Selection", "Please select at least one file to process.")
            return
        
        file_count = len(selected_paths)
        confirm = messagebox.askyesno(
            "Confirm Processing",
            f"Process {file_count} file(s) with LLM?\n\n" + 
            "\n".join([os.path.basename(f) for f in selected_paths[:5]]) +
            (f"\n... and {file_count - 5} more" if file_count > 5 else "")
        )
        
        if not confirm:
            return
        
        self.process_btn.config(state=tk.DISABLED)
        self.processing = True
        self.progress_bar.start()
        self.progress_var.set(f"Processing {file_count} file(s)...")
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"Starting processing of {file_count} file(s)...\n")
        self.results_text.insert(tk.END, "=" * 60 + "\n\n")
        
        thread = threading.Thread(target=self._process_files_thread, args=(selected_paths,))
        thread.daemon = True
        thread.start()
    
    def _process_files_thread(self, pdf_paths):
        """Process files in background thread."""
        try:
            rows, memory = self._process_files(pdf_paths, self.memory, start_new_run=True)
            self.root.after(0, self._processing_complete, rows, memory, None)
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self.root.after(0, self._processing_complete, [], self.memory, error_msg)
    
    def _log(self, message):
        """Log message to results text."""
        self.root.after(0, lambda: self.results_text.insert(tk.END, message + "\n"))
        self.root.after(0, lambda: self.results_text.see(tk.END))
    
    def _process_files(self, pdf_paths, memory=None, start_new_run=True):
        """Process PDF invoice files."""
        if memory is None:
            memory = MemoryBank("memory_bank.json")
        
        rows = []

        if start_new_run:
            memory.start_run(
                {
                    "use_llm": USE_LLM,
                    "parser_version": "v1",
                    "app": "invoice_extractor",
                }
            )

        for path in pdf_paths:
            fname = os.path.basename(path)
            self._log(f"Processing: {fname}")
            
            used_llm = USE_LLM
            error_msg = None

            try:
                text = load_pdf_text(path)
                self._log(f"  ✓ PDF loaded successfully")
                
                temp_inv = parse_invoice_from_text(text)
                self._log(f"  ✓ LLM parsing completed")
                
                vendor_context = None
                
                if temp_inv.vendor_name and memory.is_flagged_vendor(temp_inv.vendor_name):
                    flagged_info = memory.data.get("flagged_vendors", {}).get(temp_inv.vendor_name, {})
                    vendor_context = (
                        f"Vendor '{temp_inv.vendor_name}' was previously flagged {flagged_info.get('count', 0)} time(s). "
                        f"Last issue: {flagged_info.get('last_reason', 'unknown')}. "
                        f"Be extra careful when extracting data from this vendor."
                    )
                    self._log(f"  ⚠ Vendor '{temp_inv.vendor_name}' is flagged - re-parsing with context")
                    inv = parse_invoice_from_text(
                        text, 
                        vendor_name=temp_inv.vendor_name,
                        vendor_context=vendor_context
                    )
                else:
                    inv = temp_inv

                memory.apply_vendor_policy(inv)

                if inv.line_items:
                    self._log(f"  ✓ Found {len(inv.line_items)} line item(s)")
                    for line_item in inv.line_items:
                        rows.append({
                            "file": fname,
                            "vendor_name": inv.vendor_name,
                            "invoice_date": str(inv.invoice_date) if inv.invoice_date else None,
                            "invoice_number": inv.invoice_number,
                            "currency": inv.currency,
                            "bill_to": inv.bill_to,
                            "description": line_item.description,
                            "quantity": line_item.quantity,
                            "rate": line_item.unit_price,
                            "amount": line_item.amount,
                            "status": inv.status,
                        })
                else:
                    self._log(f"  ✓ No line items - using total amount")
                    rows.append({
                        "file": fname,
                        "vendor_name": inv.vendor_name,
                        "invoice_date": str(inv.invoice_date) if inv.invoice_date else None,
                        "invoice_number": inv.invoice_number,
                        "currency": inv.currency,
                        "bill_to": inv.bill_to,
                        "description": None,
                        "quantity": None,
                        "rate": None,
                        "amount": inv.total_amount,
                        "status": inv.status,
                    })

                memory.record_result(
                    fname,
                    used_llm=used_llm,
                    vendor_name=inv.vendor_name,
                    invoice_number=inv.invoice_number,
                    invoice_date=str(inv.invoice_date) if inv.invoice_date else None,
                    total_amount=inv.total_amount,
                    currency=inv.currency,
                    status=inv.status,
                    review_reason=inv.review_reason,
                    error=None,
                )
                
                self._log(f"  ✓ Status: {inv.status}")
                self._log("")

            except Exception as e:
                error_msg = repr(e)
                self._log(f"  ✗ ERROR: {error_msg}")
                self._log("")
                
                memory.record_result(
                    fname,
                    used_llm=used_llm,
                    vendor_name=None,
                    invoice_number=None,
                    invoice_date=None,
                    total_amount=None,
                    currency=None,
                    status="ERROR",
                    review_reason=None,
                    error=error_msg,
                )

        self._log("=" * 60)
        self._log(f"Total rows extracted: {len(rows)}")
        
        try:
            df = pd.DataFrame(rows)
            if len(df) > 0:
                df.to_excel("invoices_ui.xlsx", index=False, engine='openpyxl')
                self._log(f"✓ Saved to: invoices_ui.xlsx")
            else:
                self._log("⚠ No data to save (empty DataFrame)")
        except Exception as e:
            self._log(f"✗ Error saving Excel: {e}")
            try:
                df = pd.DataFrame(rows)
                if len(df) > 0:
                    df.to_csv("invoices_ui.csv", index=False)
                    self._log(f"✓ Saved to: invoices_ui.csv (fallback)")
            except Exception as e2:
                self._log(f"✗ Error saving CSV: {e2}")

        memory.end_run()
        return rows, memory
    
    def _processing_complete(self, rows, memory, error):
        """Handle processing completion."""
        self.progress_bar.stop()
        self.processing = False
        self.process_btn.config(state=tk.NORMAL)
        
        if error:
            self.progress_var.set("Error occurred")
            self.results_text.insert(tk.END, f"\n{'=' * 60}\n")
            self.results_text.insert(tk.END, f"ERROR:\n{error}\n")
            messagebox.showerror("Processing Error", f"An error occurred:\n{error}")
        else:
            self.progress_var.set(f"Completed! Processed {len(rows)} line item(s)")
            self.results_text.insert(tk.END, f"\n{'=' * 60}\n")
            self.results_text.insert(tk.END, f"✓ Processing completed successfully!\n\n")
            self.results_text.insert(tk.END, f"Total line items extracted: {len(rows)}\n")
            self.results_text.insert(tk.END, f"Results saved to: invoices_ui.xlsx\n\n")
            summary = memory.summary_text()
            self.results_text.insert(tk.END, f"Memory Bank Summary:\n{summary}\n")
            
            messagebox.showinfo(
                "Processing Complete",
                f"Successfully processed files!\n\n"
                f"Extracted {len(rows)} line item(s)\n"
                f"Results saved to invoices_ui.xlsx"
            )
            self.refresh_file_list()
    
    def show_memory_stats(self):
        """Show memory bank statistics."""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Memory Bank Statistics")
        stats_window.geometry("500x400")
        
        stats_text = scrolledtext.ScrolledText(stats_window, font=("Consolas", 10))
        stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        summary = self.memory.summary_text()
        stats_text.insert(1.0, summary + "\n\n")
        flagged = self.memory.data.get("flagged_vendors", {})
        if flagged:
            stats_text.insert(tk.END, "Flagged Vendors:\n")
            stats_text.insert(tk.END, "-" * 50 + "\n")
            for vendor, info in flagged.items():
                stats_text.insert(
                    tk.END,
                    f"• {vendor}\n"
                    f"  Count: {info.get('count', 0)}\n"
                    f"  Last reason: {info.get('last_reason', 'N/A')}\n"
                    f"  Last seen: {info.get('last_seen_israel', 'N/A')}\n\n"
                )
        else:
            stats_text.insert(tk.END, "No flagged vendors.\n")


def run_ui():
    """Run UI."""
    root = tk.Tk()
    app = InvoiceProcessorUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_ui()

