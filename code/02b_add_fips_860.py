#!/usr/bin/env python3
"""
02b_add_fips.py

Merge 5-digit county FIPS codes onto the intermediate EIA 860 file
(EIA_860_with_loc.csv) by state name and county name.

Inputs
------
data_intermediate/EIA_860_with_loc.csv
data_intermediate/fips_state_codes.csv
data_intermediate/fips_county_codes_2007.csv

Outputs
-------
data_intermediate/EIA_860_with_fips.csv
data_intermediate/EIA_860_with_fips.dta
"""

from pathlib import Path
import pandas as pd


def main():
    # ------------------------------------------------------------------
    # 0. Set up paths relative to this script (repo-root independent)
    # ------------------------------------------------------------------
    this_file = Path(__file__).resolve()
    repo_root = this_file.parents[1]           # .. from code/ to repo root

    data_int = repo_root / "data_intermediate"

    eia_path = data_int / "EIA_860_with_loc.csv"
    state_path = data_int / "fips_state_codes.csv"
    county_path = data_int / "fips_county_codes_2007.csv"

    # ------------------------------------------------------------------
    # 1. Load data
    # ------------------------------------------------------------------
    # Keep codes as strings to preserve leading zeros
    eia = pd.read_csv(eia_path, dtype={"State": str, "County": str})
    state = pd.read_csv(state_path, dtype=str)
    county = pd.read_csv(county_path, dtype=str)

    # ------------------------------------------------------------------
    # 2. Standardize state & county names (upper-case, trimmed)
    # ------------------------------------------------------------------
    def clean_name(s: pd.Series) -> pd.Series:
        return s.str.upper().str.strip()

    # EIA names
    eia["state_clean"] = clean_name(eia["State"])
    eia["county_clean"] = clean_name(eia["County"])

    # State crosswalk
    # Expect columns: govs_state_code, state_name, fips_state_code
    state["state_clean"] = clean_name(state["state_name"])

    # County crosswalk
    # Expect columns: govs_state_code, govs_county_code, county_name,
    #                 fips_state_code, fips_county_2002, fips_county_2007,
    #                 fips_state_county_2007
    # Attach state name to county table via govs/fips state code
    county_full = county.merge(
        state[["govs_state_code", "state_name", "fips_state_code", "state_clean"]],
        on=["govs_state_code", "fips_state_code"],
        how="left",
        validate="m:1"
    )

    county_full["county_clean"] = clean_name(county_full["county_name"])

    # ------------------------------------------------------------------
    # 3. Merge EIA with county FIPS by (state_clean, county_clean)
    # ------------------------------------------------------------------
    merge_cols = [
        "state_clean",
        "county_clean",
        "fips_state_code",
        "fips_county_2007",
        "fips_state_county_2007",
    ]

    eia_merged = eia.merge(
        county_full[merge_cols],
        on=["state_clean", "county_clean"],
        how="left",
        indicator=True,
    )

    # Optional: quick diagnostics printed to console
    total = len(eia_merged)
    matched = (eia_merged["_merge"] == "both").sum()
    print(f"Matched rows: {matched} of {total} ({matched/total:.1%})")

    # You can uncomment this to inspect problem cases:
    # unmatched = eia_merged[eia_merged["_merge"] != "both"]
    # unmatched.to_csv(data_int / "EIA_860_fips_unmatched_debug.csv", index=False)

    # ------------------------------------------------------------------
    # 4. Tidy up and save outputs
    # ------------------------------------------------------------------
    # Rename final FIPS columns to something intuitive
    eia_merged = eia_merged.drop(columns=["_merge"])
    eia_merged = eia_merged.rename(
        columns={
            "fips_state_code": "FIPS_state",
            "fips_county_2007": "FIPS_county",
            "fips_state_county_2007": "FIPS_state_county_5digit",
        }
    )

    # Save CSV
    out_csv = data_int / "EIA_860_with_fips.csv"
    eia_merged.to_csv(out_csv, index=False)

    # Also save a Stata .dta file for convenience
    out_dta = data_int / "EIA_860_with_fips.dta"
    eia_merged.to_stata(out_dta, write_index=False, version=118)

    print(f"Saved with FIPS to:\n  {out_csv}\n  {out_dta}")


if __name__ == "__main__":
    main()
