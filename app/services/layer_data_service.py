"""Demo data service for additional geospatial layers.

Provides sample data for all new layer types. In production, each layer
would be backed by its own provider adapter (ADS-B Exchange, MarineTraffic,
AbuseIPDB, etc.). For now this generates realistic demo data.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime


class LayerDataService:
    """Returns demo data for all layer types."""

    @staticmethod
    def get_flights() -> list[dict]:
        now = datetime.now(UTC).isoformat()
        return [
            {
                "id": "fl-001",
                "callsign": "UAL256",
                "origin": [-73.78, 40.64],
                "destination": [-0.46, 51.47],
                "current_position": [-30.0, 50.2, 11000],
                "heading": 62.0,
                "speed": 480,
                "altitude": 36000,
                "aircraft_type": "B777",
                "timestamp": now,
            },
            {
                "id": "fl-002",
                "callsign": "DLH410",
                "origin": [8.57, 50.03],
                "destination": [-87.90, 41.98],
                "current_position": [-20.5, 55.1, 10500],
                "heading": 280.0,
                "speed": 495,
                "altitude": 38000,
                "aircraft_type": "A340",
                "timestamp": now,
            },
            {
                "id": "fl-003",
                "callsign": "SIA12",
                "origin": [103.99, 1.36],
                "destination": [139.78, 35.55],
                "current_position": [120.5, 18.3, 12000],
                "heading": 32.0,
                "speed": 510,
                "altitude": 39000,
                "aircraft_type": "A380",
                "timestamp": now,
            },
            {
                "id": "fl-004",
                "callsign": "QFA1",
                "origin": [151.18, -33.95],
                "destination": [0.07, 51.15],
                "current_position": [75.0, 5.0, 11500],
                "heading": 315.0,
                "speed": 505,
                "altitude": 37000,
                "aircraft_type": "B787",
                "timestamp": now,
            },
            {
                "id": "fl-005",
                "callsign": "EK215",
                "origin": [55.36, 25.25],
                "destination": [-118.41, 33.94],
                "current_position": [30.0, 52.0, 11200],
                "heading": 320.0,
                "speed": 490,
                "altitude": 40000,
                "aircraft_type": "A380",
                "timestamp": now,
            },
        ]

    @staticmethod
    def get_ships() -> list[dict]:
        now = datetime.now(UTC).isoformat()
        return [
            {
                "id": "sh-001",
                "name": "MSC OSCAR",
                "mmsi": "353136000",
                "position": [1.2, 51.9],
                "path": [[-5.0, 48.0], [-2.0, 49.5], [0.5, 51.0], [1.2, 51.9]],
                "speed": 14.5,
                "heading": 45.0,
                "ship_type": "Container",
                "destination": "ROTTERDAM",
                "timestamp": now,
            },
            {
                "id": "sh-002",
                "name": "CRUDE VOYAGER",
                "mmsi": "477123456",
                "position": [50.2, 25.8],
                "path": [[56.0, 26.5], [54.0, 26.0], [52.0, 25.9], [50.2, 25.8]],
                "speed": 12.0,
                "heading": 270.0,
                "ship_type": "Tanker",
                "destination": "FUJAIRAH",
                "timestamp": now,
            },
            {
                "id": "sh-003",
                "name": "PACIFIC TRADER",
                "mmsi": "636092789",
                "position": [121.5, 31.2],
                "path": [[135.0, 34.0], [130.0, 33.0], [125.0, 32.0], [121.5, 31.2]],
                "speed": 18.0,
                "heading": 240.0,
                "ship_type": "Bulk Carrier",
                "destination": "SHANGHAI",
                "timestamp": now,
            },
            {
                "id": "sh-004",
                "name": "MAERSK TIGRIS",
                "mmsi": "219032000",
                "position": [-79.5, 9.0],
                "path": [[-76.0, 10.5], [-77.5, 9.8], [-78.5, 9.4], [-79.5, 9.0]],
                "speed": 10.0,
                "heading": 250.0,
                "ship_type": "Container",
                "destination": "PANAMA",
                "timestamp": now,
            },
        ]

    @staticmethod
    def get_cyber_iocs() -> list[dict]:
        now = datetime.now(UTC).isoformat()
        return [
            {"id": "ioc-001", "ip": "185.220.101.34", "lat": 52.52, "lon": 13.41, "threat_type": "C2 Server", "severity": "high", "country": "Germany", "isp": "Hetzner", "count": 847, "first_seen": now, "last_seen": now},
            {"id": "ioc-002", "ip": "91.215.85.17", "lat": 55.75, "lon": 37.62, "threat_type": "Botnet", "severity": "high", "country": "Russia", "isp": "HostKey", "count": 1250, "first_seen": now, "last_seen": now},
            {"id": "ioc-003", "ip": "103.145.13.2", "lat": 22.30, "lon": 114.17, "threat_type": "Scanner", "severity": "medium", "country": "Hong Kong", "isp": "HKBN", "count": 320, "first_seen": now, "last_seen": now},
            {"id": "ioc-004", "ip": "45.33.32.156", "lat": 37.77, "lon": -122.42, "threat_type": "Phishing", "severity": "medium", "country": "United States", "isp": "Linode", "count": 156, "first_seen": now, "last_seen": now},
            {"id": "ioc-005", "ip": "177.54.148.50", "lat": -23.55, "lon": -46.63, "threat_type": "Malware Host", "severity": "high", "country": "Brazil", "isp": "GlobeNet", "count": 530, "first_seen": now, "last_seen": now},
            {"id": "ioc-006", "ip": "14.215.177.38", "lat": 23.13, "lon": 113.26, "threat_type": "DDoS Source", "severity": "high", "country": "China", "isp": "ChinaNet", "count": 2100, "first_seen": now, "last_seen": now},
            {"id": "ioc-007", "ip": "196.216.113.5", "lat": -26.20, "lon": 28.04, "threat_type": "Spam Relay", "severity": "low", "country": "South Africa", "isp": "MTN", "count": 89, "first_seen": now, "last_seen": now},
            {"id": "ioc-008", "ip": "203.113.167.42", "lat": 21.03, "lon": 105.85, "threat_type": "Brute Force", "severity": "medium", "country": "Vietnam", "isp": "VNPT", "count": 410, "first_seen": now, "last_seen": now},
        ]

    @staticmethod
    def get_signals() -> list[dict]:
        signals = []
        centers = [
            (48.86, 2.35, "Urban LTE"),
            (40.71, -74.01, "Urban LTE"),
            (35.68, 139.69, "Urban 5G"),
            (51.51, -0.13, "Urban LTE"),
            (-33.87, 151.21, "Urban LTE"),
        ]
        for lat, lon, sig_type in centers:
            for i in range(12):
                angle = (i / 12) * 2 * math.pi
                for r in [0.05, 0.15, 0.3, 0.5]:
                    signals.append({
                        "lat": lat + r * math.sin(angle),
                        "lon": lon + r * math.cos(angle),
                        "intensity": max(0.1, 1.0 - r * 2),
                        "frequency": 2400.0 if "LTE" in sig_type else 3500.0,
                        "signal_type": sig_type,
                    })
        return signals

    @staticmethod
    def get_satellites() -> list[dict]:
        now = datetime.now(UTC).isoformat()
        satellites = []
        configs = [
            ("sat-001", "ISS (ZARYA)", 25544, "LEO", 51.6, 0),
            ("sat-002", "STARLINK-1007", 44713, "LEO", 53.0, 30),
            ("sat-003", "GOES-16", 41866, "GEO", 0.03, 60),
            ("sat-004", "COSMOS 2545", 44850, "LEO", 64.8, 90),
            ("sat-005", "GPS BIIR-2", 28474, "MEO", 55.0, 120),
        ]
        for sat_id, name, norad, orbit_type, inclination, phase_offset in configs:
            path = []
            for step in range(100):
                t = (step / 100) * 2 * math.pi
                lon = ((t + math.radians(phase_offset)) * 180 / math.pi) % 360 - 180
                lat = inclination * math.sin(t)
                alt = 408 if orbit_type == "LEO" else (35786 if orbit_type == "GEO" else 20200)
                path.append([round(lon, 2), round(lat, 2), alt])
            current = path[50]
            satellites.append({
                "id": sat_id,
                "name": name,
                "norad_id": norad,
                "path": path,
                "current_position": current,
                "orbit_type": orbit_type,
                "timestamp": now,
            })
        return satellites

    @staticmethod
    def get_conflicts() -> list[dict]:
        return [
            {
                "id": "cz-001",
                "name": "Eastern Ukraine Conflict Zone",
                "geometry": {
                    "type": "Feature",
                    "properties": {"name": "Eastern Ukraine"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[36.0, 47.0], [40.0, 47.0], [40.0, 50.0], [36.0, 50.0], [36.0, 47.0]]],
                    },
                },
                "severity": "high",
                "event_count": 152,
                "description": "Active conflict zone in eastern Ukraine with ongoing military operations.",
                "events": [
                    {"lat": 48.0, "lon": 37.8, "type": "shelling", "date": "2024-01-15"},
                    {"lat": 48.5, "lon": 38.2, "type": "airstrike", "date": "2024-01-14"},
                    {"lat": 47.8, "lon": 37.5, "type": "ground_combat", "date": "2024-01-13"},
                ],
            },
            {
                "id": "cz-002",
                "name": "Sahel Region Instability",
                "geometry": {
                    "type": "Feature",
                    "properties": {"name": "Sahel"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-5.0, 12.0], [15.0, 12.0], [15.0, 20.0], [-5.0, 20.0], [-5.0, 12.0]]],
                    },
                },
                "severity": "high",
                "event_count": 87,
                "description": "Ongoing insurgency and intercommunal violence across the Sahel region.",
                "events": [
                    {"lat": 14.5, "lon": 2.1, "type": "insurgent_attack", "date": "2024-01-12"},
                    {"lat": 16.0, "lon": -1.5, "type": "military_operation", "date": "2024-01-10"},
                ],
            },
            {
                "id": "cz-003",
                "name": "Myanmar Civil Conflict",
                "geometry": {
                    "type": "Feature",
                    "properties": {"name": "Myanmar"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[92.0, 10.0], [101.0, 10.0], [101.0, 28.0], [92.0, 28.0], [92.0, 10.0]]],
                    },
                },
                "severity": "high",
                "event_count": 64,
                "description": "Widespread civil conflict following military coup.",
                "events": [
                    {"lat": 19.8, "lon": 96.2, "type": "protest", "date": "2024-01-11"},
                    {"lat": 21.0, "lon": 97.5, "type": "armed_clash", "date": "2024-01-09"},
                ],
            },
        ]

    @staticmethod
    def get_entity_links() -> list[dict]:
        return [
            {
                "id": "el-001",
                "source_name": "Moscow HQ",
                "target_name": "Damascus Office",
                "source_position": [37.62, 55.75],
                "target_position": [36.29, 33.51],
                "relationship": "Military Alliance",
                "strength": 0.9,
            },
            {
                "id": "el-002",
                "source_name": "Washington DC",
                "target_name": "London",
                "source_position": [-77.04, 38.91],
                "target_position": [-0.13, 51.51],
                "relationship": "Intelligence Sharing",
                "strength": 0.95,
            },
            {
                "id": "el-003",
                "source_name": "Beijing",
                "target_name": "Islamabad",
                "source_position": [116.40, 39.90],
                "target_position": [73.05, 33.69],
                "relationship": "Economic Corridor",
                "strength": 0.8,
            },
            {
                "id": "el-004",
                "source_name": "Tehran",
                "target_name": "Beirut",
                "source_position": [51.39, 35.69],
                "target_position": [35.50, 33.89],
                "relationship": "Proxy Support",
                "strength": 0.85,
            },
            {
                "id": "el-005",
                "source_name": "Riyadh",
                "target_name": "Abu Dhabi",
                "source_position": [46.72, 24.77],
                "target_position": [54.37, 24.45],
                "relationship": "Coalition Partner",
                "strength": 0.75,
            },
            {
                "id": "el-006",
                "source_name": "Tokyo",
                "target_name": "Seoul",
                "source_position": [139.69, 35.68],
                "target_position": [126.98, 37.57],
                "relationship": "Trade Agreement",
                "strength": 0.7,
            },
        ]
