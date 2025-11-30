import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data_raw"
DATA_INT = ROOT / "data_intermediate"

govs_path = DATA_RAW / "GOVS_to_FIPS_Codes_State_&_County_2007.xls"

# -------------------------------------------------------------
# 1. Load raw file with no header
# -------------------------------------------------------------
raw = pd.read_excel(govs_path, sheet_name="County Codes", header=None)
print(raw.head(30))
print(raw.shape)

# Find the first row where the first cell is a 5-digit GEO ID (e.g., 01001)
data_start = None
for idx, val in raw.iloc[:, 0].items():
    s = str(val).strip()
    if s.isdigit() and len(s) == 5:     # county/state GEO ID
        data_start = idx
        break

if data_start is None:
    raise RuntimeError("Could not detect the data start row.")

header_row = data_start - 1
print("Header row detected at:", header_row)

# -------------------------------------------------------------
# 2. Re-read with proper header row
# -------------------------------------------------------------
govs = pd.read_excel(govs_path, header=header_row)
govs.columns = [str(c).strip() for c in govs.columns]
print("Columns:", govs.columns.tolist())

# Rename columns reliably
govs = govs.rename(columns={
    govs.columns[1]: "statecode",
    govs.columns[2]: "countycode",
    govs.columns[3]: "Name",
    govs.columns[4]: "FIPS_state",
    govs.columns[5]: "CoG2002",
    govs.columns[6]: "CoG2007"
})

# Mark state rows
govs["is_state"] = govs["countycode"] == 0

# Build state_name
govs["state_name"] = np.where(
    govs["is_state"],
    govs["Name"].astype(str).str.upper().str.strip(),
    np.nan
)
govs["state_name"] = govs.groupby("statecode")["state_name"].ffill()

# Build county_name
govs["county_name"] = np.where(
    ~govs["is_state"],
    govs["Name"].astype(str).str.upper().str.strip(),
    np.nan
)

# Only county rows
county = govs[~govs["is_state"]].copy()

# Build FIPS
county["state_fips"] = county["FIPS_state"].astype(int).astype(str).zfill(2)
county["county_fips"] = county["CoG2007"].astype(int).astype(str).zfill(3)
county["fips"] = county["state_fips"] + county["county_fips"]

cross = county[["state_name", "county_name", "fips"]].drop_duplicates()

print("Crosswalk size:", len(cross))

# -------------------------------------------------------------
# Helper to add FIPS
# -------------------------------------------------------------
def add_fips(infile, outfile):
    df = pd.read_csv(infile)
    df["State_up"] = df["State"].astype(str).str.upper().str.strip()
    df["County_up"] = df["County"].astype(str).str.upper().str.strip()

    merged = df.merge(
        cross,
        how="left",
        left_on=["State_up", "County_up"],
        right_on=["state_name", "county_name"]
    )

    print(outfile.name, "missing FIPS:", merged["fips"].isna().mean())
    merged.drop(columns=["State_up", "County_up", "state_name", "county_name"], errors="ignore").to_csv(outfile, index=False)


add_fips(DATA_INT / "EIA_860_with_loc.csv", DATA_INT / "EIA_860_with_fips.csv")
add_fips(DATA_INT / "EIA_923_with_loc.csv", DATA_INT / "EIA_923_with_fips.csv")

print("DONE.")
