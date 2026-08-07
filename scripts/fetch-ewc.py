#!/usr/bin/env python3
"""Cache EWC 2026 (OpenDota league 19785) match payloads.

This script only fetches data. Statistical processing lives in process-data.py.
Existing JSON files are reused unless the corresponding refresh flag is set.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEAGUE_ID = 19785
DEFAULT_API_BASE = "https://api.opendota.com/api"
DEFAULT_RAW_DIR = ROOT / "data" / "raw"


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temporary.replace(path)


def api_url(base: str, route: str, api_key: str | None) -> str:
    url = f"{base.rstrip('/')}/{route.lstrip('/')}"
    if api_key:
        url = f"{url}?{urllib.parse.urlencode({'api_key': api_key})}"
    return url


def get_json(url: str, retries: int, timeout: float) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "ti15-ewc-stats/0.2"})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            retryable = error.code == 429 or error.code >= 500
            if not retryable or attempt == retries:
                raise RuntimeError(f"OpenDota returned HTTP {error.code} for {url}") from error
        except urllib.error.URLError as error:
            if attempt == retries:
                raise RuntimeError(f"Could not reach OpenDota for {url}: {error.reason}") from error
        time.sleep(2**attempt)
    raise AssertionError("retry loop ended unexpectedly")


def league_match_ids(
    raw_dir: Path,
    api_base: str,
    api_key: str | None,
    refresh: bool,
    retries: int,
    timeout: float,
) -> list[int]:
    cache = raw_dir / "league_19785_matches.json"
    if refresh or not cache.exists():
        payload = get_json(api_url(api_base, f"leagues/{LEAGUE_ID}/matches", api_key), retries, timeout)
        if not isinstance(payload, list):
            raise RuntimeError("OpenDota league endpoint did not return an array.")
        write_json(cache, payload)
    else:
        payload = read_json(cache)
    match_ids = sorted(
        {
            int(row["match_id"])
            for row in payload
            if isinstance(row, dict) and isinstance(row.get("match_id"), int)
        }
    )
    if not match_ids:
        raise RuntimeError(f"No match IDs found for league {LEAGUE_ID}.")
    return match_ids


def choose_matches(match_ids: list[int], sample_size: int | None, seed: int) -> list[int]:
    if sample_size is None:
        return match_ids
    if sample_size < 1:
        raise ValueError("--sample-size must be at least 1.")
    if sample_size > len(match_ids):
        raise ValueError(f"--sample-size {sample_size} exceeds the {len(match_ids)} league matches.")
    return sorted(random.Random(seed).sample(match_ids, sample_size))


def fetch_matches(
    match_ids: list[int],
    raw_dir: Path,
    api_base: str,
    api_key: str | None,
    refresh: bool,
    delay: float,
    retries: int,
    timeout: float,
) -> tuple[int, int]:
    matches_dir = raw_dir / "matches"
    matches_dir.mkdir(parents=True, exist_ok=True)
    fetched = 0
    reused = 0
    for index, match_id in enumerate(match_ids, start=1):
        destination = matches_dir / f"{match_id}.json"
        if destination.exists() and not refresh:
            payload = read_json(destination)
            if isinstance(payload, dict) and payload.get("match_id") == match_id:
                reused += 1
                print(f"[{index}/{len(match_ids)}] cached  {match_id}")
                continue
        payload = get_json(api_url(api_base, f"matches/{match_id}", api_key), retries, timeout)
        if not isinstance(payload, dict) or payload.get("match_id") != match_id:
            raise RuntimeError(f"Unexpected match payload for {match_id}.")
        write_json(destination, payload)
        fetched += 1
        print(f"[{index}/{len(match_ids)}] fetched {match_id}")
        if index < len(match_ids) and delay > 0:
            time.sleep(delay)
    return fetched, reused


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    result.add_argument("--api-base", default=DEFAULT_API_BASE)
    result.add_argument("--api-key", default=os.environ.get("OPENDOTA_API_KEY"))
    result.add_argument("--refresh-league", action="store_true")
    result.add_argument("--refresh-matches", action="store_true")
    result.add_argument("--sample-size", type=int, help="Randomly fetch N league matches for auditing.")
    result.add_argument("--seed", type=int, default=20260807)
    result.add_argument("--delay", type=float, default=0.25)
    result.add_argument("--retries", type=int, default=3)
    result.add_argument("--timeout", type=float, default=45.0)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        all_ids = league_match_ids(
            args.raw_dir,
            args.api_base,
            args.api_key,
            args.refresh_league,
            args.retries,
            args.timeout,
        )
        selected = choose_matches(all_ids, args.sample_size, args.seed)
        fetched, reused = fetch_matches(
            selected,
            args.raw_dir,
            args.api_base,
            args.api_key,
            args.refresh_matches,
            args.delay,
            args.retries,
            args.timeout,
        )
        print(
            f"League {LEAGUE_ID}: discovered={len(all_ids)}, selected={len(selected)}, "
            f"fetched={fetched}, cached={reused}"
        )
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
