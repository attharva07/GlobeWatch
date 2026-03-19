"""GDELT provider for fetching real-world geolocated events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import Settings


class ProviderRateLimitError(Exception):
    """Raised when provider responds with HTTP 429."""


class ProviderNetworkError(Exception):
    """Raised when a network/transport-level failure prevents fetching events."""


@dataclass
class ProviderEvent:
    external_id: str | None
    title: str
    description: str
    category: str
    source: str
    provider: str
    lat: float
    lon: float
    country: str
    city: str
    event_timestamp: datetime
    url: str | None
    metadata: dict[str, Any]


# Approximate country centroids keyed by GDELT FIPS 2-letter source country codes.
# GDELT uses FIPS 10-4 country codes, not ISO 3166.
COUNTRY_CENTROIDS: dict[str, tuple[float, float, str]] = {
    "US": (37.09, -95.71, "United States"),
    "UK": (55.37, -3.44, "United Kingdom"),
    "GM": (51.16, 10.45, "Germany"),
    "FR": (46.23, 2.21, "France"),
    "RS": (61.52, 105.32, "Russia"),
    "CH": (35.86, 104.19, "China"),
    "IN": (20.59, 78.96, "India"),
    "BR": (-14.24, -51.93, "Brazil"),
    "AS": (-25.27, 133.77, "Australia"),
    "CA": (56.13, -106.35, "Canada"),
    "JA": (36.20, 138.25, "Japan"),
    "MX": (23.63, -102.55, "Mexico"),
    "IT": (41.87, 12.56, "Italy"),
    "SP": (40.46, -3.75, "Spain"),
    "PO": (39.40, -8.22, "Portugal"),
    "NL": (52.13, 5.29, "Netherlands"),
    "SW": (60.13, 18.64, "Sweden"),
    "NO": (60.47, 8.47, "Norway"),
    "DA": (56.26, 9.50, "Denmark"),
    "FI": (61.92, 25.75, "Finland"),
    "PL": (51.92, 19.14, "Poland"),
    "UP": (48.38, 31.16, "Ukraine"),
    "EG": (26.82, 30.80, "Egypt"),
    "SA": (23.89, 45.08, "Saudi Arabia"),
    "IR": (32.43, 53.69, "Iran"),
    "IZ": (33.22, 43.68, "Iraq"),
    "IS": (31.05, 34.85, "Israel"),
    "SY": (34.80, 38.99, "Syria"),
    "TU": (38.96, 35.24, "Turkey"),
    "PK": (30.38, 69.35, "Pakistan"),
    "AF": (33.93, 67.71, "Afghanistan"),
    "ID": (-0.79, 113.92, "Indonesia"),
    "TH": (15.87, 100.99, "Thailand"),
    "VM": (14.06, 108.28, "Vietnam"),
    "MY": (4.21, 101.98, "Malaysia"),
    "PH": (12.88, 121.77, "Philippines"),
    "KS": (35.91, 127.77, "South Korea"),
    "KN": (40.34, 127.51, "North Korea"),
    "SF": (-28.47, 24.68, "South Africa"),
    "NI": (9.08, 8.68, "Nigeria"),
    "ET": (9.15, 40.49, "Ethiopia"),
    "KE": (-0.02, 37.91, "Kenya"),
    "GH": (7.95, -1.02, "Ghana"),
    "CI": (7.54, -5.55, "Ivory Coast"),
    "SU": (12.86, 30.22, "Sudan"),
    "LY": (26.34, 17.23, "Libya"),
    "MO": (31.79, -7.09, "Morocco"),
    "TN": (33.89, 9.54, "Tunisia"),
    "AG": (28.03, 1.66, "Algeria"),
    "AR": (-38.42, -63.62, "Argentina"),
    "CO": (4.57, -74.30, "Colombia"),
    "VE": (6.42, -66.59, "Venezuela"),
    "PE": (-9.19, -75.02, "Peru"),
    "CL": (-35.68, -71.54, "Chile"),
    "UY": (-32.52, -55.77, "Uruguay"),
    "BL": (-16.29, -63.59, "Bolivia"),
    "EC": (-1.83, -78.18, "Ecuador"),
    "GR": (39.07, 21.82, "Greece"),
    "HU": (47.16, 19.50, "Hungary"),
    "RO": (45.94, 24.97, "Romania"),
    "BU": (42.73, 25.49, "Bulgaria"),
    "EZ": (49.82, 15.47, "Czech Republic"),
    "LO": (48.67, 19.70, "Slovakia"),
    "NZ": (-40.90, 174.89, "New Zealand"),
    "JO": (30.59, 36.24, "Jordan"),
    "LE": (33.85, 35.86, "Lebanon"),
    "YM": (15.55, 48.52, "Yemen"),
    "OM": (21.51, 55.92, "Oman"),
    "AE": (23.42, 53.85, "UAE"),
    "KU": (29.34, 47.49, "Kuwait"),
    "QA": (25.35, 51.18, "Qatar"),
    "BA": (26.03, 50.55, "Bahrain"),
    "SG": (1.35, 103.82, "Singapore"),
    "BT": (27.51, 90.43, "Bhutan"),
    "NP": (28.39, 84.12, "Nepal"),
    "CE": (7.87, 80.77, "Sri Lanka"),
    "BG": (23.68, 90.36, "Bangladesh"),
    "MV": (3.20, 73.22, "Maldives"),
    "CB": (12.57, 104.99, "Cambodia"),
    "LA": (19.86, 102.50, "Laos"),
    "BX": (4.54, 114.73, "Brunei"),
    "TW": (23.70, 120.96, "Taiwan"),
    "HK": (22.40, 114.11, "Hong Kong"),
    "MG": (-18.77, 46.87, "Madagascar"),
    "MZ": (-18.67, 35.53, "Mozambique"),
    "ZI": (-19.02, 29.15, "Zimbabwe"),
    "ZA": (-13.13, 27.85, "Zambia"),
    "AO": (-11.20, 17.87, "Angola"),
    "CG": (-0.23, 15.83, "Congo"),
    "CF": (6.61, 20.94, "Central African Republic"),
    "CD": (-4.04, 21.76, "DR Congo"),
    "UG": (1.37, 32.29, "Uganda"),
    "TZ": (-6.37, 34.89, "Tanzania"),
    "RW": (-1.94, 29.87, "Rwanda"),
    "BI": (-3.37, 29.92, "Burundi"),
    "SO": (5.15, 46.20, "Somalia"),
    "DJ": (11.83, 42.59, "Djibouti"),
    "ER": (15.18, 39.78, "Eritrea"),
    "ML": (17.57, -3.99, "Mali"),
    "NG": (13.44, 2.08, "Niger"),
    "CT": (15.45, 18.73, "Chad"),
    "SN": (14.50, -14.45, "Senegal"),
    "GV": (11.80, -15.18, "Guinea-Bissau"),
    "GC": (11.00, -10.90, "Guinea"),
    "SL": (8.46, -11.78, "Sierra Leone"),
    "LI": (6.43, -9.43, "Liberia"),
    "IV": (7.54, -5.55, "Ivory Coast"),
    "BF": (12.36, -1.56, "Burkina Faso"),
    "TO": (8.62, 0.82, "Togo"),
    "BN": (9.31, 2.32, "Benin"),
    "CM": (7.37, 12.35, "Cameroon"),
    "EK": (1.65, 10.27, "Equatorial Guinea"),
    "GA": (-0.80, 11.61, "Gabon"),
    "MP": (-13.25, 34.30, "Malawi"),
    "KZ": (48.02, 66.92, "Kazakhstan"),
    "UZ": (41.38, 64.59, "Uzbekistan"),
    "TX": (38.97, 59.56, "Turkmenistan"),
    "KG": (41.20, 74.77, "Kyrgyzstan"),
    "TI": (38.86, 71.28, "Tajikistan"),
    "GG": (42.32, 43.36, "Georgia"),
    "AM": (40.07, 45.04, "Armenia"),
    "AJ": (40.14, 47.58, "Azerbaijan"),
    "MD": (47.41, 28.37, "Moldova"),
    "BO": (53.71, 27.95, "Belarus"),
    "LH": (56.88, 24.60, "Latvia"),
    "LT": (55.17, 23.88, "Lithuania"),
    "EN": (58.60, 25.01, "Estonia"),
    "IC": (64.96, -19.02, "Iceland"),
    "EI": (53.41, -8.24, "Ireland"),
    "BE": (50.50, 4.47, "Belgium"),
    "LU": (49.82, 6.13, "Luxembourg"),
    "SZ": (46.82, 8.23, "Switzerland"),
    "AU": (47.52, 14.55, "Austria"),
    "SI": (46.15, 14.99, "Slovenia"),
    "HR": (45.10, 15.20, "Croatia"),
    "BK": (44.02, 17.67, "Bosnia"),
    "MK": (41.61, 21.75, "North Macedonia"),
    "AL": (41.15, 20.17, "Albania"),
    "MJ": (42.71, 19.37, "Montenegro"),
    "RB": (44.02, 21.01, "Serbia"),
    "CY": (35.13, 33.43, "Cyprus"),
    "MT": (35.94, 14.38, "Malta"),
    "FO": (61.89, -6.91, "Faroe Islands"),
}


class GDELTProvider:
    """Adapter for GDELT DOC 2.0 API.

    The DOC 2.0 ArtList mode does NOT return lat/lon fields — it returns
    url, title, seendate, socialimage, domain, language, sourcecountry.
    We resolve coordinates from the sourcecountry FIPS code using a
    built-in centroid lookup table.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def fetch_events(self) -> list[ProviderEvent]:
        params = {
            "query": self.settings.GDELT_QUERY,
            "mode": "ArtList",
            "maxrecords": self.settings.GDELT_MAX_RECORDS,
            "format": "json",
            "sort": "datedesc",
        }
        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.get(self.settings.GDELT_BASE_URL, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise ProviderRateLimitError("GDELT rate limit reached (HTTP 429)") from exc
            raise ProviderNetworkError(f"GDELT request failed with HTTP {exc.response.status_code}") from exc
        except httpx.TransportError as exc:
            raise ProviderNetworkError(f"GDELT network error: {exc}") from exc

        articles = payload.get("articles", []) if isinstance(payload, dict) else []
        normalized: list[ProviderEvent] = []
        for item in articles:
            if not isinstance(item, dict):
                continue

            # Filter to English-language articles only.
            language = str(item.get("language") or "").strip().lower()
            if not language.startswith("english"):
                continue

            # Resolve coordinates from sourcecountry FIPS code.
            # The DOC 2.0 ArtList response does NOT include locationlat/locationlong —
            # those only exist in the GEO 2.0 API. We use a centroid lookup instead.
            fips_code = str(item.get("sourcecountry") or "").strip().upper()
            centroid = COUNTRY_CENTROIDS.get(fips_code)
            if centroid is None:
                # Unknown country — skip rather than place at (0, 0)
                continue
            lat_f, lon_f, country_name = centroid

            title = str(item.get("title") or "Untitled event").strip()
            if not title:
                continue

            seen_date = self._parse_timestamp(item.get("seendate"))
            source_name = str(item.get("domain") or "GDELT").strip() or "GDELT"
            url = item.get("url")
            category = self._categorize(title)

            normalized.append(
                ProviderEvent(
                    external_id=self._external_id(url, item),
                    title=title,
                    description=title,
                    category=category,
                    source=source_name,
                    provider="gdelt",
                    lat=lat_f,
                    lon=lon_f,
                    country=country_name,
                    city=country_name,
                    event_timestamp=seen_date,
                    url=str(url).strip() if isinstance(url, str) and url.strip() else None,
                    metadata={
                        "tone": item.get("tone"),
                        "language": item.get("language"),
                        "socialimage": item.get("socialimage"),
                        "fips_country": fips_code,
                    },
                )
            )

        return normalized

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        if isinstance(value, str):
            for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S"):
                try:
                    return datetime.strptime(value, fmt).replace(tzinfo=UTC)
                except ValueError:
                    continue
        return datetime.now(UTC)

    @staticmethod
    def _external_id(url: Any, item: dict[str, Any]) -> str | None:
        if isinstance(url, str) and url.strip():
            return url.strip()
        docid = item.get("documentidentifier")
        if isinstance(docid, str) and docid.strip():
            return docid.strip()
        return None

    @staticmethod
    def _categorize(title: str) -> str:
        lowered = title.lower()
        if any(word in lowered for word in ["flood", "storm", "wildfire", "earthquake", "weather", "hurricane", "tornado", "tsunami", "drought"]):
            return "weather_alert"
        if any(word in lowered for word in ["health", "virus", "outbreak", "hospital", "disease", "pandemic", "vaccine"]):
            return "public_health"
        if any(word in lowered for word in ["protest", "strike", "election", "conflict", "riot", "war", "military", "attack"]):
            return "civic"
        return "world_event"
