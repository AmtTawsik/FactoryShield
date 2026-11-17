"""Turns document files into chunks for the knowledge base: text extraction, splitting and the manifest."""

import logging
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.modules.auth.service import FactoryScope
from app.modules.knowledge.schemas import IngestResult, KnowledgeDocumentCreate
from app.modules.knowledge.service import KnowledgeService

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = (".pdf", ".txt", ".md")
# multilingual-e5-small reads at most 512 tokens. Bangla text uses roughly one token per two to three
# characters, so 900 characters keeps a chunk inside that limit with room to spare.
MAX_CHUNK_CHARS = 900
UNREADABLE_CHARACTER = "�"

_SENTENCE_END = re.compile(r"(?<=[.!?।৷;])\s+")
_MARKDOWN_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*$")
_PAGE_NUMBER = re.compile(r"^\s*\d{1,4}\s*$")


class IngestionError(Exception):
    """A document file or manifest entry that cannot be loaded."""


@dataclass(frozen=True)
class ExtractedText:
    text: str
    unreadable_characters: int = 0


@dataclass(frozen=True)
class ManifestEntry:
    path: Path
    document: KnowledgeDocumentCreate


@dataclass(frozen=True)
class PreparedDocument:
    entry: ManifestEntry
    chunks: list[str]
    unreadable_characters: int


def extract_text(path: Path) -> ExtractedText:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise IngestionError(f"{path.name}: unsupported file type (supported: {', '.join(SUPPORTED_EXTENSIONS)})")
    if not path.is_file():
        raise IngestionError(f"{path}: file not found")
    if suffix == ".pdf":
        return _extract_pdf(path)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IngestionError(f"{path.name}: text files must be UTF-8") from exc
    return ExtractedText(text.replace("\r\n", "\n"))


def _extract_pdf(path: Path) -> ExtractedText:
    try:
        pages = [page.extract_text() or "" for page in PdfReader(path).pages]
    except (PdfReadError, OSError) as exc:
        raise IngestionError(f"{path.name}: the PDF could not be read") from exc

    lines = [line.rstrip() for page in pages for line in page.splitlines() if not _PAGE_NUMBER.match(line)]
    # PDF lines are layout, not paragraphs: join them, rejoining words hyphenated across a line break.
    text = ""
    for line in lines:
        if text.endswith("-") and line[:1].islower():
            text = text[:-1] + line.lstrip()
        else:
            text = f"{text} {line.strip()}" if text else line.strip()
    # Glyphs without a Unicode mapping come out as U+FFFD. A space keeps the words around them apart.
    unreadable = text.count(UNREADABLE_CHARACTER)
    text = re.sub(r"[ \t]+", " ", text.replace(UNREADABLE_CHARACTER, " ")).strip()
    if not text:
        raise IngestionError(f"{path.name}: the PDF has no extractable text (scanned PDFs are not supported)")
    return ExtractedText(text, unreadable)


def split_into_chunks(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Splits text into chunks along headings, paragraphs and sentences, in that order of preference.

    Markdown headings start a new chunk and are repeated at the top of every chunk of their section,
    so each chunk still says what it is about when read on its own.
    """
    chunks: list[str] = []
    heading = ""
    body: list[str] = []

    def flush() -> None:
        if body:
            chunks.append("\n".join([heading, *body]) if heading else "\n".join(body))
            body.clear()

    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n")):
        block = block.strip()
        if not block:
            continue
        first_line, _, rest = block.partition("\n")
        if match := _MARKDOWN_HEADING.match(first_line):
            flush()
            heading = match.group(1)
            block = rest.strip()
            if not block:
                continue
        room = max_chars - len(heading) - 1 if heading else max_chars
        for piece in _pieces(" ".join(block.split()), room):
            if body and len("\n".join([*body, piece])) > room:
                flush()
            body.append(piece)
    flush()
    return chunks


def _pieces(paragraph: str, limit: int) -> list[str]:
    """The paragraph itself if it fits, otherwise sentence groups (or word groups) of at most `limit`."""
    if len(paragraph) <= limit:
        return [paragraph]
    pieces: list[str] = []
    current = ""
    for sentence in _SENTENCE_END.split(paragraph):
        for part in _words_within(sentence, limit):
            if current and len(current) + 1 + len(part) > limit:
                pieces.append(current)
                current = part
            else:
                current = f"{current} {part}" if current else part
    if current:
        pieces.append(current)
    return pieces


def _words_within(sentence: str, limit: int) -> list[str]:
    if len(sentence) <= limit:
        return [sentence]
    parts: list[str] = []
    current = ""
    for word in sentence.split():
        if current and len(current) + 1 + len(word) > limit:
            parts.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        parts.append(current)
    return parts


def load_manifest(path: Path) -> list[ManifestEntry]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise IngestionError(f"{path}: manifest not found") from exc
    except tomllib.TOMLDecodeError as exc:
        raise IngestionError(f"{path}: invalid TOML ({exc})") from exc

    items = data.get("documents")
    if not isinstance(items, list) or not items:
        raise IngestionError(f"{path}: add at least one [[documents]] entry")
    entries: list[ManifestEntry] = []
    keys: set[str] = set()
    for number, item in enumerate(items, start=1):
        fields = dict(item)
        file = fields.pop("file", None)
        key = fields.pop("key", None)
        if not file:
            raise IngestionError(f"{path}: document {number} has no 'file'")
        try:
            document = KnowledgeDocumentCreate(source_key=key, **fields)
        except ValidationError as exc:
            problems = "; ".join(
                f"{'.'.join(map(str, error['loc'])) or 'document'}: {error['msg']}" for error in exc.errors()
            )
            raise IngestionError(f"{path}: document {number} ({file}) is invalid: {problems}") from exc
        if document.source_key in keys:
            raise IngestionError(f"{path}: key '{document.source_key}' is used more than once")
        keys.add(document.source_key)
        entries.append(ManifestEntry(path=(path.parent / file).resolve(), document=document))
    return entries


def prepare(entries: list[ManifestEntry]) -> list[PreparedDocument]:
    """Reads and splits every file before anything is embedded, so a bad file stops the run early."""
    prepared = []
    for entry in entries:
        extracted = extract_text(entry.path)
        chunks = split_into_chunks(extracted.text)
        if not chunks:
            raise IngestionError(f"{entry.path.name}: no text found")
        prepared.append(PreparedDocument(entry, chunks, extracted.unreadable_characters))
    return prepared


async def ingest_prepared(
    documents: list[PreparedDocument], service: KnowledgeService, scope: FactoryScope
) -> list[IngestResult]:
    return [await service.ingest(item.entry.document, item.chunks, scope) for item in documents]
