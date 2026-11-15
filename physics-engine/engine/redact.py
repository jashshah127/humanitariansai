"""
REDACT -- removes personal details from problem text before it is stored in problems_log.

problems_log has no user or session id (identity scope "none", like the event log), but it
does keep the problem text, and a student can paste anything into it: "I'm jane@uni.edu,
NUID 002123456, here's my homework...". So the server cleans the text first and stores how
many items it replaced in problems_log.redactions.

Only the STORED copy is cleaned. The solver always gets the original text -- redaction must
never change an answer.

THE TRADE-OFF: physics text is full of numbers, so every rule is deliberately narrow.
  - emails, links      -> always replaced (they cannot be physics)
  - phone numbers      -> only in phone-like layouts: 617-555-1234, 617.555.1234,
                          (617) 555-1234, +1 617 555 1234. A bare run like 6175551234 is
                          left alone, because "c = 300000000 m/s" looks the same.
  - ID numbers         -> only when labelled (NUID, student ID, SSN ...) or in the SSN
                          layout 123-45-6789. An unlabelled 9-digit number is left alone
                          for the same reason.
  - names              -> NOT handled. No rule separates "Jane" from "Newton" or "Ohm";
                          that needs a name-recognition model. The table is therefore
                          *mostly* de-identified (an open point under Q6).
Missing a phone number is a privacy cost; mangling "300000000 m/s" would make the log wrong
for everyone. The rules lean towards keeping physics intact and say so here.
"""
import re

_LINK = re.compile(r"\b(?:https?://|www\.)[^\s<>\"']*[^\s<>\"'.,;:!?)\]]", re.I)
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
# The label stays (it is harmless and shows what was removed); only the number is replaced.
_LABELLED_ID = re.compile(
    r"(\b(?:NUID|student\s*(?:ID|number|no\.?)|ID|SSN|social\s+security(?:\s+number)?)\b"
    r"(?:\s*(?:is|number|no\.?|#|:))*\s*)"
    r"[A-Z]{0,3}\d[\d-]{4,}\d",
    re.I)
_SSN = re.compile(r"(?<![\w.-])\d{3}-\d{2}-\d{4}(?![\w-]|\.\d)")
_PHONE = re.compile(
    r"(?<![\w.+-])(?:"
    r"\+\d{1,3}[\s.-]?\(?\d{2,4}\)?[\s.-]?\d{3}[\s.-]?\d{3,4}"   # +1 617 555 1234
    r"|\(\d{3}\)\s?\d{3}[.-]\d{4}"                                # (617) 555-1234
    r"|\d{3}[.-]\d{3}[.-]\d{4}"                                   # 617-555-1234
    r")(?![\w-]|\.\d)")

# Order matters: a link can contain an "@" or digits, so links go first; labelled IDs go
# before phones so "Student ID: 617-555-1234" is counted once, as an ID.
_RULES = (
    (_LINK, "[LINK]"),
    (_EMAIL, "[EMAIL]"),
    (_LABELLED_ID, r"\1[ID]"),
    (_SSN, "[ID]"),
    (_PHONE, "[PHONE]"),
)


def redact(text):
    """Return (cleaned_text, number_of_items_replaced). Safe to run twice: the markers
    themselves never match, so a second pass returns the same text and 0."""
    total = 0
    for pattern, marker in _RULES:
        text, n = pattern.subn(marker, text)
        total += n
    return text, total
