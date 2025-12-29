# Invoice Processing System - Architecture Specification

## 1. System Overview

### 1.1 Purpose
Automated invoice processing system that extracts structured data from PDF invoices using LangChain and AI models, with persistent memory management for learning and optimization.

### 1.2 Core Requirements
- Extract invoice data from PDF files using LangChain DocumentLoader
- Enforce structured output using Pydantic schema validation
- Implement persistent Memory Bank for learning and audit trails
- Export results to Excel format using pandas
- Provide both CLI and GUI interfaces

## 2. Architecture Design

### 2.1 System Architecture

```
┌─────────────────┐
│   Entry Point   │
│   (main.py)     │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
    ┌────▼────┐      ┌────▼────┐
    │   CLI   │      │   UI    │
    │  Mode   │      │  Mode   │
    └────┬────┘      └────┬────┘
         │                 │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │  process_files  │
         │   (orchestrator)│
         └────────┬────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐   ┌────▼────┐   ┌───▼────┐
│ PDF   │   │ Parser  │   │ Memory │
│Loader │   │  (LLM)  │   │  Bank  │
└───┬───┘   └────┬────┘   └───┬────┘
    │            │             │
    └────────────┼─────────────┘
                 │
         ┌───────▼────────┐
         │  Excel Export  │
         └────────────────┘
```

### 2.2 Component Responsibilities

#### 2.2.1 Document Loading Layer
**File:** `pdf_loader.py`
- **Responsibility:** PDF text extraction
- **Technology:** LangChain `PyPDFLoader`
- **Interface:** `load_pdf_text(path: str) -> str`
- **Design Decision:** Use LangChain DocumentLoader for consistency with framework

#### 2.2.2 Parsing Layer
**File:** `parser.py`
- **Responsibility:** AI-powered invoice parsing with schema enforcement
- **Technology:** 
  - LangChain `ChatAnthropic` (Claude)
  - Pydantic `BaseModel` for schema
  - `with_structured_output()` for enforcement
- **Interface:** `parse_invoice_from_text(text: str, ...) -> Invoice`
- **Design Decision:** Use structured output parser instead of prompt-based JSON extraction

#### 2.2.3 Schema Layer
**File:** `schema.py`
- **Responsibility:** Data model definitions
- **Technology:** Pydantic `BaseModel`
- **Models:**
  - `Invoice`: Main invoice model
  - `LineItem`: Invoice line items
- **Design Decision:** Separate schema file for reusability and validation

#### 2.2.4 Memory Management Layer
**File:** `memory_bank.py`
- **Responsibility:** Persistent memory and learning
- **Features:**
  - Processed files tracking
  - Vendor learning (flagging problematic vendors)
  - Statistics aggregation
  - Run configuration tracking
- **Interface:** `MemoryBank` class
- **Design Decision:** JSON-based persistence for simplicity and human readability

#### 2.2.5 Processing Orchestration
**File:** `main.py`
- **Responsibility:** Main processing logic and coordination
- **Functions:**
  - `process_files()`: Core processing logic
  - `main()`: CLI entry point
- **Design Decision:** Separate processing logic from entry point for testability

#### 2.2.6 User Interface
**File:** `ui.py`
- **Responsibility:** Graphical user interface
- **Technology:** tkinter
- **Features:**
  - File selection
  - Progress tracking
  - Results display
  - Memory bank statistics
- **Design Decision:** Separate UI module to keep CLI code clean

#### 2.2.7 Mock Data
**File:** `mock_data.py`
- **Responsibility:** Generate mock invoice data for testing
- **Use Case:** Development without LLM API calls
- **Design Decision:** Realistic mock data with all required fields

## 3. Data Flow

### 3.1 Processing Flow

```
1. File Discovery
   └─> glob("pdf/*.pdf")

2. For each PDF:
   ├─> Check Memory Bank (skip if already processed)
   ├─> Load PDF text (PyPDFLoader)
   ├─> Parse with LLM (with structured output)
   ├─> Apply vendor policy (memory-based learning)
   ├─> Expand line items to separate rows
   ├─> Record result in Memory Bank
   └─> Handle errors gracefully

3. Export
   └─> pandas DataFrame -> Excel (openpyxl)
```

