"""
Application alias mapping for application normalizer.
Maps various ways users refer to applications to a standardized alias.
"""

APPLICATION_ALIASES = {
    "vscode": ["vs code", "visual studio code", "code"],
    "chrome": ["google chrome"],
    "github": ["github desktop"],
    "word": ["ms word", "microsoft word"],
    "teams": ["microsoft teams"]
}

# Reverse mapping for O(1) lookup
ALIAS_TO_APP = {}
for app, aliases in APPLICATION_ALIASES.items():
    for alias in aliases:
        ALIAS_TO_APP[alias.lower()] = app
