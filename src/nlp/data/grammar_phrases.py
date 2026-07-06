"""
Phrases and filler words to be removed during grammar normalization.
"""

GRAMMAR_PHRASES = [
    "could you please",
    "can you please",
    "would you please",
    "could you",
    "can you",
    "would you",
    "could u",
    "can u",
    "would u",
    "please",
    "kindly",
    "i want you to",
    "i need you to",
    "actually",
    "just",
    "maybe",
    "for me",
    "right now",
    "at the moment"
]

# Ensure longer phrases are removed first by sorting by length descending
GRAMMAR_PHRASES.sort(key=len, reverse=True)
