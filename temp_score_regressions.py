#  %%

import copy
import pandas as pd
import numpy as np
import itertools
from sklearn.metrics import r2_score
import json
import matplotlib.pyplot as plt

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
year_data = year_data.drop(columns=["region"] + [str(year) for year in range(2000, 2100) if year % 5 != 0] )
# year_data

# print_vars = list(year_data["variable"].to_numpy())
# set([v for v in print_vars if "Carbon Sequestration" in str(v)])
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
# useful_data[useful_data["variable"] == "Emissions|Kyoto Gases"]
#  %%
# create new target variables for each model-scenario

# we cannot find 'Feedstocks' :)))
cdr_variables = ['Carbon Sequestration|CCS|Biomass', 'Carbon Sequestration|Land Use',
                 'Carbon Sequestration|Direct Air Capture', 'Carbon Sequestration|Enhanced Weathering',
                 'Carbon Sequestration|CCS|Biomass|Energy|Supply|Other', "Carbon Sequestration|CCS|Fossil|Energy|Supply|Other"
                 ]

crucial_variables = ["Emissions|Kyoto Gases", "GDP|PPP", "Emissions|CO2|Energy|Supply|Electricity",
                     "Emissions|CO2|Energy and Industrial Processes", "Secondary Energy|Electricity",
                     "Emissions|CO2|Energy|Demand|Transportation"
                    ]



# INT.emKyoto_gdp -> Emissions|Kyoto Gases / GDP|PPP
# INT.emCO2Elec_elecGen -> Emissions|CO2|Energy|Supply|Electricity / Secondary Energy|Electricity
# INT.emCO2EI_elecGen -> Emissions|CO2|Energy and Industrial Processes / Secondary Energy|Electricity
# INT.emCO2Transport_gdp -> Emissions|CO2|Energy|Demand|Transportation / GDP|PPP





new_variables_df = pd.DataFrame()
remaining_scenarios = 0
for name, df in useful_data.groupby("model-scenario"):
    intersection_ = set(df["variable"]).intersection(set(crucial_variables))
 
    if intersection_ != set(crucial_variables):
        continue
    
    remaining_scenarios += 1

    # new temporary structure
    temp_df = pd.DataFrame(columns=df.columns)
    row_ = {k:np.nan for k in df.columns}
    row_["model-scenario"] = name

    
    # create new variables by division | spaghetti code
    # Kyoto per GDP
    kyoto_gases = df.loc[df["variable"] == "Emissions|Kyoto Gases", [str(year) for year in range(2000, 2105, 5)]].to_numpy()[0]
    gdp = df.loc[df["variable"] == "GDP|PPP", [str(year) for year in range(2000, 2105, 5)]].to_numpy()[0]
    kyto_per_gdp = kyoto_gases / gdp
    row_["variable"] = "Emissions Kyoto per GDP"
    row_["unit"] = str(df.loc[df["variable"] == "Emissions|Kyoto Gases", "unit"].values[0]) + "/" + \
        str(df.loc[df["variable"] == "GDP|PPP", "unit"].values[0])
    for c in set(df.columns).difference(set(["variable", "unit", "model-scenario"])):
        array_index = int(c) % 2000 // 5  
        row_[c] = kyto_per_gdp[array_index]
    
    temp_df = temp_df.append(row_, ignore_index=True)

    # Emission from Electricity per Generated Electricity
    electricity_supply = df.loc[df["variable"] == "Emissions|CO2|Energy|Supply|Electricity", [str(year) for year in range(2000, 2105, 5)]].to_numpy()[0]
    secondary_electricity = df.loc[df["variable"] == "Secondary Energy|Electricity", [
        str(year) for year in range(2000, 2105, 5)]].to_numpy()[0]
    electricity_ratio = electricity_supply / secondary_electricity
    row_["variable"] = "Emissions Electricity per Secondary Electricity"
    row_["unit"] = str(df.loc[df["variable"] == "Emissions|CO2|Energy|Supply|Electricity", "unit"].values[0]) + "/" + \
        str(df.loc[df["variable"] ==
            "Secondary Energy|Electricity", "unit"].values[0])
    for c in set(df.columns).difference(set(["variable", "unit", "model-scenario"])):
        array_index = int(c) % 2000 // 5  
        row_[c] = electricity_ratio[array_index]
    
    temp_df = temp_df.append(row_, ignore_index=True)

    # Energy & Industrial Processes per Generated Electricty
    energy_and_industry_processes = df.loc[df["variable"] == "Emissions|CO2|Energy and Industrial Processes", [
        str(year) for year in range(2000, 2105, 5)]].to_numpy()[0]
    energy_industry_process_ratio = energy_and_industry_processes / secondary_electricity
    row_["variable"] = "Emissions Energy & Industrial Processes per Secondary Electricity"
    row_["unit"] = str(df.loc[df["variable"] == "Emissions|CO2|Energy and Industrial Processes", "unit"].values[0]) + "/" + \
        str(df.loc[df["variable"] ==
            "Secondary Energy|Electricity", "unit"].values[0])
    for c in set(df.columns).difference(set(["variable", "unit", "model-scenario"])):
        array_index = int(c) % 2000 // 5
        row_[c] = energy_industry_process_ratio[array_index]

    temp_df = temp_df.append(row_, ignore_index=True)

    # Emissions from Transportation per GDP
    transportation = df.loc[df["variable"] == "Emissions|CO2|Energy|Demand|Transportation", [
        str(year) for year in range(2000, 2105, 5)]].to_numpy()[0]
    trasportation_per_gdp = transportation / gdp
    row_["variable"] = "Emissions Transportation per GDP"
    row_["unit"] = str(df.loc[df["variable"] == "Emissions|CO2|Energy|Demand|Transportation", "unit"].values[0]) + "/" + \
        str(df.loc[df["variable"] ==
            "GDP|PPP", "unit"].values[0])
    for c in set(df.columns).difference(set(["variable", "unit", "model-scenario"])):
        array_index = int(c) % 2000 // 5
        row_[c] = trasportation_per_gdp[array_index]

    temp_df = temp_df.append(row_, ignore_index=True)
    
    # create CDR variable by summing
    # ? the units of the summed variables should be the same; should be :)
    cdr_values = np.array([0.0 for _ in  range(2000, 2105, 5)])
    for cdr_var in cdr_variables:
        if cdr_var not in df["variable"].to_numpy():
            continue
        cdr_values += df.loc[df["variable"] == cdr_var, [str(year) for year in range(2000, 2105, 5)]].to_numpy()[0]

    row_["variable"] = "CDR"
    row_["unit"] = "Mt CO2/yr"
    for c in set(df.columns).difference(set(["variable", "unit", "model-scenario"])):
        array_index = int(c) % 2000 // 5
        row_[c] = cdr_values[array_index]
    temp_df = temp_df.append(row_, ignore_index=True)

    new_variables_df = pd.concat([new_variables_df, temp_df])

    
