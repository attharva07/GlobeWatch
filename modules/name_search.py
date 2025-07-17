"""Module for searching public profiles by name."""
from typing import List, Dict


def search_name(full_name: str) -> List[Dict[str, str]]:
    """Return a list of potential profiles for the given name.

    Each dictionary in the list should contain keys:
    - platform: name of the website
    - name: full name string
    - username: handle or username
    - url: profile URL
    - photo_url: direct link to a profile photo
    
    This function currently returns an empty list as a stub.
    """
    # TODO: Implement actual scraping logic for each platform
    return []
