# Milestone 1 — verified NASA ASF catalog results

Query time (UTC): 2026-11-14T07:09:31.655815+00:00

Source: https://asfopensarlab.github.io/NISAR_Cookbook/search-stream-nisar-asf-search/

Both requested observations were returned by a live asf_search query.
Compatible configuration: L-SAR, ascending, track 105, frame 017, bandwidth 4005, polarization DHDH, acquired source A, CRID P05023.
Catalog frequency-A polarizations: HH and HV. GCOV HH intensity layer: HHHH.

## 2026-06-21T11:19:06+00:00

Product ID: `NISAR_L2_PR_GCOV_023_105_A_017_4005_DHDH_A_20260621T111906_20260621T111941_P05023_N_F_J_001`

Product type: L2_GCOV; maturity: PROVISIONAL.

[Catalog HTTPS download URL](https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_PROVISIONAL_V1/NISAR_L2_PR_GCOV_023_105_A_017_4005_DHDH_A_20260621T111906_20260621T111941_P05023_N_F_J_001/NISAR_L2_PR_GCOV_023_105_A_017_4005_DHDH_A_20260621T111906_20260621T111941_P05023_N_F_J_001.h5)

S3 URI: `s3://sds-n-cumulus-prod-nisar-products/NISAR_L2_GCOV_PROVISIONAL_V1/NISAR_L2_PR_GCOV_023_105_A_017_4005_DHDH_A_20260621T111906_20260621T111941_P05023_N_F_J_001/NISAR_L2_PR_GCOV_023_105_A_017_4005_DHDH_A_20260621T111906_20260621T111941_P05023_N_F_J_001.h5`

## 2026-07-03T11:19:05+00:00

Product ID: `NISAR_L2_PR_GCOV_024_105_A_017_4005_DHDH_A_20260703T111905_20260703T111940_P05023_N_F_J_001`

Product type: L2_GCOV; maturity: PROVISIONAL.

[Catalog HTTPS download URL](https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_PROVISIONAL_V1/NISAR_L2_PR_GCOV_024_105_A_017_4005_DHDH_A_20260703T111905_20260703T111940_P05023_N_F_J_001/NISAR_L2_PR_GCOV_024_105_A_017_4005_DHDH_A_20260703T111905_20260703T111940_P05023_N_F_J_001.h5)

S3 URI: `s3://sds-n-cumulus-prod-nisar-products/NISAR_L2_GCOV_PROVISIONAL_V1/NISAR_L2_PR_GCOV_024_105_A_017_4005_DHDH_A_20260703T111905_20260703T111940_P05023_N_F_J_001/NISAR_L2_PR_GCOV_024_105_A_017_4005_DHDH_A_20260703T111905_20260703T111940_P05023_N_F_J_001.h5`

Verification: all 10 requested packages imported; pip check reported no broken requirements.
No HDF5 files downloaded. Catalog URLs were not opened; authenticated product access and raster contents remain unverified.

Resolved issue: the API mainBandPolarization=HH filter returned zero records; the final script follows the Cookbook query and verifies HH in returned catalog metadata and filenames.
Python 3.11 was unavailable; the existing Python 3.12.0 was used without system changes.
