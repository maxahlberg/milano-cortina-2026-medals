#!/usr/bin/env python3
"""Fetch latest 2026 Winter Olympics medal data and update the site."""

import json
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone

# EU member states (IOC codes)
EU_CODES = {
    "AUT", "BEL", "BUL", "CRO", "CYP", "CZE", "DEN", "EST", "FIN",
    "FRA", "GER", "GRE", "HUN", "IRL", "ITA", "LAT", "LTU", "LUX",
    "MLT", "NED", "POL", "POR", "ROU", "SVK", "SLO", "ESP", "SWE",
    # Alternative codes used by some sources
    "LVA", "BGR",
}

# Population data (approximate 2025-2026)
POPULATIONS = {
    "NOR": 5500000, "ITA": 58900000, "USA": 335000000, "JPN": 123000000,
    "FRA": 68200000, "GER": 84500000, "AUT": 9200000, "SWE": 10500000,
    "NED": 17900000, "SUI": 9000000, "CAN": 40100000, "AUS": 26500000,
    "KOR": 51700000, "CZE": 10900000, "SLO": 2100000, "CHN": 1410000000,
    "GBR": 67800000, "FIN": 5600000, "BUL": 6500000, "POL": 36800000,
    "LVA": 1800000, "NZL": 5200000, "KAZ": 19800000, "BRA": 216000000,
    "BEL": 11700000, "ESP": 47800000, "CRO": 3800000, "DEN": 5900000,
    "EST": 1300000, "GRE": 10400000, "HUN": 9600000, "IRL": 5100000,
    "LTU": 2800000, "ROU": 19000000, "SVK": 5400000, "POR": 10300000,
    "UKR": 37000000, "BLR": 9200000, "GEO": 3700000, "ARM": 2800000,
    "UZB": 35600000, "MGL": 3400000, "IND": 1430000000, "THA": 72000000,
    "COL": 52000000, "ARG": 46000000, "MEX": 130000000, "JAM": 2800000,
    "ISR": 9800000, "TUR": 85000000, "SRB": 6600000, "AND": 80000,
    "ALB": 2800000, "RUS": 144000000, "AZE": 10200000, "ISL": 380000,
    "MKD": 1800000, "MNE": 620000, "BIH": 3200000, "CYP": 1200000,
    "LUX": 660000, "MLT": 520000, "LAT": 1800000,
}

# IOC code to flag emoji mapping
FLAGS = {
    "NOR": "\U0001F1F3\U0001F1F4", "ITA": "\U0001F1EE\U0001F1F9",
    "USA": "\U0001F1FA\U0001F1F8", "JPN": "\U0001F1EF\U0001F1F5",
    "FRA": "\U0001F1EB\U0001F1F7", "GER": "\U0001F1E9\U0001F1EA",
    "AUT": "\U0001F1E6\U0001F1F9", "SWE": "\U0001F1F8\U0001F1EA",
    "NED": "\U0001F1F3\U0001F1F1", "SUI": "\U0001F1E8\U0001F1ED",
    "CAN": "\U0001F1E8\U0001F1E6", "AUS": "\U0001F1E6\U0001F1FA",
    "KOR": "\U0001F1F0\U0001F1F7", "CZE": "\U0001F1E8\U0001F1FF",
    "SLO": "\U0001F1F8\U0001F1EE", "CHN": "\U0001F1E8\U0001F1F3",
    "GBR": "\U0001F1EC\U0001F1E7", "FIN": "\U0001F1EB\U0001F1EE",
    "BUL": "\U0001F1E7\U0001F1EC", "POL": "\U0001F1F5\U0001F1F1",
    "LVA": "\U0001F1F1\U0001F1FB", "NZL": "\U0001F1F3\U0001F1FF",
    "KAZ": "\U0001F1F0\U0001F1FF", "BRA": "\U0001F1E7\U0001F1F7",
    "BEL": "\U0001F1E7\U0001F1EA", "ESP": "\U0001F1EA\U0001F1F8",
    "CRO": "\U0001F1ED\U0001F1F7", "DEN": "\U0001F1E9\U0001F1F0",
    "EST": "\U0001F1EA\U0001F1EA", "GRE": "\U0001F1EC\U0001F1F7",
    "HUN": "\U0001F1ED\U0001F1FA", "IRL": "\U0001F1EE\U0001F1EA",
    "LTU": "\U0001F1F1\U0001F1F9", "ROU": "\U0001F1F7\U0001F1F4",
    "SVK": "\U0001F1F8\U0001F1F0", "POR": "\U0001F1F5\U0001F1F9",
    "UKR": "\U0001F1FA\U0001F1E6", "BLR": "\U0001F1E7\U0001F1FE",
    "GEO": "\U0001F1EC\U0001F1EA", "ARM": "\U0001F1E6\U0001F1F2",
    "ISR": "\U0001F1EE\U0001F1F1", "TUR": "\U0001F1F9\U0001F1F7",
    "SRB": "\U0001F1F7\U0001F1F8", "ISL": "\U0001F1EE\U0001F1F8",
    "LAT": "\U0001F1F1\U0001F1FB", "MKD": "\U0001F1F2\U0001F1F0",
}

