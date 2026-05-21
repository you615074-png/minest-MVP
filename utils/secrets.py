import re


def _looks_like_key(s: str) -> bool:
    has_alpha = any(c.isalpha() for c in s)
    has_digit = any(c.isdigit() for c in s)
    return has_alpha and has_digit and len(set(s)) > 20


def redact_secrets(text: str) -> str:
    if not text:
        return text
    text = re.sub(r'sk-[a-zA-Z0-9]{20,}', '[API_KEY_REDACTED]', text)
    text = re.sub(r'Bearer\s+[a-zA-Z0-9_\-]{20,}', 'Bearer [REDACTED]', text)
    return text
