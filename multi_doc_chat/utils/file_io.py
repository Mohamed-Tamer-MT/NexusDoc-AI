from __future__ import annotations
import re
import uuid
from pathlib import Path
from typing import Iterable, List
from multi_doc_chat.logger.cutom_logger import CustomLogger
from multi_doc_chat.exception.custom_exception import DocumentPortalException

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".pptx",
    ".md",
    ".csv",
    ".xlsx",
    ".xls",
    ".db",
    ".sqlite",
    ".sqlite3",
}

# Local logger instance
log = CustomLogger().get_logger(__name__)


def _as_bytes(data: object) -> bytes:
    """Validate binary content before passing it to a binary file handle."""
    if isinstance(data, bytes):
        return data
    if isinstance(data, bytearray):
        return bytes(data)
    if isinstance(data, memoryview):
        return data.tobytes()
    raise TypeError("Uploaded file content must be bytes-like")


def _read_bytes(source: object) -> bytes:
    """Read and validate binary content from an uploaded-file-like object."""
    reader = getattr(source, "read", None)
    if not callable(reader):
        raise ValueError("Unsupported uploaded file object; no readable interface")
    return _as_bytes(reader())


def save_uploaded_files(uploaded_files: Iterable[object], target_dir: Path) -> List[Path]:
    """Save uploaded files (Streamlit-like) and return local paths."""
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        saved: List[Path] = []
        for uf in uploaded_files:
            # Handle Starlette UploadFile (has .filename and .file) and generic objects (have .name)
            raw_name: object = getattr(uf, "filename", getattr(uf, "name", "file"))
            name = raw_name if isinstance(raw_name, str) else "file"
            ext = Path(name).suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                log.warning("Unsupported file skipped", filename=name)
                continue
            # Clean file name (only alphanum, dash, underscore)
            safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", Path(name).stem).lower()
            fname = f"{safe_name}_{uuid.uuid4().hex[:6]}{ext}"
            fname = f"{uuid.uuid4().hex[:8]}{ext}"
            out = target_dir / fname
            with open(out, "wb") as f:
                # Prefer underlying file buffer when available (e.g., Starlette UploadFile.file)
                file_buffer = getattr(uf, "file", None)
                if callable(getattr(file_buffer, "read", None)):
                    f.write(_read_bytes(file_buffer))
                elif callable(getattr(uf, "read", None)):
                    f.write(_read_bytes(uf))
                else:
                    # Fallback for objects exposing a getbuffer()
                    buf = getattr(uf, "getbuffer", None)
                    if callable(buf):
                        f.write(_as_bytes(buf()))
                    else:
                        raise ValueError(
                            "Unsupported uploaded file object; no readable interface"
                        )
            saved.append(out)
            log.info("File saved for ingestion", uploaded=name, saved_as=str(out))
        return saved
    except Exception as e:
        log.error("Failed to save uploaded files", error=str(e), dir=str(target_dir))
        raise DocumentPortalException("Failed to save uploaded files", e) from e
