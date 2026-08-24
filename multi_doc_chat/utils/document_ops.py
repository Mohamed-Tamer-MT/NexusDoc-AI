from __future__ import annotations
from pathlib import Path
from typing import Iterable, List
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from multi_doc_chat.logger import GLOBAL_LOGGER as log
from multi_doc_chat.exception.custom_exception import DocumentPortalException
from fastapi import UploadFile

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# Map of extension -> factory building the appropriate loader.
LoaderFactory = (
    object  # noqa: E501 placeholder; each branch builds its own loader below.
)


def load_documents(paths: Iterable[Path]) -> List[Document]:
    """Load docs using appropriate loader based on extension."""
    docs: List[Document] = []
    try:
        for p in paths:
            ext = p.suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                log.warning("Unsupported extension skipped", path=str(p))
                continue
            if ext == ".pdf":
                loader = PyPDFLoader(str(p))
            elif ext == ".docx":
                loader = Docx2txtLoader(str(p))
            else:  # ".txt"
                loader = TextLoader(str(p), encoding="utf-8")
            docs.extend(loader.load())
        log.info("Documents loaded", count=len(docs))
        return docs
    except Exception as e:
        log.error("Failed loading documents", error=str(e))
        raise DocumentPortalException("Error loading documents", e) from e


class FastAPIFileAdapter:
    """Adapt FastAPI UploadFile to a simple object with .name and .getbuffer()."""

    def __init__(self, uf: UploadFile):
        self._uf = uf
        self.name = uf.filename or "file"

    def getbuffer(self) -> bytes:
        self._uf.file.seek(0)
        return self._uf.file.read()
