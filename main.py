"""Entry point for PeopleHunt proof of concept."""
import argparse
import json
from pathlib import Path

from modules import name_search, image_collector, face_selector, reverse_image_search, face_matcher, osint_deep_scan
from utils.display import print_header


def main():
    parser = argparse.ArgumentParser(description="PeopleHunt OSINT tool")
    parser.add_argument("full_name", help="Full name of the person to search")
    parser.add_argument("--output", default="output", help="Directory for output files")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    print_header(f"Searching for {args.full_name}")
    profiles = name_search.search_name(args.full_name)

    # Download one image per profile if available
    for prof in profiles:
        photo_url = prof.get("photo_url")
        if photo_url:
            local_path = image_collector.download_image(photo_url, args.output)
            prof["photo_path"] = local_path

    selected = face_selector.select_face(profiles)
    if not selected:
        print("No selection made. Exiting.")
        return

    print_header("Reverse Image Search")
    if selected.get("photo_path"):
        reverse_image_search.reverse_search(selected["photo_path"])

    print_header("Deep OSINT Scan")
    results = osint_deep_scan.deep_scan(selected.get("name", ""))
    matches_file = output_dir / "matches.json"
    with matches_file.open("w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {matches_file}")


if __name__ == "__main__":
    main()