concat_data = pd.concat([useful_data, new_variables_df])
# %%
# make CDR a column (cumulative CDR & max CDR)
tmp_data = concat_data.loc[concat_data["variable"] == "CDR"]
model_scenario, cdr_sums, cdr_maxs = tmp_data["model-scenario"], tmp_data[[str(year) for year in range(2000, 2105, 5)]].sum(axis=1).to_list(), tmp_data[[str(year) for year in range(2000, 2105, 5)]].max(axis=1).to_list()

cdr_df = pd.DataFrame({"model-scenario": model_scenario, "Cumulative CDR": cdr_sums, "Max CDR": cdr_maxs})


concat_data = pd.merge(concat_data, cdr_df, on="model-scenario", how="left")

# %%
# merging data and metadata
data = concat_data.merge(scenarios_meta, how="left", on="model-scenario")
data = data.loc[data["variable"].isin(["Emissions|Kyoto Gases",
                                "Emissions|CO2|Energy and Industrial Processes",
                                "Emissions Kyoto per GDP", "Emissions Electricity per Secondary Electricity",
                                "Emissions Energy & Industrial Processes per Secondary Electricity",
                                "Emissions Transportation per GDP"
                               ])]
# data
# %%
# calculate Annual Reduction
def calculate_lar_by_two_points(base_year, target_year, val_base_year, val_target_year):
    # just pctage of change
    # return 100 * (val_target_year - val_base_year) / val_base_year / (target_year - base_year)
    # real reduction
    return 100 * (val_base_year - val_target_year) / abs(val_base_year) / (target_year - base_year)


def calculate_aggragated_lar(year_range, values_, show_ = False):
    # values_ = list(reversed(values_))
    # make sure that we dont use nan values to calculate LAR
    values_ = np.array(values_)
    idxs = np.where(np.isnan(values_))
    values_ = np.delete(values_, idxs)

    year_range = np.array(year_range)
    year_range = np.delete(year_range, idxs)

    slope, intercept, r, p, se = stats.linregress(year_range, values_)


    # print(slope)
    # print(intercept)


    base_year = year_range[0]
    target_year = year_range[-1]

    val_base_year = base_year * slope + intercept
    val_target_year = target_year * slope + intercept

    X = year_range
    y = values_
    get_val = lambda v: v * slope + intercept
    y_pred = [get_val(v) for v in year_range]
    if show_:
        print(values_)
        print(y_pred)
        plt.scatter(X, y)
        plt.plot(X, y_pred, color="black")
        plt.plot([base_year, target_year], [values_[0], values_[-1]], color="red")
        plt.show()
    return calculate_lar_by_two_points(base_year, target_year, val_base_year, val_target_year)