### 3.2 Memory Bank Integration

```
Parse Invoice
    │
    ├─> Check if vendor flagged
    │   └─> If yes: Add context to LLM prompt
    │
    ├─> Apply vendor policy
    │   └─> If vendor flagged: Mark as NEEDS_REVIEW
    │
    └─> Record result
        ├─> Update statistics
        ├─> Flag vendor if error/review
        └─> Save to JSON
```

## 4. Design Patterns

### 4.1 Separation of Concerns
- **Document Loading:** Isolated in `pdf_loader.py`
- **Parsing Logic:** Isolated in `parser.py`
- **Memory Management:** Isolated in `memory_bank.py`
- **UI Logic:** Isolated in `ui.py`
- **Business Logic:** In `main.py`

### 4.2 Memory Integration Pattern
- Memory Bank provides context to LLM chain
- Vendor learning influences future processing
- Demonstrates "memory within chain" requirement

### 4.3 Error Handling Strategy
- Try-catch around each file processing
- Continue processing remaining files on error
- Record errors in Memory Bank for analysis

## 5. Technology Stack

### 5.1 Core Libraries
- **LangChain:** Framework for LLM integration
  - `langchain_community.document_loaders.PyPDFLoader`
  - `langchain_anthropic.ChatAnthropic`
  - `langchain_core.prompts.ChatPromptTemplate`
- **Pydantic:** Schema validation and structured output
- **pandas:** Data manipulation and Excel export
- **openpyxl:** Excel file generation
- **tkinter:** GUI framework (built-in)

### 5.2 Design Principles
- **Schema Enforcement:** Mandatory Pydantic validation
- **Memory Integration:** Context-aware processing
- **Modularity:** Each component in separate file
- **Testability:** Mock data for development

## 6. File Structure

```
project/
├── main.py              # Entry point and orchestration
├── pdf_loader.py        # PDF text extraction
├── parser.py            # LLM-based parsing
├── schema.py            # Pydantic models
├── memory_bank.py       # Persistent memory management
├── ui.py                # Graphical interface
├── mock_data.py         # Mock data generator
├── requirements.txt     # Dependencies
├── SPEC.bmad            # BMAD specification
└── pdf/                 # Input PDF files
```

## 7. Key Design Decisions

### 7.1 Why Structured Output Parser?
- **Requirement:** Must enforce schema, not rely on "nice prompts"
- **Solution:** `with_structured_output(Invoice)` ensures type-safe output
- **Benefit:** Guaranteed schema compliance

### 7.2 Why Memory Bank?
- **Requirement:** Advanced memory management within Agent/Chain
- **Solution:** Persistent JSON-based memory with vendor learning
- **Benefit:** System learns from past errors and improves over time

### 7.3 Why Separate UI?
- **Requirement:** User-friendly interface
- **Solution:** tkinter-based GUI with file selection
- **Benefit:** Non-technical users can process invoices easily

### 7.4 Why Excel Export?
- **Requirement:** Export to Excel using pandas
- **Solution:** `df.to_excel()` with openpyxl engine
- **Benefit:** Structured data in familiar format

## 8. Processing Logic

### 8.1 Line Items Expansion
Each invoice line item becomes a separate row in output:
- Same invoice metadata (vendor, date, number, currency, bill_to)
- Different line item data (description, quantity, rate, amount)

### 8.2 Memory Context Integration
When vendor is flagged:
1. First parse to get vendor name
2. Check Memory Bank for vendor history
3. If flagged, re-parse with vendor context in prompt
4. Demonstrates memory influencing chain behavior

## 9. Error Handling

### 9.1 File-Level Errors
- Catch exceptions per file
- Continue processing remaining files
- Record error in Memory Bank
- Display error message to user

### 9.2 LLM Errors
- Handle API failures gracefully
- Record error status
- Continue with next file

## 10. Testing Strategy

### 10.1 Mock Mode
- `USE_LLM=false` uses mock data
- Allows development without API costs
- Realistic data structure for testing

### 10.2 Memory Bank Testing
- Test vendor flagging logic
- Test skip logic for processed files
- Test statistics aggregation