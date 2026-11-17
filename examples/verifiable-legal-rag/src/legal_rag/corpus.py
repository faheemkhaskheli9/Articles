"""Load statute-like text files as one chunk per section or rule."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PACKAGE_ROOT / "data"
DEFAULT_CORPUS_DIR = DEFAULT_DATA_DIR / "corpus"

_TITLE_RE = re.compile(r"^Title:\s*(.+)$")
_HEADING_RE = re.compile(r"^(Section|Rule)\s+(\d+[A-Z]?)\.\s+(.+)$")


@dataclass(frozen=True)
class Chunk:
    """One complete legal provision with a stable, citable identifier."""

    chunk_id: str
    document: str
    title: str
    kind: str
    number: str
    heading: str
    text: str

    @property
    def citation(self) -> str:
        return f"{self.title}, {self.kind} {self.number} ({self.heading})"


def parse_document(path: Path) -> list[Chunk]:
    """Split a document at provision headings; never split inside a provision."""
    lines = path.read_text(encoding="utf-8").splitlines()
    title = path.stem
    chunks: list[Chunk] = []
    current: tuple[str, str, str] | None = None
    body: list[str] = []
    seen: set[str] = set()

    def flush() -> None:
        if current is None:
            return
        kind, number, heading = current
        text = " ".join(line.strip() for line in body if line.strip())
        if not text:
            raise ValueError(f"{path.name}: {kind} {number} has no text")
        chunk_id = f"{path.stem}#{kind[0].lower()}{number}"
        if chunk_id in seen:
            raise ValueError(f"{path.name}: duplicate provision {kind} {number}")
        seen.add(chunk_id)
        chunks.append(Chunk(chunk_id, path.name, title, kind, number, heading.strip(), text))

    for line in lines:
        title_match = _TITLE_RE.match(line)
        if title_match and current is None:
            title = title_match.group(1).strip()
            continue
        heading_match = _HEADING_RE.match(line.strip())
        if heading_match:
            flush()
            current = (heading_match.group(1), heading_match.group(2), heading_match.group(3))
            body = []
        elif current is not None:
            body.append(line)
    flush()
    if not chunks:
        raise ValueError(f"{path.name}: no Section/Rule headings found")
    return chunks


def load_corpus(corpus_dir: Path = DEFAULT_CORPUS_DIR) -> list[Chunk]:
    paths = sorted(corpus_dir.glob("*.txt"))
    if not paths:
        raise FileNotFoundError(f"No .txt documents in {corpus_dir}")
    chunks: list[Chunk] = []
    for path in paths:
        chunks.extend(parse_document(path))
    return chunks
