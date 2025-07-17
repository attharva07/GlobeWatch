# PeopleHunt

PeopleHunt is a proof-of-concept OSINT tool designed for educational and ethical purposes only.

It demonstrates a possible workflow for finding public profiles by name and using basic face-matching
techniques. The implementation is intentionally minimal and incomplete.

**Ethics Notice**

- Use only on data you have permission to access.
- Do not stalk, harass or impersonate anyone.
- This project shows how OSINT might be structured and should not be used for malicious activities.

## Folder Structure

```
PeopleHunt/
├── main.py
├── modules/
│   ├── name_search.py
│   ├── image_collector.py
│   ├── face_selector.py
│   ├── face_matcher.py
│   ├── reverse_image_search.py
│   └── osint_deep_scan.py
├── utils/
│   └── display.py
├── requirements.txt
└── output/
    └── matches.json (generated)
```
