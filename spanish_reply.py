"""
Spanish Reply Window - Auto-detect Spanish, translate, and draft replies
Handles Spanish language detection and provides translation + drafting.
"""

import re
from dataclasses import dataclass
from typing import Optional

try:
    from googletrans import Translator
    HAS_GOOGLETRANS = True
except ImportError:
    HAS_GOOGLETRANS = False


SPANISH_INDICATORS = [
    "estimado", "estimada", "hola", "gracias", "por favor", "necesito",
    "documento", "prestamo", "hipoteca", "adjunto", "favor", "favor de",
    "tengo", "puedo", "quiero", "necesitamos", "solicitud", "aprobacion",
    "condiciones", "documentacion", "firmar", "fecha", "lunes", "martes",
    "miercoles", "jueves", "viernes", "sabado", "domingo", "enero",
    "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
    "septiembre", "octubre", "noviembre", "diciembre", "senor", "senora",
    "prestatario", "prestataria", "co", "de", "la", "el", "en", "es",
    "que", "esta", "para", "con", "los", "las", "del", "una", "por",
]


@dataclass
class LanguageDetection:
    """Result of language detection."""
    detected: str
    confidence: float
    is_spanish: bool
    original_text: str


def detect_language(text: str) -> LanguageDetection:
    """
    Detect if text is Spanish or English.
    Returns LanguageDetection with result.
    """
    if not text:
        return LanguageDetection("unknown", 0.0, False, "")
    
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    
    if not words:
        return LanguageDetection("unknown", 0.0, False, text)
    
    spanish_matches = sum(1 for w in words if w in SPANISH_INDICATORS)
    spanish_ratio = spanish_matches / len(words)
    
    is_spanish = spanish_ratio > 0.02 or any(
        indicator in text_lower for indicator in ["estimado", "adjunto", "prestamo", "necesitamos"]
    )
    
    if is_spanish:
        return LanguageDetection("Spanish", spanish_ratio * 10, True, text)
    
    return LanguageDetection("English", 1.0 - spanish_ratio, False, text)


def translate_text(text: str, dest: str = "en") -> Optional[str]:
    """Translate text to destination language."""
    if not HAS_GOOGLETRANS:
        return None
    
    try:
        translator = Translator()
        result = translator.translate(text, dest=dest)
        return result.text
    except Exception:
        return None


def translate_to_english(text: str) -> str:
    """Translate Spanish text to English."""
    result = translate_text(text, "en")
    if result:
        return result

    return "[Error: Could not translate from Spanish to English. Please translate manually.]"


def translate_to_spanish(text: str) -> str:
    """Translate English text to Spanish."""
    result = translate_text(text, "es")
    if result:
        return result

    return "[Error: No se pudo traducir al español. Por favor traduzca manualmente.]"


def get_spanish_template(conditions: str = "") -> str:
    """Get Spanish email template for borrower conditions."""
    if conditions:
        return f"""Estimado/a Prestatario/a,

Estamos trabajando para avanzar su préstamo hacia el cierre lo más rápido posible.
Para mantener todo en orden, necesitamos los siguientes documentos de su parte:

{conditions}

Por favor proporciónelos lo antes posible. Si tiene alguna pregunta sobre cualquiera
de estos documentos, no dude en comunicarse con nosotros.

Gracias por su pronta atención a este asunto.

Atentamente,
[Su Nombre]
Procesador de Préstamos"""

    return """Estimado/a Prestatario/a,

Por favor contáctenos para discutir el estado de su préstamo.

Atentamente,
[Su Nombre]
Procesador de Préstamos"""


def get_english_template(conditions: str = "") -> str:
    """Get English email template for borrower conditions."""
    if conditions:
        return f"""Dear Borrower,

We are working to move your loan toward closing as quickly as possible.
To keep things on track, we need the following item(s) from you:

{conditions}

Please provide these at your earliest convenience. If you have any questions
about any of these items, don't hesitate to reach out.

Thank you for your prompt attention to this matter.

Sincerely,
[Your Name]
Loan Processor"""

    return """Dear Borrower,

Please contact us to discuss the status of your loan.

Sincerely,
[Your Name]
Loan Processor"""


def create_reply(
    original_text: str,
    conditions: str = None,
    recipient_name: str = None,
    reply_type: str = "borrower"
) -> dict:
    """
    Create a reply based on original message language.
    
    Returns:
        dict with: detected_language, english_translation, 
        spanish_draft, english_draft
    """
    detection = detect_language(original_text)
    
    result = {
        "detected_language": detection.detected,
        "is_spanish": detection.is_spanish,
        "confidence": detection.confidence,
    }
    
    if detection.is_spanish:
        result["english_translation"] = translate_to_english(original_text)
        result["spanish_draft"] = get_spanish_template(conditions)
        result["english_draft"] = get_english_template(conditions)
    else:
        result["english_translation"] = original_text
        result["spanish_draft"] = get_spanish_template(conditions)
        result["english_draft"] = get_english_template(conditions)
    
    return result


def format_conditions_for_email(conditions: list) -> str:
    """Format conditions list for email template."""
    if not conditions:
        return ""
    
    formatted = []
    for i, cond in enumerate(conditions, 1):
        formatted.append(f"{i}. {cond}")
    
    return "\n".join(formatted)


class SpanishReplyWindow:
    """
    Streamlit-ready Spanish reply window.
    Handles auto-detect, translation, and drafting.
    """
    
    def __init__(self):
        self.translator_available = HAS_GOOGLETRANS
    
    def render_detection(self, text: str) -> dict:
        """Render language detection for text."""
        detection = detect_language(text)
        
        return {
            "detected": detection.detected,
            "confidence": detection.confidence,
            "is_spanish": detection.is_spanish,
            "translation": None,
        }
    
    def render_translation(self, text: str, to_lang: str = "en") -> dict:
        """Render translation for text."""
        if to_lang == "es":
            translated = translate_to_spanish(text)
        else:
            translated = translate_to_english(text)
        
        return {
            "original": text,
            "translated": translated,
            "target_language": to_lang,
        }
    
    def render_draft(
        self,
        original_text: str,
        conditions: list = None,
        recipient_type: str = "borrower"
    ) -> dict:
        """Render full reply draft."""
        conditions_str = format_conditions_for_email(conditions) if conditions else ""
        return create_reply(original_text, conditions_str, reply_type=recipient_type)


def quick_detect(text: str) -> str:
    """Quick language detection - returns 'Spanish' or 'English'."""
    detection = detect_language(text)
    return detection.detected


def is_spanish(text: str) -> bool:
    """Quick check if text is Spanish."""
    return detect_language(text).is_spanish