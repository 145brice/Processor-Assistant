"""
Folder Search Engine for Processor Traien
Searches a local folder for documents matching mortgage conditions.
100% offline - fuzzy matches filenames and PDF content.
"""

import os
import re
import time
from pathlib import Path
from pypdf import PdfReader
import io

# --- Fuzzy matching (pure Python fallback if thefuzz not installed) ---
try:
    from thefuzz import fuzz
    _HAS_FUZZ = True
except ImportError:
    _HAS_FUZZ = False


# Common words to ignore when building search keywords
_STOP_WORDS = {
    "a", "an", "the", "of", "to", "for", "is", "are", "be", "in", "on",
    "and", "or", "not", "by", "at", "from", "with", "that", "this", "it",
    "all", "has", "have", "had", "been", "was", "were", "will", "can",
    "must", "shall", "should", "may", "if", "no", "any", "each", "per",
    "provide", "submit", "obtain", "supply", "deliver", "furnish", "copy",
    "document", "documentation", "acceptable", "required", "needed",
    "please", "including", "within", "prior", "most", "recent",
}

# Known mortgage document terms (multi-word) for better matching
_MORTGAGE_TERMS = [
    "bank statement", "pay stub", "pay stubs", "tax return", "tax returns",
    "credit report", "credit supplement", "w-2", "w2", "1003", "1040",
    "4506", "gift letter", "hazard insurance", "flood cert", "flood certificate",
    "flood zone", "title commitment", "title policy", "appraisal",
    "voe", "verification of employment", "vom", "verification of mortgage",
    "vor", "verification of rent", "vod", "verification of deposit",
    "hoa", "estoppel", "condo questionnaire", "good standing",
    "certificate of good standing", "settlement", "closing disclosure",
    "loan estimate", "earnest money", "purchase agreement", "sales contract",
    "deed of trust", "promissory note", "insurance binder", "declarations page",
    "cpl", "e&o", "wire instruction", "prelim cd", "preliminary cd",
    "debt acknowledgment", "property tax", "tax roll", "tax cert",
    "lien", "payoff", "mortgage payment", "rental property",
]


def extract_keywords(condition_desc: str) -> dict:
    """
    Extract search terms from a condition description.
    Returns dict with 'words' (individual keywords) and 'phrases' (multi-word terms found).
    """
    text = condition_desc.lower()
    # Remove punctuation except hyphens
    text_clean = re.sub(r'[^\w\s\-/]', ' ', text)

    # Find multi-word mortgage terms in the description
    phrases = []
    for term in _MORTGAGE_TERMS:
        if term in text:
            phrases.append(term)

    # Extract individual meaningful words
    words = []
    for w in text_clean.split():
        w = w.strip('-/')
        if len(w) < 3:
            continue
        if w in _STOP_WORDS:
            continue
        if re.match(r'^\d+$', w):
            continue
        words.append(w)

    return {"words": words, "phrases": phrases, "full": condition_desc.lower()}


def match_score(keywords: dict, target_text: str) -> int:
    """
    Compute fuzzy match score (0-100) between condition keywords and target text.
    Works with or without thefuzz library.
    """
    if not target_text or not target_text.strip():
        return 0

    target = target_text.lower()

    if _HAS_FUZZ:
        scores = []

        # Score multi-word phrases (highest weight)
        for phrase in keywords.get("phrases", []):
            s = fuzz.partial_ratio(phrase, target)
            scores.append(s * 1.2)  # boost phrase matches

        # Score individual keywords
        word_scores = []
        for word in keywords.get("words", []):
            s = fuzz.partial_ratio(word, target)
            word_scores.append(s)

        if word_scores:
            # Average of top keyword scores
            word_scores.sort(reverse=True)
            top_n = word_scores[:min(5, len(word_scores))]
            scores.append(sum(top_n) / len(top_n))

        # Full description token match
        full = keywords.get("full", "")
        if full:
            scores.append(fuzz.token_set_ratio(full, target) * 0.8)

        return min(100, int(max(scores))) if scores else 0

    else:
        # Simple fallback: count keyword hits
        hit_count = 0
        total = len(keywords.get("words", [])) + len(keywords.get("phrases", []))
        if total == 0:
            return 0

        for phrase in keywords.get("phrases", []):
            if phrase in target:
                hit_count += 2  # phrases worth more

        for word in keywords.get("words", []):
            if word in target:
                hit_count += 1

        return min(100, int((hit_count / max(total, 1)) * 100))


def extract_matching_pages(pdf_path: str, keywords: dict, threshold: int = 60) -> list:
    """
    Read a PDF page by page, return pages that match above threshold.
    Returns list of {"page": int, "score": int, "snippet": str}.
    """
    matches = []
    try:
        reader = PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if len(text.strip()) < 10:
                continue
            score = match_score(keywords, text)
            if score >= threshold:
                # Grab a snippet around the best matching keyword
                snippet = _get_snippet(text, keywords)
                matches.append({
                    "page": i + 1,
                    "score": score,
                    "snippet": snippet,
                })
            time.sleep(0.03)  # gentle per-page pause
    except Exception:
        pass  # unreadable PDF, skip
    return matches