# tweakable
start_year = 2020
last_year = 2050
interval_ = 5

column_years_to_consider = list(range(start_year, last_year+5, interval_))

test = data.iloc[1][[str(y) for y in column_years_to_consider]]

# lar1 = calculate_lar_by_two_points(start_year, last_year, test[str(start_year)], test[str(last_year)])
# print("LAR TWO POINTS")
# print(lar1)

# lar2 = calculate_aggragated_lar(
#     [y for y in column_years_to_consider], [test[str(y)] for y in column_years_to_consider], show_= True)
# print("LAR ADJUSTED")
# print(lar2)

# check types
# print([type(d) for d in data.columns])

# create LAR column
data["LAR"] = data.apply(lambda row_: calculate_aggragated_lar([y for y in column_years_to_consider],
                                                              [row_[str(y)] for y in column_years_to_consider]), axis=1)


# data["model-scenario"]

# %%
# split in 3rds by policy (carbon price|Avg NPV (2030-2100)) and by technology (CDR)

def map_number_to_meaning(n):
    if n == 1:
        return "low"
    if n == 2:
        return "medium"
    if n == 3:
        return "high"
    # this should not be reached
    return None

data = data.dropna(subset=["carbon price|Avg NPV (2030-2100)"])

chosen_cdr_column = "Cumulative CDR"
# chosen_cdr_column = "Max CDR"
data = data.dropna(subset=[chosen_cdr_column])


# ¡uncomment whats below to select only specific variable to regress!
variable_to_regress = "Emissions|Kyoto Gases"
data = data.loc[data["variable"] == variable_to_regress]

# variables_to_regress = ["Emissions|Kyoto Gases", "Emissions|CO2|Energy and Industrial Processes"]
# data = data[data.variable.isin(variables_to_regress)]

# print(data["carbon price|Avg NPV (2030-2100)"].to_list())
# %% 
print("*"*50)

print("min LAR", data["LAR"].min())

print("max LAR",  data["LAR"].max())

print("*"*50)


policy_data = copy.deepcopy(data)
technology_data = copy.deepcopy(data)

policy_data = policy_data.sort_values(by="carbon price|Avg NPV (2030-2100)")
policy_buckets = np.array_split(policy_data, 3)

technology_data = technology_data.sort_values(by=chosen_cdr_column)
technology_buckets = np.array_split(technology_data, 3)


filters = {}

for policy_idx, technology_idx in itertools.product(range(3), range(3)):
    policy_df = policy_buckets[policy_idx]
    technology_df = technology_buckets[technology_idx]
    intersection_df = pd.merge(policy_df, technology_df, on=list(policy_df.columns), how="inner")
    print((map_number_to_meaning(policy_idx+1), map_number_to_meaning(technology_idx+1)))
    print(intersection_df.shape)
    filters[(map_number_to_meaning(policy_idx+1), map_number_to_meaning(technology_idx+1))] = intersection_df



#  %%
# sanity test
print(filters[("medium", "low")]["model-scenario"])
#  %%
# regress scenario-model - var LAR to senario-model - temp66 

# plug LAR to equation ( in the backend )
def run_regression(X, y, type_="linear", poly_degree = 3):
    
    if type_ == "linear":
        slope, intercept, r, p, se = stats.linregress(X, y)

        y_ = slope * X + intercept
        plt.scatter(X, y)
        plt.plot(X, y_, color="red")
        plt.show()
        return (slope, intercept)
    
    
    if type_ == "poly":

        my_model = np.poly1d(np.polyfit(X, y, poly_degree))
        print("output of polynomial " , my_model)

        my_line = np.linspace(np.min(X), np.max(X))

        limits = (np.min(X), np.max(X))
        #print(len(X))
        plt.scatter(X, y)

        plt.plot(my_line, my_model(my_line), color="red")

        plt.show()

        r2 = r2_score(y, my_model(X))

        print(f"R2: {r2}, polynomial degree: {poly_degree}")
        print(f"Min: {limits[0]}, Max: {limits[1]}")
        return [my_model[i] for i in range(poly_degree+1)]
        #return (my_model[0], my_model[1], my_model[2], my_model[3])

