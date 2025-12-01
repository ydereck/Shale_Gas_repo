# **Shale Gas Project**

This repository processes EIA power plant data, assigns county FIPS codes, merges shale potential from Rystad/Bartik (2019), and runs county-year regressions to study how shale potential affects coal, natural gas, and renewable capacity.

Large data files are stored using **Git LFS**.

---

## **Workflow Overview**

The analysis follows these main steps:

### **1. Build FIPS crosswalk (Stata)**
- `code/02a_build_fips_crosswalk.do`

### **2. Add FIPS to EIA 860 / EIA 923 (Python)**
- `code/02b_add_fips_860.py`
- `code/02c_add_fips_923.py`

### **3. Merge shale potential (Python)**
- `code/02d_add_shale_to_860.py`
  - Collapses Rystad county × play prospectivity  
  - Creates county-level shale index:  
    ```
    shale_index = ln(1 + shale_valScoreW_sum)
    ```

### **4. Construct county-year dataset & run regressions**
- Python: `code/03a_reg_shale_860.py`  
- Stata: `code/03a_reg_shale_860.do`

## **Regression Results**

The main county-year regression table (coal, natural gas, renewables) is exported to:
- `output/reg_capacity_shale.xls`

This table reports the coefficient on:
- `shale_post = shale_index * post`

with standard errors **clustered by county**.

---

## **Key Output Files**

- `data_intermediate/EIA_860_with_fips_shale.csv`
- `data_intermediate/EIA_860_county_year_with_shale.csv`
- **`output/reg_capacity_shale.xls`** *(main regression results)*

---


