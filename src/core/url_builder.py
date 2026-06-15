import urllib.parse
from typing import Optional
from src.core.website_registry import WEBSITE_REGISTRY

def build_base_url(site_key: str) -> Optional[str]:
    """Returns the base website URL for a registered site key."""
    site_info = WEBSITE_REGISTRY.get(site_key.lower())
    if site_info and "website" in site_info:
        return site_info["website"]
    return None

def build_search_url(site_key: str, query: str) -> Optional[str]:
    """Returns the formatted search URL for a registered site key and query."""
    site_info = WEBSITE_REGISTRY.get(site_key.lower())
    if site_info and "search_url" in site_info:
        # URL encode the query
        encoded_query = urllib.parse.quote_plus(query.strip())
        return site_info["search_url"].format(query=encoded_query)
    # Fallback to base website if search_url is not defined but it's a valid site
    return build_base_url(site_key)