policy = ["low", "medium", "high"]
tech = ["low", "medium", "high"]

poly_chosen_degrees = [5,3,2,2,3,2,5,2,4]

#results = pd.DataFrame(columns=["policy", "technology", "linear", "poly"])
results = []
idx = 0
for user_policy, user_technology in itertools.product(policy, tech):
    inner_dict = {}
    print(f"user policy: {user_policy}, user_tech: {user_technology}")
    inner_dict["policy"] = user_policy
    inner_dict["technology"] = user_technology
    poly_degree = poly_chosen_degrees[idx]
    # results.loc[idx, "policy"] = user_policy
    # results.loc[idx, "technology"] = user_technology

    lar_df = filters[(user_policy, user_technology)].loc[:, ["model-scenario", "LAR"]]
    print(len(lar_df))
    temp66 = temp66.rename(columns={"concscen2": "model-scenario"})

    regression_df = pd.merge(lar_df, temp66, on="model-scenario", how="left")
    regression_df = regression_df.dropna(subset=["LAR"])
    
    inner_dict['max_temp'] = regression_df['2100'].max()
    inner_dict['min_temp'] = regression_df['2100'].min()
    inner_dict['data'] = regression_df
    
    for type_ in ["linear", "poly"]:
        output = run_regression(regression_df["LAR"].to_numpy(), regression_df["2100"].to_numpy(), type_=type_, poly_degree=poly_degree)
        inner_dict[type_] = output
        #results.loc[idx, type_] = output
    
    results.append(inner_dict)
    

    idx += 1
    # poly_degrees = [2,3,4,5]
    # for poly_degree in poly_degrees:
    #     r2 = run_regression(regression_df["LAR"].to_numpy(), regression_df["2100"].to_numpy(), type_="poly", poly_degree=poly_degree)



#%%
# make functions with dynamic min and max values

# a higher sensitivity make the boundaries more responsive to the regression slope than a lower one
sensitivity = 1

for i in range(len(results)):
    
    policy = results[i]['policy']
    tech = results[i]['technology']
    
    # read coefficient
    intercept = results[i]['linear'][1]
    slope = results[i]['linear'][0]
    
    # get boundary values
    # y values
    ymax = results[i]['max_temp'] + sensitivity * np.abs(slope)
    ymin = results[i]['min_temp'] - sensitivity * np.abs(slope)

    # Get x values at that point
    xmax = (ymax - intercept) / slope
    xmin = (ymin - intercept) / slope
    
    results[i]['boundary_bottom_lar'] = xmin
    results[i]['boundary_bottom_temp'] = ymin
    
    results[i]['boundary_top_lar'] = xmax
    results[i]['boundary_top_temp'] = ymax
    
    # create x values in space
    xfit = np.linspace(xmin, xmax, 600) # to get same box always
    
    # predict y in that space
    ypred =  intercept + slope * xfit

    # get 1000 y values
    yfit = ypred
    yup = [ymax] * 200
    ydown = [ymin] * 200
    
    yfit = np.insert(yfit, 0, yup)
    yfit = np.insert(yfit, len(yfit), ydown)
    
    # get 1000 x values
    xup = np.linspace(-10, xmax, 200)
    xdown = np.linspace(xmin, 20, 200)
    
    xfit = np.insert(xfit, 0, xup)
    xfit = np.insert(xfit, len(xfit), xdown)    

    # extract data
    xdata = results[i]['data']['LAR']
    ydata = results[i]['data']['2100']    
    
    # display scatter and fitted line - need to fix (get from data df)
    plt.figure()
    plt.plot(xdata, ydata, '.')
    plt.plot(xfit, yfit, '-')
    plt.ylim(0, 4)
    plt.xlim(-2, 7)
    plt.ylabel('Temperature in 2100')
    plt.xlabel('LAR')
    plt.title(f'Policy: {policy}; Technology: {tech}')
    
    # add range text
    plt.text(2, 0.25, f'Range({ymin:.2f}-{ymax:.2f})')
        
    # save figure
    plt.savefig(f'graphs/graph_cumCDR_{i}_pol_{policy}_tech_{tech}.pdf')
    plt.savefig(f'graphs/graph_cumCDR_{i}_pol_{policy}_tech_{tech}.svg', format='svg')
    
    # remove data for json export
    results[i].pop('data')
      

# written to json -> talk to Sorin about implementation of boundaries
# suggest if-statements for lar above or below min/max boundary lar
# keep above 3.5 and below 1 degree indicators
with open("regres_results.json", "w") as handle:
    json.dump(results, handle)
#results.to_json("regres_coefs.json")
#results.to_csv("regres_coef.csv")    
#%%