"""
Number words and phrase conversions for number normalizer.
"""

# Common word numbers
WORD_TO_NUMBER = {
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "eleven": "11",
    "twelve": "12"
}

# Time phrase multipliers to standard units (seconds)
TIME_PHRASES = {
    "half minute": "30 seconds",
    "one minute": "60 seconds",
    "two minutes": "120 seconds",
    "quarter hour": "900 seconds"
}

# Ensure longer phrases are checked first
TIME_PHRASES_SORTED = sorted(TIME_PHRASES.keys(), key=len, reverse=True)
