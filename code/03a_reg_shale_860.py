#!/usr/bin/env python3
"""
03a_reg_shale_860.py

County-year regressions of capacity on shale potential using
EIA_860_with_fips_shale.csv.

- Builds coal / gas / RE (wind+solar) capacity at county-year level
- Normalizes shale_valScoreW_sum via log(1 + x)
- Runs regressions:
    cap_coal_ct, cap_ng_ct, cap_re_ct
  on shale_index * post + shale_index + post + county FE + year FE
  with SEs clustered by county.

Prints a compact summary table of the coefficient on shale_post only.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def main():
    # ---------------------------------------------------------
    # 0. Paths
    # ---------------------------------------------------------
    this_file = Path(__file__).resolve()
    repo_root = this_file.parents[1]  # .. from code/ to repo root

    data_int = repo_root / "data_intermediate"
    eia_path = data_int / "EIA_860_with_fips_shale.csv"

    # ---------------------------------------------------------
    # 1. Load plant-level data
    # ---------------------------------------------------------
    df = pd.read_csv(
        eia_path,
        dtype={
            "FIPS_state_county_5digit": str,
            "year": int,
        },
    )

    # ---------------------------------------------------------
    # 2. Build county-year panel & capacity by fuel
    # ---------------------------------------------------------
    # Make sure 5-digit FIPS is clean
    df["fips_5"] = (
        df["FIPS_state_county_5digit"]
        .astype(str)
        .str.strip()
        .str.zfill(5)
    )

    # ---- Map capacity sources ----
    # Using your coauthor's naming:
    # 1 = coal, 3 = natural gas, 4 = wind, 5 = solar
    coal_col = "capacity source 1"
    ng_col   = "capacity source 3"
    wind_col = "capacity source 4"
    solar_col = "capacity source 5"

    for c in [coal_col, ng_col, wind_col, solar_col]:
        if c not in df.columns:
            raise KeyError(f"Expected column '{c}' not found in {eia_path.name}")

    # County-year aggregation: sum capacities, take max shale score (same within county)
    group_cols = ["fips_5", "year"]

    agg_dict = {
        coal_col: "sum",
        ng_col: "sum",
        wind_col: "sum",
        solar_col: "sum",
        "shale_valScoreW_sum": "max",  # constant per county
        "shale_valScoreM_max": "max",
    }

    cty = df.groupby(group_cols, as_index=False).agg(agg_dict)

    # Rename capacities
    cty = cty.rename(
        columns={
            coal_col: "cap_coal",
            ng_col: "cap_ng",
            wind_col: "cap_wind",
            solar_col: "cap_solar",
        }
    )
    cty["cap_re"] = cty["cap_wind"] + cty["cap_solar"]

    # ---------------------------------------------------------
    # 3. Normalize shale potential & build post / interaction
    # ---------------------------------------------------------
    # Raw county shale potential (0 = no shale)
    cty["shale_raw"] = cty["shale_valScoreW_sum"].fillna(0.0)

    # Normalized index: log(1 + shale_raw)
    # - preserves 0 for non-shale counties
    cty["shale_index"] = np.log1p(cty["shale_raw"])

    # Post-2010 dummy
    cty["post"] = (cty["year"] >= 2010).astype(int)

    # Interaction
    cty["shale_post"] = cty["shale_index"] * cty["post"]

    # ---------------------------------------------------------
    # 4. Run regressions & build compact summary table
    # ---------------------------------------------------------
    def run_reg(dep_var: str):
        """Run OLS with county & year FE, clustered by county, return stats for shale_post."""
        formula = (
            f"{dep_var} ~ shale_post + shale_index + post "
            f"+ C(year) + C(fips_5)"
        )

        model = smf.ols(formula=formula, data=cty)
        res = model.fit(cov_type="cluster", cov_kwds={"groups": cty["fips_5"]})

        b = res.params.get("shale_post", np.nan)
        se = res.bse.get("shale_post", np.nan)
        t = res.tvalues.get("shale_post", np.nan)
        p = res.pvalues.get("shale_post", np.nan)

        return b, se, t, p

    results = {}
    for dep in ["cap_coal", "cap_ng", "cap_re"]:
        results[dep] = run_reg(dep)

    # Build a small DataFrame for pretty print
    out = pd.DataFrame.from_dict(
        results,
        orient="index",
        columns=["coef_shale_post", "se", "t", "pval"],
    )
    out.index.name = "dep_var"

    print("\n" + "=" * 72)
    print("Effect of shale_index × post (shale_post) on capacity")
    print("County & year FE, SEs clustered by county")
    print("=" * 72)
    print(out.round(4))

    # ---------------------------------------------------------
    # 5. Save county-year data for later plots / checks
    # ---------------------------------------------------------
    out_cty = data_int / "EIA_860_county_year_with_shale.csv"
    cty.to_csv(out_cty, index=False)
    print(f"\nSaved county-year dataset to: {out_cty}")


if __name__ == "__main__":
    main()
