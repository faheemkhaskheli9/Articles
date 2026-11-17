import pytest

from legal_rag.pipeline import LegalRAG


@pytest.fixture(scope="session")
def rag() -> LegalRAG:
    return LegalRAG.from_files()
