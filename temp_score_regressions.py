#  %%
import pandas as pd
import numpy as np
import patsy as ps

scenario_data_path_xls = "./input_data/iamc15_scenario_data_world_r2.0.xlsx"
scenario_data_path = "./input_data/iamc15_scenario_data_world_r2.0.csv"

scenario_metadata_indicators = "./input_data/sr15_metadata_indicators_r2.0.xlsx"

test_lar = 1000
#  %%
# main line in R-code that needs to be translated
# sr15_prefilter <- sr15_var_long %>% merge(sr15_meta, by='Model-Scenario')

scenarios_meta = pd.read_excel(scenario_metadata_indicators, sheet_name="meta")
scenarios_meta["Model-Scenario"] = scenarios_meta.model.map(
    str) + "-" + scenarios_meta.scenario.map(str)
scenarios_meta = scenarios_meta.iloc[:, 2:]
# scenarios_meta.head()
# %%
# all_data = pd.read_csv(scenario_data_path, dtype={str(c): np.float64 for c in range (2000, 2101)})
all_data = pd.read_csv(scenario_data_path)

all_data["Model-Scenario"] = all_data.Model.map(
    str) + "-" + all_data.Scenario.map(str)
all_data = all_data.iloc[:, 2:]

# all_data.head()

# %%

parentvar_to_subvar = {
    'Emissions|CO2': ['Energy and Industrial Processes', 'Energy', 'Industrial Processes',
                      'Energy|Supply', 'Energy|Demand', 'Energy|Demand|Industry', 'Energy|Demand|Transportation',
                      'Energy|Supply|Electricity', 'AFOLU'],
    'Carbon Sequestration': ['CCS|Biomass', 'CCS|Biomass|Energy', 'CCS|Biomass|Energy|Supply',
             'CCS|Biomass|Energy|Supply|Electricity', 'CCS|Fossil', 'Land Use',
             'Feedstocks', 'Direct Air Capture', 'Enhanced Weathering', 'Other']
}

other_vars = ['Primary Energy', 'Secondary Energy|Electricity',
              'Emissions|Kyoto Gases', 'Emissions|CH4|AFOLU', 'Emissions|N2O|AFOLU', 'Price|Carbon',
              'Carbon Sequestration|CCS|Biomass|Energy|Supply|Electricity', 'GDP|PPP']

all_vars_names = [parent+"|"+subvar
                    for parent in parentvar_to_subvar.keys()
                  for subvar in parentvar_to_subvar[parent]] + other_vars
all_vars_names

# %%
# print(all_data["Variable"])
useful_data = all_data[all_data["Variable"].isin(all_vars_names)]
# useful_data.shape
useful_data
# %%

