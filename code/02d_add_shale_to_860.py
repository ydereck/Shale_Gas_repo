#!/usr/bin/env python3
"""
02d_add_shale_to_860.py

Attach county-level shale potential scores (from Bartik's rystad_county.dta)
to the EIA 860 intermediate file with FIPS.

Inputs
------
data_intermediate/EIA_860_with_fips.csv
data_raw/Rystad/rystad_county.dta

Outputs
-------
data_intermediate/EIA_860_with_fips_shale.csv
data_intermediate/EIA_860_with_fips_shale.dta
"""

from pathlib import Path
import pandas as pd


def main():
    # -------------------------------------------------------------
    # 0. Paths relative to repo root
    # -------------------------------------------------------------
    this_file = Path(__file__).resolve()
    repo_root = this_file.parents[1]  # .. from code/ to repo root

    data_int = repo_root / "data_intermediate"
    data_raw = repo_root / "data_raw" / "Rystad"

    eia_path = data_int / "EIA_860_with_fips.csv"
    rystad_path = data_raw / "rystad_county.dta"

    # -------------------------------------------------------------
    # 1. Load data
    # -------------------------------------------------------------
    # Keep FIPS as string to preserve leading zeros
    eia = pd.read_csv(
        eia_path,
        dtype={"FIPS_state_county_5digit": str},
    )

    rystad = pd.read_stata(rystad_path, convert_categoricals=False)

    # -------------------------------------------------------------
    # 2. Clean FIPS & collapse Rystad to county-level index
    # -------------------------------------------------------------
    # Ensure 5-digit string FIPS
    rystad["fips"] = rystad["fips"].astype(str).str.strip().str.zfill(5)

    # Collapse to one row per county:
    #   shale_valScoreW_sum: total shale prospectivity (sum over plays)
    #   shale_valScoreM_max: best (max) prospectivity across plays
    shale_by_county = (
        rystad.groupby("fips", as_index=False)
        .agg(
            shale_valScoreW_sum=("valScoreW", "sum"),
            shale_valScoreM_max=("valScoreM", "max"),
        )
    )

    # -------------------------------------------------------------
    # 3. Merge onto EIA 860 by county FIPS
    # -------------------------------------------------------------
    # Create a clean 5-digit FIPS in the EIA file; uses column created earlier
    eia["fips_5"] = (
        eia["FIPS_state_county_5digit"]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )

    eia_merged = eia.merge(
        shale_by_county,
        left_on="fips_5",
        right_on="fips",
        how="left",
        indicator=True,
    )

    # Diagnostic
    total = len(eia_merged)
    matched = (eia_merged["_merge"] == "both").sum()
    print(f"[EIA-860] Rows with shale match: {matched} of {total} ({matched/total:.1%})")

    # Drop helper columns
    eia_merged = eia_merged.drop(columns=["_merge", "fips"])

    # For counties with no shale plays, set shale potential to 0
    eia_merged["shale_valScoreW_sum"] = eia_merged["shale_valScoreW_sum"].fillna(0.0)
    eia_merged["shale_valScoreM_max"] = eia_merged["shale_valScoreM_max"].fillna(0.0)

    # -------------------------------------------------------------
    # 4. Save outputs
    # -------------------------------------------------------------
    out_csv = data_int / "EIA_860_with_fips_shale.csv"
    eia_merged.to_csv(out_csv, index=False)

    # Save a Stata .dta version (make sure object cols are strings)
    out_dta = data_int / "EIA_860_with_fips_shale.dta"
    obj_cols = eia_merged.select_dtypes(include="object").columns
    eia_merged[obj_cols] = (
        eia_merged[obj_cols]
        .fillna("")
        .astype(str)
    )
    eia_merged.to_stata(out_dta, write_index=False, version=118)

    print(f"[EIA-860] Saved shale-augmented files to:\n  {out_csv}\n  {out_dta}")


if __name__ == "__main__":
    main()
