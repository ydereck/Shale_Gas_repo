import pandas as pd
from pathlib import Path

# --- paths ---
ROOT = Path(__file__).resolve().parents[1]   # project_root/
DATA_RAW = ROOT / "data_raw"
DATA_INT = ROOT / "data_intermediate"

DATA_INT.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------
# 1. Load plant location file
# -------------------------------------------------------------
loc_path = DATA_RAW / "EIA_power_plant_location.csv"
loc = pd.read_csv(loc_path)

# Keep needed variables
loc_subset = loc[[
    "Plant_Code",
    "Utility_ID",
    "Plant_Name",
    "Utility_Name",
    "County",
    "State",
    "Longitude",
    "Latitude"
]].copy()

# STANDARDIZE TYPES FOR MERGING
loc_subset["Plant_Code"] = (
    pd.to_numeric(loc_subset["Plant_Code"], errors="coerce")
      .astype("Int64")
      .astype(str)
      .str.strip()
)
loc_subset["Utility_ID"] = (
    pd.to_numeric(loc_subset["Utility_ID"], errors="coerce")
      .astype("Int64")
      .astype(str)
      .str.strip()
)

loc_subset["County"] = loc_subset["County"].astype(str).str.strip()
loc_subset["State"]  = loc_subset["State"].astype(str).str.strip()

print("Loaded plant location file.")
print("Unique plants in location file:", loc_subset["Plant_Code"].nunique())

# -------------------------------------------------------------
# 2. Process EIA 860 (capacity)
# -------------------------------------------------------------
e860_path = DATA_RAW / "EIA_860.csv"
e860 = pd.read_csv(e860_path)

# Make sure IDs are string, using numeric coercion to align with Plant_Code
e860["facilid"] = (
    pd.to_numeric(e860["facilid"], errors="coerce")
      .astype("Int64")
      .astype(str)
      .str.strip()
)
e860["utilid"]  = e860["utilid"].astype(str).str.strip()

print("Unique plants in EIA 860:", e860["facilid"].nunique())

# Merge ONLY on plant ID
e860_loc = e860.merge(
    loc_subset,
    how="left",
    left_on="facilid",
    right_on="Plant_Code",
    suffixes=("", "_loc")
)

missing_860 = e860_loc["County"].isna().mean()
print(f"EIA 860: missing location fraction = {missing_860:.3f}")

e860_loc_out = DATA_INT / "EIA_860_with_loc.csv"
e860_loc.to_csv(e860_loc_out, index=False)
print("Saved:", e860_loc_out)

# -------------------------------------------------------------
# 3. Process EIA 923 (generation)
# -------------------------------------------------------------
e923_path = DATA_RAW / "EIA_923.csv"
e923 = pd.read_csv(e923_path)

e923["facilid"] = (
    pd.to_numeric(e923["facilid"], errors="coerce")
      .astype("Int64")
      .astype(str)
      .str.strip()
)
e923["utilid"]  = e923["utilid"].astype(str).str.strip()

print("Unique plants in EIA 923:", e923["facilid"].nunique())

e923_loc = e923.merge(
    loc_subset,
    how="left",
    left_on="facilid",
    right_on="Plant_Code",
    suffixes=("", "_loc")
)

missing_923 = e923_loc["County"].isna().mean()
print(f"EIA 923: missing location fraction = {missing_923:.3f}")

e923_loc_out = DATA_INT / "EIA_923_with_loc.csv"
e923_loc.to_csv(e923_loc_out, index=False)
print("Saved:", e923_loc_out)
