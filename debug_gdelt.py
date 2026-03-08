"""
Run this script from your GlobeWatch project root:
  python debug_gdelt.py

It will show you exactly what GDELT returns and where the pipeline breaks.
"""
import httpx
import json

GDELT_BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_QUERY = "(flood OR wildfire OR earthquake OR outbreak OR protest)"
GDELT_MAX_RECORDS = 10

params = {
    "query": GDELT_QUERY,
    "mode": "ArtList",
    "maxrecords": GDELT_MAX_RECORDS,
    "format": "json",
    "sort": "datedesc",
}

print("=" * 60)
print("Hitting GDELT API...")
print(f"URL: {GDELT_BASE_URL}")
print(f"Params: {params}")
print("=" * 60)

try:
    with httpx.Client(timeout=20.0) as client:
        response = client.get(GDELT_BASE_URL, params=params)
        print(f"HTTP Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        raw = response.text
        print(f"\nRaw response (first 1000 chars):\n{raw[:1000]}")

        try:
            payload = response.json()
            print(f"\nParsed JSON type: {type(payload)}")
            if isinstance(payload, dict):
                print(f"Top-level keys: {list(payload.keys())}")
                articles = payload.get("articles", [])
                print(f"\nNumber of articles: {len(articles)}")
                if articles:
                    print(f"\nFirst article keys: {list(articles[0].keys())}")
                    print(f"\nFirst article:\n{json.dumps(articles[0], indent=2)}")
                    print(f"\nSecond article:\n{json.dumps(articles[1], indent=2)}" if len(articles) > 1 else "")
                    
                    # Check what country codes appear
                    countries = [a.get("sourcecountry", "MISSING") for a in articles]
                    print(f"\nCountry codes in response: {countries}")
                    
                    # Check if locationlat exists at all
                    has_lat = any("locationlat" in a for a in articles)
                    has_lon = any("locationlong" in a for a in articles)
                    print(f"\nlocationlat field exists: {has_lat}")
                    print(f"locationlong field exists: {has_lon}")
                else:
                    print("\nWARNING: 'articles' list is empty!")
                    print(f"Full payload:\n{json.dumps(payload, indent=2)}")
            else:
                print(f"Unexpected payload type: {type(payload)}")
                print(f"Content: {payload}")
        except Exception as e:
            print(f"\nFailed to parse JSON: {e}")
            print(f"Raw text: {raw}")

except Exception as e:
    print(f"Request failed: {e}")
