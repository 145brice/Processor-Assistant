"""
Guidelines Engine for Processor Traien
Indexes and searches Fannie Mae / Freddie Mac selling guides locally.
Builds a searchable index on first run, then searches from cache.
100% offline.
"""

import os
import re
import json
import time
import hashlib
from pathlib import Path
from pypdf import PdfReader

try:
    from thefuzz import fuzz
    _HAS_FUZZ = True
except ImportError:
    _HAS_FUZZ = False

# Where to store the index cache
_INDEX_DIR = os.path.join(os.path.dirname(__file__), "guidelines_index")

# Default guideline PDF locations
DEFAULT_GUIDELINES = {
    "Fannie Mae": os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", "Fannie Mae.pdf"),
    "Freddie Mac": os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", "Freddie Mac.pdf"),
}

# Mortgage topic keywords mapped to common condition types
# Used to boost relevance when searching guidelines
_TOPIC_MAP = {
    "appraisal": ["appraisal", "appraised value", "comparable", "1004", "subject property", "market value"],
    "credit": ["credit", "fico", "credit score", "tradeline", "derogatory", "collection", "dispute", "charge-off", "bankruptcy"],
    "employment": ["employment", "voe", "verification of employment", "employer", "income", "pay stub", "w-2", "self-employed"],
    "assets": ["asset", "bank statement", "reserves", "gift", "deposit", "earnest money", "funds", "savings", "checking"],
    "title": ["title", "lien", "title commitment", "title policy", "deed", "vesting", "easement", "encumbrance", "payoff"],
    "insurance": ["insurance", "hazard", "homeowner", "flood", "wind", "hoi", "binder", "mortgagee clause", "coverage"],
    "income": ["income", "salary", "wages", "rental income", "schedule e", "1099", "commission", "bonus", "overtime"],
    "dti": ["dti", "debt-to-income", "debt to income", "qualifying ratio", "housing ratio", "front end", "back end"],
    "ltv": ["ltv", "loan-to-value", "loan to value", "cltv", "combined", "down payment"],
    "property": ["property", "condo", "pud", "manufactured", "modular", "multi-unit", "investment", "second home", "occupancy"],
    "hoa": ["hoa", "homeowner association", "condo association", "estoppel", "dues", "assessment", "condo project"],
    "closing": ["closing", "settlement", "closing disclosure", "cd", "clear to close", "ctc", "funding", "disbursement"],
    "tax": ["tax", "tax return", "1040", "4506", "transcript", "property tax", "tax roll", "tax certification"],
    "llc": ["llc", "entity", "corporation", "trust", "vesting", "good standing", "certificate", "operating agreement"],
    "mortgage": ["mortgage", "vom", "verification of mortgage", "payment history", "housing history", "rent verification"],
    "debt": ["debt", "undisclosed", "acknowledgment", "liability", "obligation", "payoff", "collection"],
    "investor": ["investor", "dscr", "rental", "investment property", "non-owner", "lease"],
    "fee": ["fee", "cpl", "closing protection", "e&o", "wire", "settlement", "prelim cd"],
}


def _get_file_hash(filepath: str) -> str:
    """Get a hash of file size + mod time for cache invalidation."""
    stat = os.stat(filepath)
    return hashlib.md5(f"{stat.st_size}_{stat.st_mtime}".encode()).hexdigest()[:12]


def _chunk_text(text: str, page_num: int, source: str, chunk_size: int = 1500) -> list:
    """
    Split a page's text into overlapping chunks for better search.
    Each chunk is ~1500 chars with 200 char overlap.
    """
    chunks = []
    if len(text) < chunk_size:
        if text.strip():
            chunks.append({
                "text": text.strip(),
                "page": page_num,
                "source": source,
            })
        return chunks

    stride = chunk_size - 200  # 200 char overlap
    for start in range(0, len(text), stride):
        segment = text[start:start + chunk_size].strip()
        if len(segment) < 50:
            continue
        chunks.append({
            "text": segment,
            "page": page_num,
            "source": source,
        })
    return chunks


def _detect_section(text: str) -> str:
    """Try to detect a section/chapter header from chunk text."""
    # Fannie Mae sections: "B3-3.1-01", "B5-6-02", etc.
    m = re.search(r'([A-Z]\d[\-\.]\d[\-\.]\d{1,2}[\-\.]\d{2})', text[:200])
    if m:
        return m.group(1)
    # Freddie Mac chapters: "Chapter 5501", "Section 4201.16"
    m = re.search(r'(?:Chapter|Section)\s+(\d{4}(?:\.\d+)?)', text[:200])
    if m:
        return m.group(0)
    return ""


