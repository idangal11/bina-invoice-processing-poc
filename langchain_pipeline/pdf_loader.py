from langchain_community.document_loaders import PyPDFLoader


def load_pdf_text(path: str) -> str:
    """Load and extract text from PDF file."""
    try:
        loader = PyPDFLoader(path)
        docs = loader.load()
        return "\n".join(d.page_content for d in docs)
    except Exception as e:
        raise RuntimeError(f"Failed to load PDF {path}: {e}") from e
