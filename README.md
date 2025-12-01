📘 Shale Gas Project — Repository Overview

This repository contains the full workflow for matching U.S. power plant data (EIA 860 & EIA 923) to county FIPS codes, merging in shale potential measures from Rystad/Bartik (2019), and running county-year regressions to study how shale development influences power-sector capacity (coal, natural gas, and renewables).

The project uses:

Stata for data cleaning & crosswalk generation

Python for plant-level processing, merging, and regressions

Git LFS to track large raw & intermediate datasets

This README explains the structure, data processing steps, and how to run each stage.

📁 Repository Structure
Shale_Gas_repo/
│
├── code/                   # Stata & Python code (main workflow)
│   ├── 01_merge_location.py
│   ├── 02a_build_fips_crosswalk.do
│   ├── 02b_add_fips_860.py
│   ├── 02c_add_fips_923.py
│   ├── 02d_add_shale_to_860.py
│   ├── 03a_reg_shale_860.do
│   └── 03a_reg_shale_860.py
│
├── data_raw/               # Raw data files (tracked via Git LFS)
│   ├── EIA_860.csv
│   ├── EIA_923.csv
│   ├── EIA_power_plant_location.csv
│   ├── GOVS_to_FIPS_Codes_State_&_County_2007.xls
│   └── Rystad/rystad_county.dta
│
├── data_intermediate/      # Processed datasets (tracked via Git LFS)
│   ├── fips_state_codes.csv / .dta
│   ├── fips_county_codes_2007.csv / .dta
│   ├── EIA_860_with_loc.csv
│   ├── EIA_860_with_fips.csv / .dta
│   ├── EIA_860_with_fips_shale.csv / .dta
│   ├── EIA_860_county_year_with_shale.csv
│   ├── EIA_923_with_loc.csv
│   ├── EIA_923_with_fips.csv
│   └── EIA_860_county_year_with_shale_from_stata.dta
│
├── .gitattributes          # Git LFS tracking rules
├── .gitignore              # Ignore temp/log/env files
└── README.md               # Project documentation (this file)


Note: Large raw and intermediate datasets are stored via Git LFS.
Run git lfs install after cloning.

📦 Data Sources
EIA 860

Annual plant-level capacity & technology data:

Nameplate capacity

Fuel type

Operational status

Generator characteristics

EIA 923

Monthly generation & fuel consumption data:

Net electricity generation

Fuel quantity & heat content

Fuel cost

Rystad / Bartik (2019) Shale Potential

County × shale-play prospectivity data:

valScoreW: area-weighted total prospectivity

valScoreM: peak prospectivity

Used to construct a county-level shale potential index

🛠 Processing Pipeline

The workflow proceeds in several steps:

Step 1 — Build FIPS Crosswalk (Stata)

File: 02a_build_fips_crosswalk.do

Reads:

GOVS_to_FIPS_Codes_State_&_County_2007.xls (two-tab Excel)

Extracts state and county FIPS codes

Outputs:

data_intermediate/fips_state_codes.csv/.dta
data_intermediate/fips_county_codes_2007.csv/.dta

Step 2 — Add FIPS Codes to EIA 860 and 923 (Python)
EIA 860:

File: 02b_add_fips_860.py
Merges plant-level data with:

County FIPS

State names

County names

EIA 923:

File: 02c_add_fips_923.py
Does the same for EIA 923 generation data.

Outputs:

EIA_860_with_fips.csv
EIA_923_with_fips.csv

Step 3 — Merge Shale Potential (Python)

File: 02d_add_shale_to_860.py

Reads rystad_county.dta

Collapses to county-level:

shale_valScoreW_sum = total Rystad prospectivity

shale_valScoreM_max = maximum prospectivity

Merges onto the EIA 860 file by county FIPS

Fills missing shale scores with 0 for non-shale counties

Outputs:

EIA_860_with_fips_shale.csv
EIA_860_county_year_with_shale.csv

Step 4 — Regression Analysis (Python & Stata)
Python version:

File: 03a_reg_shale_860.py

Aggregates plant-level data to county-year

Builds shale_index = log(1 + shale_valScoreW_sum)

Constructs:

post (year ≥ 2010)

shale_post = shale_index × post

Runs regressions:

cap
𝑐
𝑡
=
𝛼
𝑐
+
𝜆
𝑡
+
𝛽
⋅
(
shale_index
𝑐
×
post
𝑡
)
+
𝜀
𝑐
𝑡
cap
ct
	​

=α
c
	​

+λ
t
	​

+β⋅(shale_index
c
	​

×post
t
	​

)+ε
ct
	​


For:

Coal capacity

Natural gas capacity

Renewable capacity (wind + solar)

Stata version (cross-check):

File: 03a_reg_shale_860.do

Same FE specification using reghdfe.

📊 Key Interpretations (Current Results)

Renewables (wind+solar): Positive and statistically significant shale_post effect

Natural gas capacity: No significant relationship detected in current spec

Coal capacity: Weak/non-significant evidence of response

These are preliminary and depend on:

county-level aggregation

treatment timing (post = 2010)

shale index choice

clustering choice

🚀 How to Reproduce the Workflow
1. Clone the repo (with LFS):
git clone https://github.com/<your-username>/Shale_Gas_repo.git
git lfs pull

2. Install dependencies

Python:

pip install pandas numpy statsmodels


Stata:

ssc install reghdfe
ssc install ftools

3. Run in order:
02a_build_fips_crosswalk.do
02b_add_fips_860.py
02c_add_fips_923.py
02d_add_shale_to_860.py
03a_reg_shale_860.py   (or 03a_reg_shale_860.do)

🧩 Notes

All large data files are handled via Git LFS

Intermediate CSV/DTA files are created inside data_intermediate/

Scripts use relative paths for full reproducibility

County FIPS is always treated as string to preserve leading zeros