"""Module for downloading profile images."""
import os
from typing import Optional
from urllib.parse import urlparse

import requests


def download_image(url: str, output_dir: str) -> Optional[str]:
    """Download image from URL into output_dir.

    Returns the local file path if successful, otherwise None.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.basename(urlparse(url).path) or "image.jpg"
        filepath = os.path.join(output_dir, filename)
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(resp.content)
        return filepath
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None
