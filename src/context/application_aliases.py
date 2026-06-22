APP_WINDOW_ALIASES = {
    "vscode": ["visual studio code", "code"],
    "chrome": ["google chrome", "chrome"],
    "brave": ["brave"],
    "steam": ["steam"],
    "discord": ["discord"],
    "whatsapp": ["whatsapp"],
    "word": ["microsoft word", "word"],
    "excel": ["microsoft excel", "excel"],
    "spotify": ["spotify"]
}

import difflib

def normalize_app_name(app_name: str) -> str:
    if not app_name:
        return ""
    
    app_name = app_name.lower().strip()
    
    # 1. Exact match against canonical names
    if app_name in APP_WINDOW_ALIASES:
        return app_name
        
    # 2. Exact match against aliases
    for app, aliases in APP_WINDOW_ALIASES.items():
        if app_name in aliases:
            return app
            
    # 3. High-confidence fuzzy match against canonical names and aliases
    all_possible_names = list(APP_WINDOW_ALIASES.keys())
    for aliases in APP_WINDOW_ALIASES.values():
        all_possible_names.extend(aliases)
        
    matches = difflib.get_close_matches(app_name, all_possible_names, n=1, cutoff=0.8)
    if matches:
        best_match = matches[0]
        # Resolve best_match to its canonical name
        if best_match in APP_WINDOW_ALIASES:
            return best_match
        for app, aliases in APP_WINDOW_ALIASES.items():
            if best_match in aliases:
                return app
                
    return app_name
