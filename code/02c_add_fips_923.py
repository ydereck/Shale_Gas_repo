#!/usr/bin/env python3
"""
02c_add_fips_923.py

Merge 5-digit county FIPS codes onto the intermediate EIA 923 file
(EIA_923_with_loc.csv) by state name and county name.

Inputs
------
data_intermediate/EIA_923_with_loc.csv
data_intermediate/fips_state_codes.csv
data_intermediate/fips_county_codes_2007.csv

Outputs
-------
data_intermediate/EIA_923_with_fips.csv
data_intermediate/EIA_923_with_fips.dta
"""

from pathlib import Path
import pandas as pd


def clean_name(s: pd.Series) -> pd.Series:
    """Uppercase + strip whitespace for name matching."""
    return s.astype(str).str.upper().str.strip()


def main():
    # ------------------------------------------------------------------
    # 0. Set up paths relative to this script (repo-root independent)
    # ------------------------------------------------------------------
    this_file = Path(__file__).resolve()
    repo_root = this_file.parents[1]  # .. from code/ to repo root

    data_int = repo_root / "data_intermediate"

    eia923_path = data_int / "EIA_923_with_loc.csv"
    state_path = data_int / "fips_state_codes.csv"
    county_path = data_int / "fips_county_codes_2007.csv"

    # ------------------------------------------------------------------
    # 1. Load data
    # ------------------------------------------------------------------
    # We only need to force State/County to string here; everything else can be inferred.
    eia923 = pd.read_csv(
        eia923_path,
        dtype={"State": str, "County": str},
    )

    state = pd.read_csv(state_path, dtype=str)
    county = pd.read_csv(county_path, dtype=str)

    # ------------------------------------------------------------------
    # 2. Standardize state & county names
    # ------------------------------------------------------------------
    # EIA-923 names
    eia923["state_clean"] = clean_name(eia923["State"])
    eia923["county_clean"] = clean_name(eia923["County"])

    # State crosswalk: expect columns govs_state_code, state_name, fips_state_code
    state["state_clean"] = clean_name(state["state_name"])

    # County crosswalk: add state name + clean county name
    county_full = county.merge(
        state[["govs_state_code", "state_name", "fips_state_code", "state_clean"]],
        on=["govs_state_code", "fips_state_code"],
        how="left",
        validate="m:1",
    )
    county_full["county_clean"] = clean_name(county_full["county_name"])

    # ------------------------------------------------------------------
    # 3. Merge EIA-923 with county FIPS by (state_clean, county_clean)
    # ------------------------------------------------------------------
    merge_cols = [
        "state_clean",
        "county_clean",
        "fips_state_code",
        "fips_county_2007",
        "fips_state_county_2007",
    ]

    eia923_merged = eia923.merge(
        county_full[merge_cols],
        on=["state_clean", "county_clean"],
        how="left",
        indicator=True,
    )

    # Quick diagnostics
    total = len(eia923_merged)
    matched = (eia923_merged["_merge"] == "both").sum()
    print(f"[EIA-923] Matched rows: {matched} of {total} ({matched/total:.1%})")

    # Uncomment if you want a debug file of unmatched rows:
    # unmatched_923 = eia923_merged[eia923_merged["_merge"] != "both"]
    # unmatched_923.to_csv(data_int / "EIA_923_fips_unmatched_debug.csv", index=False)

    # ------------------------------------------------------------------
    # 4. Clean up and save outputs
    # ------------------------------------------------------------------
    eia923_merged = eia923_merged.drop(columns=["_merge"])

    # Rename FIPS cols to something intuitive
    eia923_merged = eia923_merged.rename(
        columns={
            "fips_state_code": "FIPS_state",
            "fips_county_2007": "FIPS_county",
            "fips_state_county_2007": "FIPS_state_county_5digit",
        }
    )

    # Save CSV
    out_csv = data_int / "EIA_923_with_fips.csv"
    eia923_merged.to_csv(out_csv, index=False)

    # Save Stata .dta
    out_dta = data_int / "EIA_923_with_fips.dta"

    # Convert all object columns to pure strings
    obj_cols = eia923_merged.select_dtypes(include="object").columns
    eia923_merged[obj_cols] = (
        eia923_merged[obj_cols]
        .fillna("")   # None/NaN → empty string
        .astype(str)
    )

    eia923_merged.to_stata(out_dta, write_index=False, version=118)


    print(f"[EIA-923] Saved with FIPS to:\n  {out_csv}\n  {out_dta}")


if __name__ == "__main__":
    main()
