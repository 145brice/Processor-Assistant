"""
AI Processing Engine for Processor Traien
All document analysis happens in memory - no files are saved.
"""

import os
from string import Template
from openai import OpenAI
from dotenv import load_dotenv
from prompts import (
    SYSTEM_PROMPT,
    CONDITION_EXTRACTION_PROMPT,
    BANK_STATEMENT_RULES_PROMPT,
    RISK_FLAG_PROMPT,
    EMAIL_DRAFT_PROMPT,
    AUTO_EMAIL_PROMPT,
    WEB_RESEARCH_PROMPT,
    CONTACTS_EXTRACT_PROMPT,
    STACKING_ORDER_PROMPT,
    MEGA_CHECKLIST_PROMPT,
    DOC_TYPE_CONTEXT,
)

def _load_env():
    """Force reload .env every time to pick up changes."""
    load_dotenv(override=True)

_load_env()


def get_client():
    """Create OpenAI client (works with Grok, GPT-4, any OpenAI-compatible API)."""
    _load_env()
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )


def get_model():
    _load_env()
    return os.getenv("OPENAI_MODEL", "gpt-4o")


def _call_ai(prompt: str, user_history: list[dict] | None = None) -> str:
    """Core AI call. Stuffs user history into context for memory."""
    client = get_client()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Stuff last 5 history entries for context (memory feature)
    if user_history:
        history_text = "\n".join(
            f"- [{h.get('doc_type', 'Unknown')}] {h.get('summary', '')}"
            for h in user_history[-5:]
        )
        messages.append(
            {
                "role": "system",
                "content": f"User's recent processing history for context:\n{history_text}",
            }
        )

    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=get_model(),
        messages=messages,
        temperature=0.1,  # Low temp for accuracy
        max_tokens=8000,
    )
    return response.choices[0].message.content


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes in memory. Never saves to disk."""
    from pypdf import PdfReader
    import io

    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()


def extract_conditions(pdf_text: str, doc_type: str, user_history=None) -> str:
    """Extract conditions from a mortgage document."""
    context = DOC_TYPE_CONTEXT.get(doc_type, "")
    prompt = Template(CONDITION_EXTRACTION_PROMPT).substitute(
        doc_type=f"{doc_type} ({context})", text=pdf_text
    )
    return _call_ai(prompt, user_history)


def check_bank_rules(pdf_text: str, user_history=None) -> str:
    """Run 50-rule bank statement analysis."""
    prompt = Template(BANK_STATEMENT_RULES_PROMPT).substitute(text=pdf_text)
    return _call_ai(prompt, user_history)


def flag_risks(pdf_text: str, user_history=None) -> str:
    """Scan document for risk indicators."""
    prompt = Template(RISK_FLAG_PROMPT).substitute(text=pdf_text)
    return _call_ai(prompt, user_history)


def draft_email(
    conditions: str, recipient_type: str, language: str = "English", user_history=None
) -> str:
    """Draft an email based on extracted conditions."""
    prompt = Template(EMAIL_DRAFT_PROMPT).substitute(
        recipient_type=recipient_type, language=language, conditions=conditions
    )
    return _call_ai(prompt, user_history)


def auto_draft_emails(conditions: str, user_history=None) -> str:
    """Auto-draft all emails based on conditions, grouped by responsible party."""
    prompt = Template(AUTO_EMAIL_PROMPT).substitute(conditions=conditions)
    return _call_ai(prompt, user_history)


def web_research(conditions: str, user_history=None) -> str:
    """Identify conditions that need online verification and provide search links."""
    prompt = Template(WEB_RESEARCH_PROMPT).substitute(conditions=conditions)
    return _call_ai(prompt, user_history)


def extract_contacts(pdf_text: str, user_history=None) -> str:
    """Extract names, contacts, and loan details from document."""
    prompt = Template(CONTACTS_EXTRACT_PROMPT).substitute(text=pdf_text)
    return _call_ai(prompt, user_history)


def generate_stacking_order(pdf_text: str, user_history=None) -> str:
    """Generate loan file stacking order checklist."""
    prompt = Template(STACKING_ORDER_PROMPT).substitute(text=pdf_text)
    return _call_ai(prompt, user_history)


def run_mega_checklist(pdf_text: str, user_history=None) -> str:
    """Run the 250-item mega checklist against the document."""
    prompt = Template(MEGA_CHECKLIST_PROMPT).substitute(text=pdf_text)
    return _call_ai(prompt, user_history)


def process_document(pdf_bytes: bytes, doc_type: str, user_history=None) -> dict:
    """
    Main processing function. Takes PDF bytes, returns structured results.
    PDF is ONLY in memory - never saved anywhere.
    """
    # Extract text in memory
    text = extract_text_from_pdf(pdf_bytes)

    if not text or len(text.strip()) < 50:
        return {
            "success": False,
            "error": "Could not extract enough text from this PDF. It may be a scanned image (OCR support coming in Phase 2).",
            "conditions": "",
            "risks": "",
            "text_length": len(text) if text else 0,
        }

    # Only extract conditions on upload - everything else is on-demand
    conditions = extract_conditions(text, doc_type, user_history)

    return {
        "success": True,
        "conditions": conditions,
        "text_length": len(text),
        "doc_type": doc_type,
    }
