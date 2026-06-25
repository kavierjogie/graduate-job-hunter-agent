import re
from typing import Dict, Tuple, Any, Optional
from pydantic import BaseModel

# Common prompt injection signature patterns (case-insensitive)
INJECTION_PATTERNS = [
    r'ignore\s+(?:all\s+)?(?:previous\s+)?instructions',
    r'system\s+override',
    r'jailbreak',
    r'you\s+must\s+(?:now\s+)?act\s+as',
    r'forget\s+previous\s+instructions',
    r'ignore\s+the\s+above',
    r'new\s+instructions\s+follow',
    r'override\s+system\s+prompt'
]

def redact_text(
    text: str, 
    full_name: Optional[str] = None, 
    email: Optional[str] = None, 
    phone: Optional[str] = None
) -> Tuple[str, Dict[str, str]]:
    """
    Scans text for PII (names, emails, phone numbers) and redacts them with placeholders.
    Returns the redacted text and a mapping of placeholders to original values.
    """
    if not text:
        return text, {}
        
    redaction_map = {}
    counter = {"NAME": 1, "EMAIL": 1, "PHONE": 1}
    
    def add_replacement(val: str, ptype: str) -> str:
        # Avoid double-mapping same values
        for ph, original in redaction_map.items():
            if original == val:
                return ph
        ph = f"[{ptype}_{counter[ptype]}]"
        redaction_map[ph] = val
        counter[ptype] += 1
        return ph

    # 1. Redact specific email if provided
    if email and email.strip():
        email_val = email.strip()
        if email_val in text:
            ph = add_replacement(email_val, "EMAIL")
            text = text.replace(email_val, ph)
            
    # 2. Redact specific phone if provided
    if phone and phone.strip():
        phone_val = phone.strip()
        if phone_val in text:
            ph = add_replacement(phone_val, "PHONE")
            text = text.replace(phone_val, ph)

    # 3. Redact specific full name and its constituent parts if provided
    if full_name and full_name.strip():
        fn_val = full_name.strip()
        if fn_val in text:
            ph = add_replacement(fn_val, "NAME")
            text = text.replace(fn_val, ph)
            
        # Redact individual name parts (first, last, middle) if they are at least 3 characters
        name_parts = [part for part in fn_val.split() if len(part) >= 3]
        for part in name_parts:
            # Use word boundary checks to avoid partial matches inside other words
            pattern = r'\b' + re.escape(part) + r'\b'
            matches = re.findall(pattern, text)
            if matches:
                ph = add_replacement(part, "NAME")
                text = re.sub(pattern, ph, text)

    # 4. Redact general emails using regex
    email_regex = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    for m in re.findall(email_regex, text):
        ph = add_replacement(m, "EMAIL")
        text = text.replace(m, ph)

    # 5. Redact general phone numbers using regex (covers common international and local formats)
    phone_regex = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    for m in re.findall(phone_regex, text):
        ph = add_replacement(m, "PHONE")
        text = text.replace(m, ph)

    return text, redaction_map

def rehydrate_text(text: str, redaction_map: Dict[str, str]) -> str:
    """
    Restores original PII values in a string by replacing placeholders.
    """
    if not text or not redaction_map:
        return text
    
    # Sort placeholders by length descending to prevent substring collisions (e.g. [NAME_10] vs [NAME_1])
    sorted_placeholders = sorted(redaction_map.keys(), key=len, reverse=True)
    for ph in sorted_placeholders:
        text = text.replace(ph, redaction_map[ph])
    return text

def rehydrate_object(obj: Any, redaction_map: Dict[str, str]) -> Any:
    """
    Recursively traverses lists, dicts, and Pydantic models to re-hydrate all string fields.
    """
    if not redaction_map:
        return obj
        
    if isinstance(obj, str):
        return rehydrate_text(obj, redaction_map)
    elif isinstance(obj, list):
        return [rehydrate_object(item, redaction_map) for item in obj]
    elif isinstance(obj, dict):
        return {key: rehydrate_object(value, redaction_map) for key, value in obj.items()}
    elif isinstance(obj, BaseModel):
        model_dict = obj.model_dump()
        rehydrated_dict = rehydrate_object(model_dict, redaction_map)
        return obj.__class__(**rehydrated_dict)
    return obj

def check_guardrails(text: str) -> None:
    """
    Scans input text for potential prompt injection patterns and raises ValueError if detected.
    """
    if not text:
        return
        
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            raise ValueError(f"Security Alert: Potential prompt injection detected (pattern match: '{pattern}')")
