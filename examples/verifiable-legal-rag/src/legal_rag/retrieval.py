"""BM25 retrieval plus a relevance gate that decides when to abstain."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .corpus import DEFAULT_DATA_DIR, Chunk

DEFAULT_GLOSSARY = DEFAULT_DATA_DIR / "glossary.json"

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_SECTION_REF_RE = re.compile(r"\b(section|rule|دفعہ|قاعدہ)\s*(\d+[a-z]?)\b", re.IGNORECASE)

STOPWORDS = frozenset(
    """
    a an and any are as at be by can could do does for from had has have how i if in into is it its
    me my of on or say says should tell than that the their them then there these this to under was
    what when where which who why will with would you your must may much many long after before about
    kya ka ki ke mein hai se ko par kitne kitni kitna sakta sakti milta milna hota batao bataen
    کیا کا کی کے میں ہے سے کو پر کتنے کتنی کتنا سکتا سکتی ہونا چاہیے دے ہیں ہو اپنا
    """.split()
)


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.casefold()) if t not in STOPWORDS]


def load_glossary(path: Path = DEFAULT_GLOSSARY) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    phrases = data["phrases"]
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in phrases.items()):
        raise ValueError("Glossary phrases must map strings to strings")
    return phrases


def expand_query(query: str, glossary: dict[str, str]) -> str:
    """Replace known Urdu/Roman Urdu phrases with English corpus terms.

    Longest phrases first, so "کرایہ دار" (tenant) wins over "کرایہ" (rent).
    """
    text = query.casefold()
    for phrase in sorted(glossary, key=len, reverse=True):
        pattern = r"(?<!\w)" + re.escape(phrase.casefold()) + r"(?!\w)"
        text = re.sub(pattern, f" {glossary[phrase]} ", text)
    return text


@dataclass(frozen=True)
class ScoredChunk:
    chunk: Chunk
    score: float
    coverage: float
    matched_terms: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalDecision:
    query_terms: tuple[str, ...]
    results: tuple[ScoredChunk, ...]
    abstain: bool
    reason: str
    referenced: tuple[str, ...] = field(default_factory=tuple)


class BM25Index:
    """Plain Okapi BM25. Lexical matching suits exact legal terms; it misses paraphrase."""

    def __init__(self, chunks: list[Chunk], *, k1: float = 1.5, b: float = 0.75):
        if not chunks:
            raise ValueError("Cannot index an empty corpus")
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.docs = [tokenize(f"{c.heading} {c.text}") for c in chunks]
        self.tf = [Counter(doc) for doc in self.docs]
        self.avg_len = sum(len(doc) for doc in self.docs) / len(self.docs)
        df: Counter[str] = Counter()
        for doc in self.docs:
            df.update(set(doc))
        n = len(self.docs)
        self.idf = {term: math.log((n - freq + 0.5) / (freq + 0.5) + 1) for term, freq in df.items()}
        # Unknown terms get the rarest possible IDF: they are informative, just absent.
        self.unknown_idf = math.log((n + 0.5) / 0.5 + 1)

    def term_idf(self, term: str) -> float:
        return self.idf.get(term, self.unknown_idf)

    def score(self, terms: list[str], index: int) -> float:
        tf = self.tf[index]
        length = len(self.docs[index])
        total = 0.0
        for term in terms:
            freq = tf.get(term, 0)
            if not freq:
                continue
            norm = freq + self.k1 * (1 - self.b + self.b * length / self.avg_len)
            total += self.idf[term] * freq * (self.k1 + 1) / norm
        return total

    def coverage(self, terms: list[str], index: int) -> tuple[float, tuple[str, ...]]:
        """IDF-weighted share of the query that this chunk actually contains."""
        unique = list(dict.fromkeys(terms))
        if not unique:
            return 0.0, ()
        present = self.tf[index]
        matched = tuple(t for t in unique if t in present)
        total = sum(self.term_idf(t) for t in unique)
        return sum(self.term_idf(t) for t in matched) / total, matched

    def search(self, terms: list[str], top_k: int = 3) -> list[ScoredChunk]:
        scored = []
        for i, chunk in enumerate(self.chunks):
            value = self.score(terms, i)
            if value <= 0:
                continue
            cov, matched = self.coverage(terms, i)
            scored.append(ScoredChunk(chunk, value, cov, matched))
        scored.sort(key=lambda s: (-s.score, s.chunk.chunk_id))
        return scored[:top_k]


class Retriever:
    def __init__(
        self,
        chunks: list[Chunk],
        glossary: dict[str, str] | None = None,
        *,
        top_k: int = 3,
        min_score: float = 1.5,
        min_coverage: float = 0.4,
    ):
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        if not 0 <= min_coverage <= 1:
            raise ValueError("min_coverage must be between 0 and 1")
        self.index = BM25Index(chunks)
        self.glossary = glossary or {}
        self.top_k = top_k
        self.min_score = min_score
        self.min_coverage = min_coverage

    def referenced_provisions(self, query: str) -> list[str]:
        refs = []
        for word, number in _SECTION_REF_RE.findall(query):
            kind = "s" if word.casefold() in {"section", "دفعہ"} else "r"
            refs.append(f"{kind}{number.upper()}")
        return refs

    def retrieve(self, query: str) -> RetrievalDecision:
        terms = tokenize(expand_query(query, self.glossary))
        refs = self.referenced_provisions(query)
        if refs:
            # An explicit provision number must exist; never answer "Section 12"
            # with whatever Section happens to be lexically closest.
            matches = [c for c in self.index.chunks if c.chunk_id.split("#")[1] in refs]
            if not matches:
                return RetrievalDecision(tuple(terms), (), True, "referenced_provision_not_in_corpus", tuple(refs))
            # A real provision was named: ground on it directly, ranked by lexical score.
            ranked = sorted(
                (ScoredChunk(c, self.index.score(terms, self.index.chunks.index(c)), 1.0, ()) for c in matches),
                key=lambda s: (-s.score, s.chunk.chunk_id),
            )
            return RetrievalDecision(tuple(terms), tuple(ranked[: self.top_k]), False, "explicit_reference", tuple(refs))
        if not terms:
            return RetrievalDecision((), (), True, "no_searchable_terms", tuple(refs))
        results = self.index.search(terms, self.top_k)
        if not results:
            return RetrievalDecision(tuple(terms), (), True, "no_lexical_match", tuple(refs))
        best = results[0]
        if best.score < self.min_score:
            return RetrievalDecision(tuple(terms), tuple(results), True, "score_below_threshold", tuple(refs))
        if best.coverage < self.min_coverage:
            return RetrievalDecision(tuple(terms), tuple(results), True, "query_not_covered", tuple(refs))
        return RetrievalDecision(tuple(terms), tuple(results), False, "grounded", tuple(refs))
