#!/usr/bin/env python3

import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

import yaml

CONFIG_FILE = "_data/socials.yml"
BIB_FILE = "_bibliography/papers.bib"
OUTPUT_FILE = "_data/citations.yml"
REQUEST_TIMEOUT_SECONDS = 20

# A browser-like UA helps avoid low-quality bot blocks.
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)

FIELD_LINE_PATTERN = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{(.*)\}\s*,?\s*$")
CITATION_PATTERNS = [
    re.compile(r"Cited by\s*([0-9,]+)", re.IGNORECASE),
    re.compile(r"被引用次数\s*([0-9,]+)"),
]
BLOCK_INDICATORS = [
    "unusual traffic",
    "not a robot",
    "detected unusual traffic",
    "our systems have detected",
]


def load_yaml(path: str):
    """Load a YAML file. Return an empty dict when file is missing/empty."""
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data or {}
    except yaml.YAMLError as exc:
        print(f"Error parsing YAML file {path}: {exc}")
        sys.exit(1)


def load_scholar_user_id() -> str:
    """Load scholar_userid from _data/socials.yml."""
    config = load_yaml(CONFIG_FILE)
    scholar_user_id = config.get("scholar_userid")
    if not scholar_user_id:
        print(
            f"No 'scholar_userid' found in {CONFIG_FILE}. "
            "Please add 'scholar_userid: <your_google_scholar_id>'."
        )
        sys.exit(1)
    return scholar_user_id


def parse_bib_publications(bib_file: str):
    """
    Parse papers.bib and return entries with google_scholar_id.

    We only need title/year/google_scholar_id and parse them line-by-line.
    """
    if not os.path.exists(bib_file):
        print(f"Bibliography file not found: {bib_file}")
        sys.exit(1)

    entries = []
    current = None

    with open(bib_file, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line or line == "---":
                continue

            if line.startswith("@"):
                current = {}
                continue

            if current is None:
                continue

            if line in ("}", "},"):
                pub_id = current.get("google_scholar_id")
                if pub_id:
                    entries.append(
                        {
                            "pub_id": pub_id,
                            "title": current.get("title", "Unknown Title"),
                            "year": str(current.get("year", "Unknown Year")),
                        }
                    )
                current = None
                continue

            match = FIELD_LINE_PATTERN.match(line)
            if not match:
                continue

            field_name = match.group(1).strip().lower()
            field_value = match.group(2).strip()
            current[field_name] = field_value

    if not entries:
        print(
            f"No entries with 'google_scholar_id' found in {bib_file}. "
            "Please add google_scholar_id to your publications."
        )
        sys.exit(1)

    return entries


def fetch_html(url: str) -> str:
    """Fetch URL content with explicit timeout and a browser-like user-agent."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="ignore")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc


def parse_citation_count(html: str) -> int:
    """Extract citation count from Google Scholar citation page HTML."""
    for pattern in CITATION_PATTERNS:
        match = pattern.search(html)
        if match:
            return int(match.group(1).replace(",", ""))

    html_lower = html.lower()
    if any(indicator in html_lower for indicator in BLOCK_INDICATORS):
        raise RuntimeError("Google Scholar blocked the request (captcha/rate limit).")

    raise RuntimeError("Citation count not found in response.")


def fetch_single_publication_citations(scholar_user_id: str, pub_id: str) -> int:
    """Fetch citation count for one publication ID."""
    params = urllib.parse.urlencode(
        {
            "view_op": "view_citation",
            "hl": "en",
            "user": scholar_user_id,
            "citation_for_view": f"{scholar_user_id}:{pub_id}",
        }
    )
    url = f"https://scholar.google.com/citations?{params}"
    html = fetch_html(url)
    return parse_citation_count(html)


def get_scholar_citations() -> None:
    """Fetch and update Google Scholar citation data."""
    scholar_user_id = load_scholar_user_id()
    print(f"Fetching citations for Google Scholar ID: {scholar_user_id}")

    existing_data = load_yaml(OUTPUT_FILE)
    existing_papers = existing_data.get("papers", {}) if isinstance(existing_data, dict) else {}
    previous_updated = (
        existing_data.get("metadata", {}).get("last_updated")
        if isinstance(existing_data, dict)
        else None
    )
    if previous_updated:
        print(f"Last updated on: {previous_updated}")

    publications = parse_bib_publications(BIB_FILE)
    citation_data = {"metadata": {"last_updated": datetime.now().strftime("%Y-%m-%d")}, "papers": {}}

    fresh_fetch_count = 0
    fallback_count = 0
    missing_without_cache = []

    for publication in publications:
        pub_id = publication["pub_id"]
        key = f"{scholar_user_id}:{pub_id}"
        title = publication["title"]
        year = publication["year"]

        try:
            citations = fetch_single_publication_citations(scholar_user_id, pub_id)
            fresh_fetch_count += 1
            print(f"Found: {title} ({year}) - Citations: {citations}")
        except Exception as exc:
            cached = existing_papers.get(key)
            if isinstance(cached, dict) and "citations" in cached:
                citations = int(cached["citations"])
                fallback_count += 1
                print(
                    f"Warning: Could not refresh {pub_id}; using cached citations={citations}. "
                    f"Reason: {exc}"
                )
            else:
                missing_without_cache.append(f"{pub_id} ({title}): {exc}")
                print(f"Error: Could not fetch {pub_id} and no cache exists. Reason: {exc}")
                continue

        citation_data["papers"][key] = {
            "title": title,
            "year": year,
            "citations": citations,
        }

    if missing_without_cache:
        print("Failed to fetch citations for entries without cache:")
        for item in missing_without_cache:
            print(f"- {item}")
        sys.exit(1)

    if not citation_data["papers"]:
        print("No citation data could be fetched or recovered from cache.")
        sys.exit(1)

    if fresh_fetch_count == 0 and previous_updated:
        # Keep the previous date when no fresh data was retrieved.
        citation_data["metadata"]["last_updated"] = previous_updated
        print(
            "No fresh citation data fetched this run; "
            f"preserving last_updated={previous_updated}."
        )

    if existing_data and existing_data.get("papers") == citation_data["papers"] and (
        existing_data.get("metadata", {}).get("last_updated")
        == citation_data["metadata"]["last_updated"]
    ):
        print("No changes in citation data. Skipping file update.")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        yaml.dump(citation_data, f, width=1000, sort_keys=True, allow_unicode=False)

    print(
        f"Citation data saved to {OUTPUT_FILE} "
        f"(fresh={fresh_fetch_count}, fallback={fallback_count})."
    )


if __name__ == "__main__":
    try:
        get_scholar_citations()
    except Exception as exc:
        print(f"Unexpected error: {exc}")
        sys.exit(1)
