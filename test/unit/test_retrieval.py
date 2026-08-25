import pathlib

import pytest
from exception.custom_exception import DocumentPortalException

from multi_doc_chat.src.document_chat.retrieval import ConversationalRAG


def test_conversationalrag_error_handling(tmp_dirs, stub_model_loader):
    rag = ConversationalRAG(session_id="s1")
    with pytest.raises(DocumentPortalException):
        rag.invoke("hello")
    with pytest.raises(DocumentPortalException):
        rag.load_retriever_from_faiss(index_path="faiss_index/does_not_exist")
