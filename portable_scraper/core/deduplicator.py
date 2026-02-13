import re

def normalize_title(title: str) -> str:
    if not title:
        return ""

    t = title.lower()
    t = re.sub(r'[^a-z0-9 ]', ' ', t)   # remove punctuation
    t = re.sub(r'\s+', ' ', t)          # collapse spaces
    return t.strip()
