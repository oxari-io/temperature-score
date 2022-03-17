#  %%
import pandas as pd
import numpy as np
import patsy as ps
import matplotlib.pyplot as plt

from email.mime import base
from scipy import stats

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
def calculate_lar_by_two_points(base_year, target_year, val_base_year, val_target_year, show_=False):
    if show_:
        X = [base_year, target_year]
        y = [val_base_year, val_target_year]
        plt.scatter(X, y)
        plt.plot(X, y)
        plt.show()
    # return 100 * (val_target_year - val_base_year) / val_base_year / (target_year - base_year)
    return 100 * (val_base_year - val_target_year) / val_base_year / (target_year - base_year)


def calculate_aggragated_lar(year_range, values_):
    # values_ = list(reversed(values_))
    slope, intercept, r, p, se = stats.linregress(year_range, values_)
    print(values_)

    print(slope)
    print(intercept)


    base_year = year_range[0]
    target_year = year_range[-1]

    val_base_year = base_year * slope + intercept
    val_target_year = target_year * slope + intercept

    X = year_range
    y = values_
    get_val = lambda v: v * slope + intercept
    y_pred = [get_val(v) for v in year_range]
    print(y_pred)
    plt.scatter(X, y)
    plt.plot(X, y_pred)
    plt.show()
    # return 1
    return calculate_lar_by_two_points(base_year, target_year, val_base_year, val_target_year)



# tweakable
start_year = 2020
last_year = 2050
interval_ = 5

column_years_to_consider = list(range(start_year, last_year+5, interval_))

test = data.iloc[100][[str(y) for y in column_years_to_consider]]

lar1 = calculate_lar_by_two_points(start_year, last_year, test[str(start_year)], test[str(last_year)], show_= True)
print("LAR TWO POINTS")
print(lar1)

lar2 = calculate_aggragated_lar(
    [y for y in column_years_to_consider], [test[str(y)] for y in column_years_to_consider])
print("LAR Aggregated")
print(lar2)

# TODO: calculate for all data and store it
# create AR column
# data["anual_reduction"] =

# %%





#  TODOs
# split in 3rds by policy (carbon price) and by tech (cdr something)

# regress scenario-model + LAR to senario-model + temp66 


#  %%
