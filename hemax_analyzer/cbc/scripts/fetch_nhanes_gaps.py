#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests


@dataclass(frozen=True)
class NhanesFile:
    cycle_dir: str
    component: str
    table: str
    xpt_name: str
    cdc_year: str
    why: str

    @property
    def url(self) -> str:
        return f"https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{self.cdc_year}/DataFiles/{self.xpt_name}"


GAPS: list[NhanesFile] = [
    NhanesFile(
        cycle_dir="2017-2020", component="examination",
        table="P_BPXO", xpt_name="P_BPXO.xpt", cdc_year="2017",
        why="Oscillometric BP for 2017-2020 (~13k people). Replaces auscultatory BPX which was discontinued after 2017-2018.",
    ),
    NhanesFile(
        cycle_dir="2017-2020", component="laboratory",
        table="P_VID", xpt_name="P_VID.xpt", cdc_year="2017",
        why="25-hydroxy Vitamin D for 2017-2020.",
    ),
    NhanesFile(
        cycle_dir="2017-2020", component="laboratory",
        table="P_APOB", xpt_name="P_APOB.xpt", cdc_year="2017",
        why="Apolipoprotein B (fasting subsample, ~3k people).",
    ),
]



def _download_xpt(url: str, timeout: int = 120) -> bytes:
    headers = {"User-Agent": "hemax-nhanes-fetch/1.0 (+diploma project)"}
    r = requests.get(url, headers=headers, timeout=timeout)
    if r.status_code == 404:
        raise FileNotFoundError(f"CDC returned 404 for {url}. File may not exist.")
    r.raise_for_status()
    return r.content


def _xpt_to_csv(xpt_bytes: bytes, csv_path: Path) -> tuple[int, int]:
    df = pd.read_sas(io.BytesIO(xpt_bytes), format="xport")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    return len(df), df.shape[1]


def fetch_one(f: NhanesFile, csv_root: Path, force: bool) -> str:
    csv_path = csv_root / f.cycle_dir / f.component / f"{f.table}.csv"
    if csv_path.exists() and not force:
        return f"SKIP  {csv_path}  (already present; use --force to overwrite)"

    try:
        data = _download_xpt(f.url)
        rows, cols = _xpt_to_csv(data, csv_path)
        return f"OK    {csv_path}  ({rows} rows × {cols} cols)  ← {f.url}"
    except FileNotFoundError as e:
        return f"MISS  {f.url}  (not on CDC right now)"
    except Exception as e:
        return f"ERR   {f.url}  → {type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv-root", type=Path, required=True,
                    help="Root of your local NHANES CSV mirror (contains 1999-2000, 2001-2002, ...).")
    ap.add_argument("--only", nargs="*", default=None,
                    help="Download only these tables (e.g. --only P_BPXO P_VID).")
    ap.add_argument("--force", action="store_true",
                    help="Re-download even if the CSV already exists locally.")
    ap.add_argument("--delay", type=float, default=0.5,
                    help="Polite delay in seconds between requests.")
    args = ap.parse_args()

    if not args.csv_root.is_dir():
        sys.exit(f"--csv-root does not exist or is not a directory: {args.csv_root}")

    targets = GAPS
    if args.only:
        wanted = set(args.only)
        targets = [f for f in GAPS if f.table in wanted]
        if not targets:
            sys.exit(f"None of the requested tables are registered in GAPS: {args.only}")

    print(f"NHANES gap-fill → {args.csv_root.resolve()}")
    print(f"Targets: {len(targets)}")
    print("-" * 72)
    for f in targets:
        print(f"[{f.table}] {f.why}")
        msg = fetch_one(f, args.csv_root, args.force)
        print(f"  {msg}")
        time.sleep(args.delay)
    print("-" * 72)
    print("Done.")


if __name__ == "__main__":
    main()