def _get_snippet(text: str, keywords: dict, context_chars: int = 120) -> str:
    """Extract a short snippet around the first keyword match."""
    target = text.lower()
    # Try phrases first, then words
    search_terms = keywords.get("phrases", []) + keywords.get("words", [])
    for term in search_terms:
        idx = target.find(term)
        if idx >= 0:
            start = max(0, idx - 40)
            end = min(len(text), idx + len(term) + context_chars)
            snippet = text[start:end].replace('\n', ' ').strip()
            if start > 0:
                snippet = "..." + snippet
            if end < len(text):
                snippet = snippet + "..."
            return snippet
    # Fallback: first N chars
    return text[:context_chars].replace('\n', ' ').strip() + "..."


# Supported file extensions
_PDF_EXTS = {'.pdf'}
_TEXT_EXTS = {'.txt', '.csv'}
_SKIP_EXTS = {'.exe', '.dll', '.zip', '.rar', '.7z', '.db', '.sqlite', '.pyc'}
MAX_FILES = 500
MAX_FILE_SIZE_MB = 50


def scan_folder(folder_path: str, selected_conditions: list, threshold: int = 60,
                progress_callback=None) -> dict:
    """
    Scan a folder recursively for documents matching selected conditions.

    Args:
        folder_path: Root folder to search
        selected_conditions: List of dicts with at least 'num' and 'desc' keys
        threshold: Minimum fuzzy match score (0-100) to count as a match
        progress_callback: Optional callable(percent, message) for progress updates

    Returns:
        Dict keyed by condition num, each with 'desc' and 'matches' list.
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        return {"error": f"Folder not found: {folder_path}"}

    # Build keyword sets for each condition
    cond_keywords = {}
    for cond in selected_conditions:
        cond_keywords[cond["num"]] = {
            "keywords": extract_keywords(cond["desc"]),
            "desc": cond["desc"],
        }

    # Collect all files
    all_files = []
    for root, dirs, files in os.walk(folder):
        for fname in files:
            fpath = os.path.join(root, fname)
            ext = os.path.splitext(fname)[1].lower()
            if ext in _SKIP_EXTS:
                continue
            try:
                size_mb = os.path.getsize(fpath) / (1024 * 1024)
                if size_mb > MAX_FILE_SIZE_MB:
                    continue
            except OSError:
                continue
            all_files.append((fpath, fname, ext))
            if len(all_files) >= MAX_FILES:
                break
        if len(all_files) >= MAX_FILES:
            break

    total = len(all_files)
    results = {}
    for cond in selected_conditions:
        results[cond["num"]] = {"desc": cond["desc"], "matches": []}

    for file_idx, (fpath, fname, ext) in enumerate(all_files):
        if progress_callback and total > 0:
            pct = int((file_idx / total) * 100)
            progress_callback(pct, f"Scanning {fname}...")

        fname_lower = fname.lower()

        for cnum, cdata in cond_keywords.items():
            kw = cdata["keywords"]

            # --- Filename match ---
            fname_score = match_score(kw, fname_lower)

            # --- Content match (PDF and text files only) ---
            content_matches = []
            if ext in _PDF_EXTS:
                content_matches = extract_matching_pages(fpath, kw, threshold)
            elif ext in _TEXT_EXTS:
                try:
                    with open(fpath, 'r', errors='ignore') as f:
                        text = f.read(100_000)  # read up to 100KB
                    content_score = match_score(kw, text)
                    if content_score >= threshold:
                        snippet = _get_snippet(text, kw)
                        content_matches = [{"page": 1, "score": content_score, "snippet": snippet}]
                except Exception:
                    pass

            # Record matches
            if fname_score >= threshold:
                results[cnum]["matches"].append({
                    "file_path": fpath,
                    "file_name": fname,
                    "match_type": "filename",
                    "score": fname_score,
                    "matched_pages": [],
                    "snippet": "",
                })

            if content_matches:
                pages = [m["page"] for m in content_matches]
                best_score = max(m["score"] for m in content_matches)
                best_snippet = max(content_matches, key=lambda m: m["score"])["snippet"]
                # Don't double-add if filename already matched
                existing = [m for m in results[cnum]["matches"] if m["file_path"] == fpath]
                if existing:
                    existing[0]["matched_pages"] = pages
                    existing[0]["score"] = max(existing[0]["score"], best_score)
                    existing[0]["match_type"] = "filename + content"
                    existing[0]["snippet"] = best_snippet
                else:
                    results[cnum]["matches"].append({
                        "file_path": fpath,
                        "file_name": fname,
                        "match_type": "content",
                        "score": best_score,
                        "matched_pages": pages,
                        "snippet": best_snippet,
                    })

        time.sleep(0.05)  # gentle pause between files

    # Sort matches by score descending
    for cnum in results:
        results[cnum]["matches"].sort(key=lambda m: m["score"], reverse=True)

    if progress_callback:
        progress_callback(100, "Done!")

    return results
