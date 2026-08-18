"""
RAG Security & Prompt-Injection Defense Layer.
Isolates untrusted document texts with strict XML sandboxing and flags adversarial prompt injections.
"""

import re
from typing import Dict, Any, Tuple, List


INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"disregard\s+(all\s+)?system\s+prompts",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"system\s*override",
    r"execute\s+command",
    r"delete\s+database",
    r"bypass\s+guardband",
    r"approve\s+out\s+of\s+tolerance",
]


def sanitize_document_text(raw_text: str) -> Tuple[str, bool, List[str]]:
    """
    Sanitize text and detect if it contains adversarial prompt injection strings.
    
    Returns:
      (sanitized_xml_wrapped_text, has_injection_attempt, detected_patterns)
    """
    detected = []
    lower_text = raw_text.lower()

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower_text):
            detected.append(pattern)

    has_injection = len(detected) > 0

    # Clean dangerous escape chars
    escaped = (
        raw_text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

    # Wrap in strict document isolation container
    isolated_xml = (
        f'<document_content data-isolated="true" security-warning="{has_injection}">\n'
        f'{escaped}\n'
        f'</document_content>'
    )

    return isolated_xml, has_injection, detected
