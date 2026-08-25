from __future__ import annotations

import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from multi_doc_chat.exception.custom_exception import DocumentPortalException
from multi_doc_chat.logger import GLOBAL_LOGGER as log
from multi_doc_chat.utils.document_ops import load_documents
from multi_doc_chat.utils.file_io import save_uploaded_files
from multi_doc_chat.utils.model_loader import ModelLoader


def generate_session_id() -> str:
    """Return a unique session identifier in the format ``session_YYYYMMDD_HHMMSS_XXXXXXXX``."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]
    return f"session_{ts}_{short_uuid}"


class ChatIngestor:
    """Save uploads, chunk them, and persist a session-scoped FAISS index."""

    def __init__(
        self,
        temp_base: str = "data",
        faiss_base: str = "faiss_index",
        use_session_dirs: bool = True,
        session_id: Optional[str] = None,
    ):
        try:
            self.use_session_dirs = use_session_dirs
            self.session_id = session_id or uuid.uuid4().hex
            self.temp_base = Path(temp_base)
            self.faiss_base = Path(faiss_base)

            if use_session_dirs:
                self.temp_dir = self.temp_base / self.session_id
                self.faiss_dir = self.faiss_base / self.session_id
            else:
                self.temp_dir = self.temp_base
                self.faiss_dir = self.faiss_base

            self.temp_dir.mkdir(parents=True, exist_ok=True)
            self.faiss_dir.mkdir(parents=True, exist_ok=True)
            log.info("ChatIngestor initialized", session_id=self.session_id)
        except Exception as e:
            log.error("Failed to initialize ChatIngestor", error=str(e))
            raise DocumentPortalException("Initialization error in ChatIngestor", sys)

    def _split(
        self,
        docs: Sequence[Document],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> List[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        return splitter.split_documents(list(docs))

    def built_retriver(
        self,
        uploaded_files: Iterable[object],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        k: int = 5,
        search_type: str = "mmr",
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        index_name: str = "index",
    ):
        """Persist uploaded files and write a FAISS index for later chat retrieval.

        The method name matches the existing FastAPI and notebook call sites.
        """
        try:
            saved = save_uploaded_files(uploaded_files, self.temp_dir)
            if not saved:
                raise ValueError("No supported files were uploaded (PDF, DOCX, TXT)")

            docs = load_documents(saved)
            if not docs:
                raise ValueError("No documents could be loaded from the uploaded files")

            chunks = self._split(docs, chunk_size, chunk_overlap)
            embeddings = ModelLoader().load_embeddings()
            vectorstore = FAISS.from_documents(chunks, embeddings)
            vectorstore.save_local(str(self.faiss_dir), index_name=index_name)

            search_kwargs: Dict[str, Any] = {"k": k}
            if search_type == "mmr":
                search_kwargs["fetch_k"] = fetch_k
                search_kwargs["lambda_mult"] = lambda_mult

            log.info(
                "FAISS index built",
                session_id=self.session_id,
                chunks=len(chunks),
                search_type=search_type,
            )
            return vectorstore.as_retriever(
                search_type=search_type, search_kwargs=search_kwargs
            )
        except Exception as e:
            log.error(
                "Failed to build retriever",
                error=str(e),
                session_id=self.session_id,
            )
            raise DocumentPortalException("Error building retriever", sys)


class FaissManager:
    """Manage a FAISS vector store backed by a local directory."""

    def __init__(self, index_dir: Path):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self._vectorstore: Optional[FAISS] = None
        self._existing_contents: set[str] = set()

    def load_or_create(
        self,
        texts: Sequence[str],
        metadatas: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> None:
        embeddings = ModelLoader().load_embeddings()
        docs = [
            Document(page_content=t, metadata=m or {})
            for t, m in zip(texts, metadatas or [{}] * len(texts))
        ]
        if not docs:
            raise ValueError("At least one text is required to create an index")
        self._vectorstore = FAISS.from_documents(docs, embeddings)
        for doc in docs:
            self._existing_contents.add(doc.page_content)
        self._vectorstore.save_local(str(self.index_dir))
        log.info("FAISS index created", index_dir=str(self.index_dir), count=len(docs))

    def add_documents(self, docs: Sequence[Document]) -> int:
        if self._vectorstore is None:
            embeddings = ModelLoader().load_embeddings()
            if list(docs):
                self._vectorstore = FAISS.from_documents(list(docs), embeddings)
            else:
                self._vectorstore = FAISS.from_documents(
                    [Document(page_content="", metadata={})], embeddings
                )
            for doc in docs:
                self._existing_contents.add(doc.page_content)
            self._vectorstore.save_local(str(self.index_dir))
            return len(docs)

        new_docs = [
            doc for doc in docs if doc.page_content not in self._existing_contents
        ]
        if not new_docs:
            return 0
        self._vectorstore.add_documents(new_docs)
        for doc in new_docs:
            self._existing_contents.add(doc.page_content)
        self._vectorstore.save_local(str(self.index_dir))
        log.info("Documents added to FAISS", count=len(new_docs))
        return len(new_docs)
