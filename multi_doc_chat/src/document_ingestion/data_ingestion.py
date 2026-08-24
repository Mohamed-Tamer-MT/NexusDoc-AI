from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from multi_doc_chat.exception.custom_exception import DocumentPortalException
from multi_doc_chat.logger import GLOBAL_LOGGER as log
from multi_doc_chat.utils.document_ops import load_documents
from multi_doc_chat.utils.file_io import save_uploaded_files
from multi_doc_chat.utils.model_loader import ModelLoader


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

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
            chunks = splitter.split_documents(docs)
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