# Normalize IOC codes (some sources use different codes)
CODE_ALIASES = {
    "LAT": "LVA",  # Latvia
    "BGR": "BUL",  # Bulgaria
}


def fetch_wikipedia_medals():
    """Fetch medal table from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table"
    req = urllib.request.Request(url, headers={"User-Agent": "MedalTableBot/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"Wikipedia fetch failed: {e}")
        return None, html if 'html' in dir() else None

    countries = []
    # Find the medal table - wikitable class
    table_match = re.search(
        r'<table[^>]*class="[^"]*wikitable[^"]*"[^>]*>(.*?)</table>',
        html, re.DOTALL
    )
    if not table_match:
        print("Could not find medal table on Wikipedia")
        return None, html

    table_html = table_match.group(1)

    # Parse rows - Wikipedia uses <th> for country cells and <td> for numbers
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)

    for row in rows:
        # Extract country name: pattern is "Country_at_the_2026_Winter_Olympics">CountryName</a>
        name_match = re.search(
            r'title="[^"]*at the 2026 Winter Olympics">([^<]+)</a>',
            row
        )
        if not name_match:
            continue

        country_name = name_match.group(1).strip().rstrip("*")

        # Extract medal counts - all <td> cells with just a number
        nums = re.findall(r'<td[^>]*>\s*(\d+)\s*</td>', row)
        if len(nums) < 4:
            # First number might be rank in a <td>
            continue

        # Nums should be: [rank, gold, silver, bronze, total] or [gold, silver, bronze, total]
        # Check if first num could be a rank (matches position in table)
        if len(nums) == 5:
            gold, silver, bronze, total = int(nums[1]), int(nums[2]), int(nums[3]), int(nums[4])
        else:
            gold, silver, bronze, total = int(nums[0]), int(nums[1]), int(nums[2]), int(nums[3])

        if total == 0:
            continue

        # Look up IOC code from country name
        # Handle name variants
        name_variants = {
            "Czech Republic": "CZE", "Republic of Korea": "KOR",
            "People's Republic of China": "CHN", "ROC": "RUS",
            "Great Britain": "GBR", "Chinese Taipei": "TPE",
        }
        code = name_variants.get(country_name, "")

        if not code:
            for c, n in COUNTRY_NAMES.items():
                if n == country_name:
                    code = c
                    break

        if not code:
            for c, n in COUNTRY_NAMES.items():
                if country_name.lower() in n.lower() or n.lower() in country_name.lower():
                    code = c
                    break

        if not code:
            print(f"  Warning: no IOC code for '{country_name}', skipping")
            continue

        # Normalize code
        normalized_code = CODE_ALIASES.get(code, code)

        countries.append({
            "name": country_name,
            "code": normalized_code,
            "gold": gold,
            "silver": silver,
            "bronze": bronze,
            "total": total,
        })

    return countries if countries else None, html


# Friendly country names
COUNTRY_NAMES = {
    "NOR": "Norway", "ITA": "Italy", "USA": "United States", "JPN": "Japan",
    "FRA": "France", "GER": "Germany", "AUT": "Austria", "SWE": "Sweden",
    "NED": "Netherlands", "SUI": "Switzerland", "CAN": "Canada",
    "AUS": "Australia", "KOR": "South Korea", "CZE": "Czechia", "CZR": "Czech Republic",
    "SLO": "Slovenia", "CHN": "China", "GBR": "Great Britain",
    "FIN": "Finland", "BUL": "Bulgaria", "POL": "Poland", "LVA": "Latvia",
    "NZL": "New Zealand", "KAZ": "Kazakhstan", "BRA": "Brazil",
    "BEL": "Belgium", "ESP": "Spain", "CRO": "Croatia", "DEN": "Denmark",
    "EST": "Estonia", "GRE": "Greece", "HUN": "Hungary", "IRL": "Ireland",
    "LTU": "Lithuania", "ROU": "Romania", "SVK": "Slovakia", "POR": "Portugal",
    "UKR": "Ukraine", "BLR": "Belarus", "GEO": "Georgia", "ARM": "Armenia",
    "ISR": "Israel", "TUR": "Turkey", "SRB": "Serbia", "ISL": "Iceland",
    "LAT": "Latvia", "MKD": "North Macedonia",
}


def fetch_medals_from_search():
    """Fallback: try fetching from a news/results API."""
    url = "https://www.sportshistori.com/2026/02/2026-winter-olympics-medal-table-live-standing-results-winners.html"
    req = urllib.request.Request(url, headers={"User-Agent": "MedalTableBot/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"Fallback fetch failed: {e}")
        return None

    countries = []
    # Try to parse table rows
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)

    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        if len(cells) < 5:
            continue

        # Try to extract country name and medal counts
        name_cell = re.sub(r'<[^>]+>', '', cells[1] if len(cells) > 1 else '').strip()
        nums = []
        for cell in cells:
            clean = re.sub(r'<[^>]+>', '', cell).strip()
            if clean.isdigit():
                nums.append(int(clean))

        if len(nums) >= 4 and name_cell:
            countries.append({
                "name": name_cell,
                "code": "",
                "gold": nums[0],
                "silver": nums[1],
                "bronze": nums[2],
                "total": nums[3],
            })

    return countries if countries else None


def enrich_country(c):
    """Add population, flag, EU status, and clean up names."""
    code = c["code"]

    # Fix name if it's just a code
    if code in COUNTRY_NAMES:
        if len(c["name"]) <= 3 or c["name"].isupper():
            c["name"] = COUNTRY_NAMES[code]

    # Add population
    c["population"] = POPULATIONS.get(code, 10000000)

    # Add flag
    c["flag"] = FLAGS.get(code, "")

    # Add EU status
    c["isEU"] = code in EU_CODES

    return c


def count_events_from_html(html):
    """Try to extract how many events have been completed."""
    # Look for patterns like "X of 116" or "X/116"
    match = re.search(r'(\d+)\s*(?:of|/)\s*116', html)
    if match:
        return int(match.group(1))
    return None


def update_html(countries_data, events_completed):
    """Update the index.html with fresh data."""
    with open("index.html", "r") as f:
        html = f.read()

    # Build the JS countries array
    js_entries = []
    for c in countries_data:
        flag_escaped = c.get("flag", "").encode("unicode_escape").decode("ascii")
        # Convert \UXXXXXXXX to \u{XXXXXXXX} format for JS
        flag_js = ""
        if c.get("flag"):
            codepoints = [f"\\u{{{ord(ch):X}}}" for ch in c["flag"]]
            flag_js = "".join(codepoints)

        is_eu = "true" if c.get("isEU") else "false"
        js_entries.append(
            f'  {{ name:"{c["name"]}", code:"{c["code"]}", flag:"{flag_js}", '
            f'gold:{c["gold"]}, silver:{c["silver"]}, bronze:{c["bronze"]}, '
            f'total:{c["total"]}, population:{c["population"]}, isEU:{is_eu} }}'
        )

    new_array = "const countries = [\n" + ",\n".join(js_entries) + "\n];"

    # Replace the countries array in HTML
    # Use string find/replace instead of re.sub to avoid unicode escape issues
    start_marker = "const countries = ["
    end_marker = "];"
    start_idx = html.index(start_marker)
    # Find the matching end - scan for "];" after the array
    depth = 0
    i = start_idx + len(start_marker)
    while i < len(html):
        if html[i] == '[':
            depth += 1
        elif html[i] == ']':
            if depth == 0:
                end_idx = i + 2  # include "];"
                break
            depth -= 1
        i += 1

    html = html[:start_idx] + new_array + html[end_idx:]

    # Update the events count in the subtitle
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%b %d, %Y")  # e.g. "Feb 16, 2026"

    if events_completed:
        html = re.sub(
            r'(\d+) of 116 events',
            f'{events_completed} of 116 events',
            html
        )

    html = re.sub(
        r'Feb \d+, 2026',
        date_str.replace(" 0", " "),  # Remove leading zero from day
        html
    )

    with open("index.html", "w") as f:
        f.write(html)

    # Also update the JSON data file
    json_data = {
        "lastUpdated": now.strftime("%Y-%m-%d"),
        "source": "wikipedia.org, olympics.com",
        "eventsCompleted": f"{events_completed or '?'} of 116",
        "countries": countries_data,
    }
    with open("olympics_data.json", "w") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    print(f"Updated {len(countries_data)} countries, {events_completed or '?'}/116 events")


def main():
    print(f"Fetching medal data at {datetime.now(timezone.utc).isoformat()}")

    # Try Wikipedia first
    countries, wiki_html = fetch_wikipedia_medals()
    events_completed = None

    if countries:
        print(f"Wikipedia: found {len(countries)} countries")
        if wiki_html:
            events_completed = count_events_from_html(wiki_html)
    else:
        print("Wikipedia failed, trying fallback...")
        countries = fetch_medals_from_search()

    if not countries:
        print("ERROR: Could not fetch medal data from any source")
        return

    # Enrich with population, flags, EU status
    countries = [enrich_country(c) for c in countries]

    # Sort by gold (then silver, then bronze)
    countries.sort(key=lambda c: (-c["gold"], -c["silver"], -c["bronze"]))

    update_html(countries, events_completed)
    print("Done!")


if __name__ == "__main__":
    main()
