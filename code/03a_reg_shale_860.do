*******************************************************
* 03a_reg_shale_860.do
*
* County-year regressions of capacity on shale potential
* using EIA_860_with_fips_shale.csv
*
* Replicates the Python spec:
*   cap_*_ct ~ shale_index*post + shale_index + post
*             + county FE + year FE, clustered by county
*******************************************************

clear all
set more off

*------------------------------------------------------*
* 0. Load plant-level data (with FIPS + shale scores)  *
*------------------------------------------------------*

* Assume you have already cd'ed to the repo root, e.g.:
cd "C:\Users\l2065\Sync\UMD\Research\Gas_Project\Shale_Gas_repo"

import delimited using "data_intermediate/EIA_860_with_fips_shale.csv", ///
    clear varnames(1) stringcols(1)

* Check variable names if needed:
* describe

*------------------------------------------------------*
* 1. Clean FIPS (5-digit string)                       *
*------------------------------------------------------*

rename fips_5 fips_5_old
rename fips_state_county_5digit FIPS_state_county_5digit

* If FIPS_state_county_5digit is numeric, convert to 5-digit string
capture confirm numeric variable FIPS_state_county_5digit
if _rc == 0 {
    gen fips_5 = string(FIPS_state_county_5digit, "%05.0f")
}
else {
    * If it's already string, just clean and pad
    gen fips_5 = FIPS_state_county_5digit
    replace fips_5 = strtrim(fips_5)
    replace fips_5 = substr("00000" + fips_5, ///
        strlen("00000" + fips_5) - 4, .)
}

drop if fips_5=="."
*------------------------------------------------------*
* 2. Collapse to county-year                           *
*    (coal, gas, wind, solar, renewables)              *
*------------------------------------------------------*

* In Stata, spaces in names are turned into underscores.
* So "capacity source 1" in the CSV becomes capacity_source_1, etc.

* Check these exist:
* describe capacity_source_1 capacity_source_3 capacity_source_4 capacity_source_5

rename capacitysource1 capacity_source_1
rename capacitysource3 capacity_source_3
rename capacitysource4 capacity_source_4
rename capacitysource5 capacity_source_5

rename shale_valscorew_sum shale_valScoreW_sum
rename shale_valscorem_max shale_valScoreM_max

*------------------------------------------------------*
* Convert capacity_source_* variables to numeric       *
* (Stata read them as string because of non-numeric)   *
*------------------------------------------------------*

foreach v of varlist capacity_source_* {
    di "Converting `v' to numeric..."
    destring `v', replace ignore(",") force
}

*collapse ///
    (sum) capacity_source_1 capacity_source_3 capacity_source_4 capacity_source_5 ///
    (max) shale_valScoreW_sum shale_valScoreM_max, ///
    by(fips_5 year)

rename capacity_source_1 cap_coal
rename capacity_source_3 cap_ng
rename capacity_source_4 cap_wind
rename capacity_source_5 cap_solar

gen cap_re = cap_wind + cap_solar

*------------------------------------------------------*
* 3. Normalize shale potential & build post / interact *
*------------------------------------------------------*

* Raw county shale potential (0 if missing)
gen shale_raw = shale_valScoreW_sum
replace shale_raw = 0 if missing(shale_raw)

* Normalized index: ln(1 + shale_raw)
* (matches Python's log1p)
gen shale_index = ln(shale_raw + 1)

* Post-2010 dummy
gen post = (year >= 2010)

* Interaction
gen shale_post = shale_index * post

* Save the collapsed county-year dataset (for comparison with Python)
save "data_intermediate/EIA_860_county_year_with_shale_from_stata.dta", replace

*------------------------------------------------------*
* 4. Regressions with county & year FE, clustered SEs  *
*------------------------------------------------------*

* You need reghdfe installed. If not:
* ssc install reghdfe, replace
* ssc install ftools, replace

* Coal capacity
reghdfe cap_coal shale_post shale_index post, ///
    absorb(year fips_5) vce(cluster fips_5)

* Gas capacity
reghdfe cap_ng shale_post shale_index post, ///
    absorb(year fips_5) vce(cluster fips_5)

* Renewable (wind + solar) capacity
reghdfe cap_re shale_post shale_index post, ///
    absorb(year fips_5) vce(cluster fips_5)

*******************************************************
* End of file
*******************************************************