def build_index(pdf_path: str, source_name: str, progress_callback=None) -> list:
    """
    Build a searchable index from a guideline PDF.
    Returns list of chunk dicts. Caches to disk as JSON.
    """
    os.makedirs(_INDEX_DIR, exist_ok=True)
    cache_file = os.path.join(_INDEX_DIR, f"{source_name.replace(' ', '_')}.json")
    hash_file = os.path.join(_INDEX_DIR, f"{source_name.replace(' ', '_')}.hash")

    # Check cache
    current_hash = _get_file_hash(pdf_path)
    if os.path.exists(cache_file) and os.path.exists(hash_file):
        with open(hash_file, 'r') as f:
            cached_hash = f.read().strip()
        if cached_hash == current_hash:
            if progress_callback:
                progress_callback(100, f"{source_name} index loaded from cache")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)

    # Build fresh index
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    chunks = []

    for i, page in enumerate(reader.pages):
        if progress_callback and i % 20 == 0:
            pct = int((i / total_pages) * 100)
            progress_callback(pct, f"Indexing {source_name} page {i+1}/{total_pages}...")

        text = page.extract_text() or ""
        if len(text.strip()) < 30:
            continue

        page_chunks = _chunk_text(text, i + 1, source_name)
        for chunk in page_chunks:
            chunk["section"] = _detect_section(chunk["text"])
        chunks.extend(page_chunks)

        # Pause every 50 pages to stay light
        if i % 50 == 0:
            time.sleep(0.1)

    # Save cache
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(chunks, f)
    with open(hash_file, 'w') as f:
        f.write(current_hash)

    if progress_callback:
        progress_callback(100, f"{source_name}: {len(chunks)} sections indexed")

    return chunks


def _detect_topics(condition_desc: str) -> list:
    """Detect which mortgage topics a condition relates to."""
    desc_lower = condition_desc.lower()
    topics = []
    for topic, keywords in _TOPIC_MAP.items():
        for kw in keywords:
            if kw in desc_lower:
                topics.append(topic)
                break
    return topics if topics else ["general"]


def _is_toc_or_junk(chunk_text: str) -> bool:
    """Return True if this chunk is a table of contents, index, or boilerplate."""
    t = chunk_text.strip()
    # TOC pages have lots of dot leaders (".......") and page numbers
    dot_count = t.count('...')
    if dot_count > 5:
        return True
    # Copyright / preface / boilerplate
    if re.search(r'(?i)(?:copyright|preface|table of contents|no part of this publication)', t[:200]):
        return True
    # Pages that are mostly section references with no real content
    lines = t.split('\n')
    ref_lines = sum(1 for l in lines if re.match(r'^\s*[A-Z]\d[\-\.]|^\s*Chapter\s+\d|^\s*Section\s+\d', l.strip()))
    if len(lines) > 3 and ref_lines / len(lines) > 0.5:
        return True
    return False


def _score_chunk(chunk_text: str, search_terms: list, condition_lower: str) -> int:
    """Score a chunk against condition search terms. Penalizes TOC/junk pages."""
    if _is_toc_or_junk(chunk_text):
        return 0

    chunk_lower = chunk_text.lower()

    if _HAS_FUZZ:
        # Count how many distinct search terms actually appear in the chunk
        term_hits = 0
        term_scores = []
        for term in search_terms:
            if term in chunk_lower:
                term_hits += 1
                term_scores.append(100)
            else:
                s = fuzz.partial_ratio(term, chunk_lower)
                if s >= 70:
                    term_hits += 0.5
                term_scores.append(s)

        if not term_scores:
            return 0

        # Require at least 2 meaningful term hits for a relevant result
        if term_hits < 1.5:
            return 0

        # Score = weighted combination of term coverage + fuzzy quality
        avg_score = sum(term_scores) / len(term_scores)
        coverage_bonus = min(30, int(term_hits * 8))
        full_match = fuzz.token_set_ratio(condition_lower, chunk_lower)

        final = int(avg_score * 0.4 + full_match * 0.3 + coverage_bonus)
        return min(100, final)
    else:
        # Simple keyword counting
        hits = sum(1 for t in search_terms if t in chunk_lower)
        if hits < 2:
            return 0
        return min(100, int((hits / max(len(search_terms), 1)) * 100))


