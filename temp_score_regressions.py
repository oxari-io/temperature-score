#  %%
import pandas as pd

scenario_data_path = "./input_data/iamc15_scenario_data_world_r2.0.xlsx"
scenario_metadata_indicators = "./input_data/sr15_metadata_indicators_r2.0.xlsx"

test_lar = 1000
#  %%
# main line in R-code that needs to be translated
# sr15_prefilter <- sr15_var_long %>% merge(sr15_meta, by='Model-Scenario')

scenarios_meta = pd.read_excel(scenario_metadata_indicators, sheet_name="meta")
scenarios_meta.head()
# %%
