#  %%
import pandas as pd
import numpy as np
import patsy as ps

scenario_data_path_xls = "./input_data/iamc15_scenario_data_world_r2.0.xlsx"
scenario_data_path = "./input_data/iamc15_scenario_data_world_r2.0.csv"

baseline_path = "./input_data/baselines.csv"
temp66_path = "./input_data/temp66.csv"

scenario_metadata_indicators = "./input_data/sr15_metadata_indicators_r2.0.xlsx"

#  %%
# read data
scenarios_meta = pd.read_excel(scenario_metadata_indicators, sheet_name="meta")
year_data = pd.read_csv(scenario_data_path)
baselines = pd.read_csv(baseline_path)['baseline'].to_numpy()
temp66 = pd.read_csv(temp66_path)


#  %%
# filtering
initial_lines = scenarios_meta.shape[0]
scenarios_meta = scenarios_meta[~scenarios_meta.scenario.isin(baselines)]
print(f"---- {scenarios_meta.shape[0]} out of {initial_lines} rows remained after filtering the Metadata dataframe. ----")

scenarios_meta["model-scenario"] = scenarios_meta.model.map(
    str) + "-" + scenarios_meta.scenario.map(str)
scenarios_meta = scenarios_meta.iloc[:, 2:]

initial_lines = year_data.shape[0]
year_data.columns = year_data.columns.str.lower()
year_data = year_data[~year_data.scenario.isin(baselines)]
print(f"---- {year_data.shape[0]} out of {initial_lines} rows remained after filtering the Full Data dataframe. ----")

year_data["model-scenario"] = year_data.model.map(
    str) + "-" + year_data.scenario.map(str)
year_data = year_data.iloc[:, 2:]

# %%
# get only useful variables

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

useful_data = year_data[year_data["variable"].isin(all_vars_names)]
# %%
# merging data and metadata
data = useful_data.merge(scenarios_meta, how="left", on="model-scenario")
data = data.loc[data["variable"].isin(["Emissions|Kyoto Gases",
                                "Emissions|CO2|Energy and Industrial Processes",
                                "GDP|PPP", "Emissions|CO2|Energy|Supply|Electricity",
                                "Secondary Energy|Electricity", "Emissions|CO2|Energy|Demand|Transportation"])]
# data["model-scenario"]
# %%
# calculate Anual Reduction
# tweakable
start_year = 2020
last_year = 2050
interval_ = 5

column_years_to_consider = list(range(start_year, last_year, interval_))

# create AR column
# data["anual_reduction"] =



# split in 3rds by policy (carbon price) and by tech (cdr something)

# regress scenario-model + LAR to senario-model + temp66 