def search_guidelines(condition_desc: str, index: list, top_n: int = 5,
                       threshold: int = 55) -> list:
    """
    Search the guideline index for sections relevant to a condition.

    Returns list of dicts with: source, section, page, score, excerpt.
    """
    desc_lower = condition_desc.lower()

    # Build search terms from condition + related topic keywords
    topics = _detect_topics(condition_desc)
    search_terms = []

    # Add condition words (filtered)
    stop = {"a", "an", "the", "of", "to", "for", "is", "are", "be", "in",
            "on", "and", "or", "not", "by", "at", "from", "with", "that",
            "this", "all", "has", "have", "provide", "submit", "obtain",
            "must", "shall", "should", "copy", "document", "acceptable",
            "needed", "required", "please", "including", "within", "prior"}
    for word in re.sub(r'[^\w\s]', ' ', desc_lower).split():
        if len(word) >= 3 and word not in stop:
            search_terms.append(word)

    # Add topic-specific terms for broader coverage
    for topic in topics:
        for kw in _TOPIC_MAP.get(topic, []):
            if kw not in search_terms:
                search_terms.append(kw)

    # Score all chunks
    scored = []
    for chunk in index:
        score = _score_chunk(chunk["text"], search_terms, desc_lower)
        if score >= threshold:
            scored.append((score, chunk))

    # Sort by score, take top N
    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    seen_pages = set()
    for score, chunk in scored:
        # Deduplicate by page (don't show 5 chunks from same page)
        page_key = f"{chunk['source']}_{chunk['page']}"
        if page_key in seen_pages:
            continue
        seen_pages.add(page_key)

        # Build a clean excerpt
        excerpt = chunk["text"][:600].strip()
        # Try to cut at a sentence boundary
        last_period = excerpt.rfind('.')
        if last_period > 200:
            excerpt = excerpt[:last_period + 1]

        results.append({
            "source": chunk["source"],
            "section": chunk.get("section", ""),
            "page": chunk["page"],
            "score": score,
            "excerpt": excerpt,
        })

        if len(results) >= top_n:
            break

    return results


def check_conditions_against_guidelines(selected_conditions: list,
                                         guideline_sources: list = None,
                                         progress_callback=None) -> dict:
    """
    Main function: check selected conditions against Fannie/Freddie guidelines.

    Args:
        selected_conditions: List of dicts with 'num' and 'desc'
        guideline_sources: List of ("Name", "path") tuples. Defaults to desktop PDFs.
        progress_callback: Optional callable(pct, msg)

    Returns:
        Dict keyed by condition num, each with 'desc' and 'guidelines' list.
    """
    if guideline_sources is None:
        guideline_sources = []
        for name, path in DEFAULT_GUIDELINES.items():
            if os.path.exists(path):
                guideline_sources.append((name, path))

    if not guideline_sources:
        return {"error": "No guideline PDFs found. Place 'Fannie Mae.pdf' and/or 'Freddie Mac.pdf' on your Desktop."}

    # Build/load indexes
    all_chunks = []
    for i, (name, path) in enumerate(guideline_sources):
        def _prog(pct, msg):
            if progress_callback:
                # Split progress across indexing (0-60%) and searching (60-100%)
                base = int((i / len(guideline_sources)) * 60)
                adjusted = base + int(pct * 0.6 / len(guideline_sources))
                progress_callback(min(adjusted, 60), msg)

        chunks = build_index(path, name, progress_callback=_prog)
        all_chunks.extend(chunks)

    if progress_callback:
        progress_callback(60, f"Index ready: {len(all_chunks)} sections. Searching...")

    # Search for each condition
    results = {}
    total_conds = len(selected_conditions)
    for ci, cond in enumerate(selected_conditions):
        if progress_callback:
            pct = 60 + int((ci / total_conds) * 40)
            progress_callback(pct, f"Checking condition #{cond['num']}...")

        matches = search_guidelines(cond["desc"], all_chunks, top_n=5, threshold=55)
        results[cond["num"]] = {
            "desc": cond["desc"],
            "guidelines": matches,
        }
        time.sleep(0.1)  # gentle pause

    if progress_callback:
        progress_callback(100, "Done!")

    return results


def get_available_guidelines() -> list:
    """Return list of guideline PDFs found on this machine."""
    found = []
    for name, path in DEFAULT_GUIDELINES.items():
        if os.path.exists(path):
            found.append({"name": name, "path": path, "indexed": _is_indexed(name)})
    return found


def _is_indexed(source_name: str) -> bool:
    """Check if a guideline has been indexed already."""
    cache_file = os.path.join(_INDEX_DIR, f"{source_name.replace(' ', '_')}.json")
    return os.path.exists(cache_file)
