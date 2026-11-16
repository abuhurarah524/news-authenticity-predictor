"""Shared, serializable text preparation for training and prediction."""
import html
import re
import unicodedata


def clean_text(value):
    text = unicodedata.normalize('NFKC', html.unescape(str(value)))
    # Ruling sections and explicit ratings reveal the target rather than evidence.
    text = re.split(r'\bour ruling\b', text, maxsplit=1, flags=re.I)[0]
    sentences = re.split(r'(?<=[.!?])\s+|[\r\n]+', text)
    rating = re.compile(
        r'\b(?:we\s+(?:rate|rated)|(?:politifact|fact.check\w*)\s+(?:rates?|rated)|'
        r'(?:mostly[\s-]+(?:true|false)|half[\s-]+true|pants[\s-]+(?:on[\s-]+)?fire))\b', re.I)
    text = ' '.join(sentence for sentence in sentences if not rating.search(sentence))
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
    text = re.sub(r'\b(?:reuters|politifact)\b', ' ', text, flags=re.I)
    return re.sub(r'\s+', ' ', text).strip().lower()
