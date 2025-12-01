*******************************************************
* 03_build_fips_crosswalk.do
* Create clean state- and county-level FIPS crosswalks
* from GOVS_to_FIPS_Codes_State_&_County_2007.xls
*
* Input : data_raw/GOVS_to_FIPS_Codes_State_&_County_2007.xls
* Output: data_intermediate/fips_state_codes.csv
*         data_intermediate/fips_county_codes_2007.csv
*******************************************************

clear all
set more off

cd "C:\Users\l2065\Sync\UMD\Research\Gas_Project\Shale_GAS_repo"
*cd "path/to/SHale_GAS_REPO"  

*******************************************************
* 1. STATE-LEVEL CODES
*******************************************************

* Import the "State Codes" sheet.
* We grab just the three relevant columns (GOVS state code,
* state name, and FIPS state code). Adjust B10:D if the
* header lines move in a future version.
import excel using "data_raw/GOVS_to_FIPS_Codes_State_&_County_2007.xls", ///
    sheet("State Codes") firstrow allstring clear

* Drop blank first col
ds
drop A
rename B govs_state_code
rename C state_name
rename D fips_state_code

* Force all codes to remain string
tostring govs_state_code, replace force
tostring fips_state_code, replace force

* Clean up whitespace
foreach v of varlist govs_state_code state_name fips_state_code {
    replace `v' = strtrim(`v')
}

* Drop completely empty rows
drop if govs_state_code == "" & state_name == "" & fips_state_code == ""

* (Optional) drop the "United States Total" row with code 00
drop if govs_state_code == "00"

drop in 1/4

* Save a clean state crosswalk as CSV
export delimited using "data_intermediate/fips_state_codes.csv", replace
save "data_intermediate/fips_state_codes.dta", replace

*******************************************************
* 2. COUNTY-LEVEL CODES
*******************************************************

* Import the "County Codes" sheet.
* Columns (from the spreadsheet screenshot):
*  B = GOVS ID
*  C = GOVS state code
*  D = GOVS county code
*  E = Name
*  F = FIPS state code
*  G = FIPS county code (2002)
*  H = FIPS county code (2007)
import excel using "data_raw/GOVS_to_FIPS_Codes_State_&_County_2007.xls", ///
    sheet("County Codes") firstrow allstring clear

drop A

rename B govs_id
rename C govs_state_code
rename D govs_county_code
rename E county_name
rename F fips_state_code
rename G fips_county_2002
rename H fips_county_2007

* FORCE all codes to be strings
tostring govs_state_code govs_county_code fips_state_code ///
         fips_county_2002 fips_county_2007, replace force

* Clean up whitespace
foreach v of varlist govs_id govs_state_code govs_county_code ///
                    county_name fips_state_code ///
                    fips_county_2002 fips_county_2007 {
    replace `v' = strtrim(`v')
}

* Drop completely empty rows
drop if govs_state_code == "" & govs_county_code == "" & ///
        county_name == "" & fips_state_code == "" & ///
        fips_county_2002 == "" & fips_county_2007 == ""

* (Optional) drop the UNITED STATES total row with ID 00000
drop if govs_id == "00000"
drop in 1/4  // adjust based on your sheet


* Build a standard 5-digit county FIPS using the 2007 codes
* (keep as string to preserve leading zeros)
gen fips_state_county_2007 = fips_state_code + fips_county_2007

* Save a clean county crosswalk as CSV
export delimited using "data_intermediate/fips_county_codes_2007.csv",  replace
save "data_intermediate/fips_county_codes_2007.dta", replace


*******************************************************
* End of file
*******************************************************
