"""Module providing CLI face selection tools."""
from typing import List, Dict, Optional


def select_face(profiles: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """Display a simple CLI list of profiles and return the selected one."""
    if not profiles:
        print("No profiles found.")
        return None

    for idx, prof in enumerate(profiles, 1):
        print(f"[{idx}] {prof.get('name')} - {prof.get('platform')} - {prof.get('url')}")
    choice = input("Select the correct person by number (or press Enter to cancel): ")
    if not choice.isdigit():
        return None
    idx = int(choice) - 1
    if 0 <= idx < len(profiles):
        return profiles[idx]
    return None
