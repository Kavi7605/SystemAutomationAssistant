import urllib.parse
from typing import Optional
from src.core.website_registry import WEBSITE_REGISTRY

def build_base_url(site_key: str) -> Optional[str]:
    """Returns the base website URL for a registered site key."""
    site_info = WEBSITE_REGISTRY.get(site_key.lower())
    if site_info and "website" in site_info:
        return site_info["website"]
    return None

def build_search_url(site_key: str, query: str, search_mode: str = None) -> Optional[str]:
    """Returns the formatted search URL for a registered site key and query, applying search modes if supported."""
    site_info = WEBSITE_REGISTRY.get(site_key.lower())
    if site_info and "search_url" in site_info:
        # URL encode the query
        encoded_query = urllib.parse.quote_plus(query.strip())
        url = site_info["search_url"].format(query=encoded_query)
        
        if search_mode and site_key.lower() == "github":
            mode_map = {
                "user": "users", "users": "users",
                "repository": "repositories", "repositories": "repositories",
                "issue": "issues", "issues": "issues",
                "pull request": "pullrequests", "pull requests": "pullrequests"
            }
            mapped_mode = mode_map.get(search_mode.lower())
            if mapped_mode:
                if "type=" in url:
                    import re
                    url = re.sub(r'type=[^&]*', f'type={mapped_mode}', url)
                else:
                    url += f"&type={mapped_mode}"
                    
        return url
        
    # Fallback to base website if search_url is not defined but it's a valid site
    return build_base_url(site_key)
