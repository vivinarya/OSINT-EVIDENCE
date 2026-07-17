from __future__ import annotations
import csv
import io
import json
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter
from .base import BaseTool, ToolResult

GDELT_DIR = Path("datasets/gdelt")

GDELT_COLUMNS = [
    "GlobalEventId", "SqlDate", "MonthYear", "Year", "FractionDate",
    "Actor1Code", "Actor1Name", "Actor1CountryCode", "Actor1KnownGroupCode",
    "Actor1EthnicCode", "Actor1Religion1Code", "Actor1Religion2Code",
    "Actor1Type1Code", "Actor1Type2Code", "Actor1Type3Code",
    "Actor2Code", "Actor2Name", "Actor2CountryCode", "Actor2KnownGroupCode",
    "Actor2EthnicCode", "Actor2Religion1Code", "Actor2Religion2Code",
    "Actor2Type1Code", "Actor2Type2Code", "Actor2Type3Code",
    "IsRootEvent", "EventCode", "EventBaseCode", "EventRootCode",
    "QuadClass", "GoldsteinScale", "NumMentions", "NumSources",
    "NumArticles", "AvgTone", "Actor1GeoType", "Actor1GeoFullName",
    "Actor1GeoCountryCode", "Actor1GeoAdm1Code", "Actor1GeoLat",
    "Actor1GeoLong", "Actor1GeoFeatureId", "Actor2GeoType",
    "Actor2GeoFullName", "Actor2GeoCountryCode", "Actor2GeoAdm1Code",
    "Actor2GeoLat", "Actor2GeoLong", "Actor2GeoFeatureId",
    "ActionGeoType", "ActionGeoFullName", "ActionGeoCountryCode",
    "ActionGeoAdm1Code", "ActionGeoLat", "ActionGeoLong",
    "ActionGeoFeatureId", "DateAdded", "SourceUrl",
]

QUAD_NAMES = {"1": "verbal cooperation", "2": "material cooperation",
              "3": "verbal conflict", "4": "material conflict"}

CAMEO_CONFLICT_CODES = {
    "14": "protest",
    "15": "exhibit force posture",
    "16": "reduce relations",
    "17": "coerce",
    "18": "assault",
    "19": "fight",
    "20": "mass violence",
}

FIPS_AP_COUNTRIES = {
    "AF": "Afghanistan", "AL": "Albania", "AG": "Algeria", "AO": "Angola",
    "IN": "India", "PK": "Pakistan", "CH": "China", "NP": "Nepal",
    "BT": "Bhutan", "BG": "Bangladesh", "BM": "Myanmar",
    "CE": "Sri Lanka", "MV": "Maldives", "ID": "Indonesia",
    "RP": "Philippines", "TH": "Thailand", "VM": "Vietnam",
    "MY": "Malaysia", "SN": "Singapore", "CB": "Cambodia",
    "LA": "Laos", "TT": "Timor-Leste", "AS": "Australia",
    "NZ": "New Zealand", "PP": "Papua New Guinea", "FJ": "Fiji",
    "JA": "Japan", "KS": "South Korea", "KN": "North Korea",
    "TW": "Taiwan", "MG": "Mongolia",
    "KA": "Kazakhstan", "KG": "Kyrgyzstan", "TI": "Tajikistan",
    "TX": "Turkmenistan", "UZ": "Uzbekistan",
}


class GDELTTool(BaseTool):
    name = "gdelt"
    description = "Query GDELT conflict/event data for recent global events"

    async def run(self, params: dict) -> ToolResult:
        country = (params.get("country") or "").upper()
        event_type = params.get("event_type") or ""
        quad_class = params.get("quad_class") or ""
        actor_query = (params.get("actor") or "").lower()
        min_tone = params.get("min_tone") or -100
        max_tone = params.get("max_tone") or 100
        limit = params.get("limit") or 20
        days_back = params.get("days_back") or 3

        today = datetime.utcnow()
        dates = [(today - timedelta(days=d)).strftime("%Y%m%d") for d in range(1, days_back + 1)]

        results = []
        for date_str in dates:
            path = GDELT_DIR / f"{date_str}.export.CSV.zip"
            if not path.exists():
                continue
            with zipfile.ZipFile(path) as z:
                name = z.namelist()[0]
                with z.open(name) as f:
                    reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t")
                    for row in reader:
                        if len(row) < 58:
                            continue

                        quad = row[29]
                        action_country = row[51].strip()

                        matches = True
                        if country and action_country != country:
                            matches = False
                        if quad_class and quad != quad_class:
                            matches = False
                        if event_type:
                            ec = row[26].strip()
                            if not any(ec.startswith(c) for c in CAMEO_CONFLICT_CODES):
                                matches = False
                        if actor_query:
                            a1 = (row[5] or "").lower()
                            a2 = (row[15] or "").lower()
                            n1 = (row[6] or "").lower()
                            n2 = (row[16] or "").lower()
                            if not any(actor_query in x for x in [a1, a2, n1, n2]):
                                matches = False
                        tone = float(row[34]) if row[34] else 0
                        if tone < min_tone or tone > max_tone:
                            matches = False

                        if matches:
                            entry = {GDELT_COLUMNS[i]: row[i] for i in range(min(len(row), 58))}
                            results.append(entry)
                            if len(results) >= limit:
                                break

        if not results:
            return ToolResult(success=False, error=f"No matching GDELT events found for the query")

        countries = Counter(r.get("ActionGeoCountryCode", "") for r in results)
        quads = Counter(r.get("QuadClass", "") for r in results)

        lines = [f"Found {len(results)} GDELT events:"]
        lines.append(f"  Countries: {dict(countries.most_common(5))}")
        lines.append(f"  QuadClasses: {dict(quads)}")
        for r in results[:10]:
            a1 = r.get("Actor1Name", "") or r.get("Actor1Code", "")
            a2 = r.get("Actor2Name", "") or r.get("Actor2Code", "")
            loc = r.get("ActionGeoFullName", "")
            tone_v = r.get("AvgTone", "")
            ec = r.get("EventCode", "")
            quad_name = QUAD_NAMES.get(r.get("QuadClass", ""), "")
            lines.append(f"  {a1} -> {a2} [{ec}/{quad_name}] @ {loc} tone={tone_v}")

        return ToolResult(
            success=True,
            data=results,
            source_type="gdelt_event_database",
            source_url="https://www.gdeltproject.org/",
            title=f"GDELT: {country or actor_query or event_type or 'recent events'}",
            snippet="\n".join(lines),
            raw_text=json.dumps(results, indent=2),
        )
