import pandas as pd
from collections import defaultdict
import requests
import json

## Loading Data
df = pd.read_csv('req_data_merged.csv')
df_features = pd.read_csv('feature_data.csv')
df_features.drop(columns = ['Thresh1', 'Thresh2', 'Thresh3', 'Thresh4', 'Score'], inplace = True)

df_thresh = pd.read_csv('threshold_variable_60_25_15.csv')
df_thresh.rename({'1': 'Thresh1', '2': 'Thresh2', '3': 'Thresh3', '4': 'Thresh4'}, inplace = True, axis = 1)

df_disease = pd.read_csv('healthdata_transformed.csv', index_col= 0)
df_life = pd.read_csv('req_life.csv')

with open('disease_to_breakpoint.json', 'r') as f:
   disease_to_breakpoint = json.load(f)

with open('life_thresh_dict.json','r') as f:
    life_thresh_dict = json.load(f)

with open('cross_walk.json','r') as f:
    cross_walk = json.load(f)

with open('zip_county.json','r') as f:
    zip_county = json.load(f)

## Final features
# features = pd.merge(df_thresh, df_features, left_on = ['Label', 'Risk'], right_on = ['Variable Label', 'Risk'], how = 'inner')
features = pd.merge(df_features, df_thresh, right_on = ['Label', 'Risk'], left_on = ['Variable Label', 'Risk'], how = 'inner')

## Preprocessing
names = features['Variable Name']
labels = features['Variable Label']
name_to_label = {names[i]: labels[i] for i in range(len(names))}

req_cols = ['Variable Label', 'Risk', 'Cluster Name', 'Thresh1', 'Thresh2', 'Thresh3', 'Thresh4', 'weight']
df_dict = features[req_cols].set_index('Variable Label').T.to_dict('dict')

risks = defaultdict(set)
cluster_name_to_category = {}
for val in df_dict.values():
    risks[val['Risk']].add(val['Cluster Name'])
    cluster_name_to_category[val['Cluster Name']] = val['Risk']

FPL = 5140
income_risks_make_low = ['financial Risk', 'Income', 'Beneficiary Visits', 'Medicare Utilization', 'Medicare/ Medicaid Beneficiaries', 'Technology Access Risk','Electronic Device Unavailability', 'Internet/Cellular Data Unavailability']
income_risks_make_high = ['financial Risk', 'Income']

education_risks_make_low = ['Educational Challenges', 'Childcare Educational Programs', 'Educational Institution Count', 'Educational Qualifications', 'English Proficiency']
education_risks_make_high = ['Educational Challenges', 'Educational Qualifications']

def get_tract(address):
    url = f'https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress?address={address}&benchmark=4&vintage=4&format=json'
    response = requests.get(url)
    if response.status_code != 200:
        return None

    try:
      json_data = response.json()
      tract = json_data['result']['addressMatches'][0]['geographies']['Census Tracts'][0]['TRACT']
      return tract
    except:
      return None

def parse_inputs(inputs):
   def get_veteran_status(vet_stat):
      if vet_stat == 'Yes':
         return 1
      elif vet_stat == 'No':
         return -1
      else:
         return None
   return {
      'zipcode': int(inputs['zip_code']) if inputs['zip_code'] != '' else None,
      'tract': get_tract(inputs['address']) if inputs['address'] != '' else None,
      'age': int(inputs['age']) if inputs['age'] != '' else None,
      'is_male': inputs['gender'] != 'Male' if inputs['gender'] != '' else None,
      'race': inputs['race'] if inputs['race'] != '' else None,
      'income': int(inputs['income']) if inputs['income'] != '' else None,
      'education': inputs['education'] if inputs['education'] != '' else None,
      'veteran_status':  get_veteran_status(inputs['veteran_status'])
   }

def features_finder(zipcode, tract, age, is_male, race, income, education, veteran_status):
    # print(zipcode, tract, age, is_male, race, income, education, veteran_status)
    # print(tract is None)
    if tract is None:
      filtered_df = df[df['ZIPCODE'] == zipcode]
    else:
       filtered_df = df[df.apply(lambda row: str(row['COUNTYFIPS']) + tract == str(row['TRACTFIPS']), axis=1)]
       
    features_zip = filtered_df.mean(numeric_only=True).to_dict()

    removed_features = []
    if age is not None:
      removed_features += (features[(features['age'] == 'Yes') & (features['min'] > age) & (features['max'] < age)])['Variable Name'].tolist()
    if is_male is not None:
      removed_features += (features[(features['gender'] == 'Yes') & (features['male'] != is_male)])['Variable Name'].tolist()
    if race is not None:
      removed_features += (features[(features['race'] == 'Yes') & (features[race] != 1)])['Variable Name'].tolist()
    if income is not None:
      removed_features += (features[(features['Topic'] == 'Income')])['Variable Name'].tolist()
    if education is not None:
      removed_features += (features[(features['Domain'] == '3. Education')])['Variable Name'].tolist()
    if veteran_status is not None:
      removed_features += (features[(features['veteran_status'] == veteran_status * -1)])['Variable Name'].tolist()
    removed_features = set(removed_features)
    # print(removed_features)

    req_values = {}
    for feature in features['Variable Name'].values:
      if feature not in removed_features:
        req_values[name_to_label[feature]] = features_zip[feature]
    # print(req_values)
    return req_values

def get_thresh_score(val, t1, t2, t3, t4): 
    if(str(val) == 'nan'):
        return -1
    low_min, low_max = min(t1, t2), max(t1, t2)
    mid_min, mid_max = min(t2, t3), max(t2, t3)
    high_min, high_max = min(t3, t4), max(t3, t4)

    if val >= low_min and val <= low_max: 
        return 0 ## low risk
    elif val >= mid_min and val <= mid_max: 
        return 2 ## mid risk
    elif val >= high_min and val <= high_max:
        return 5 ## high risk
    else:
        return -1 ## invalid

def income_to_risk(income):
    if income >= FPL * 4:
        return 'Low'
    elif income >= FPL * 1.5:
        return 'Medium'
    else:
        return 'High'
    
def education_to_risk(education):
    if education == 'High School':
        return 'Low'
    elif education == 'College':
        return 'Medium'
    else:
        return 'High'
    
def calculate_risk_scores(variable_to_value, income = None, education = None):
    valid_variable_cnt, total_variable_cnt = 0, 0 
    cluster_scores = defaultdict(lambda : (0, 0))
    for k, v in variable_to_value.items():
        score = get_thresh_score(v, df_dict[k]['Thresh1'], df_dict[k]['Thresh2'], df_dict[k]['Thresh3'], df_dict[k]['Thresh4'])
        if score != -1:
            cur_score, cur_cnt = cluster_scores[df_dict[k]['Cluster Name']] 
            cur_score += score * df_dict[k]['weight'] ## take weighted sum wrt type of feature -> zip, county, tract
            cur_cnt += df_dict[k]['weight'] ## update this count by the weight 
            cluster_scores[df_dict[k]['Cluster Name']] = (cur_score, cur_cnt)   
            valid_variable_cnt += 1

        total_variable_cnt += 1

    cluster_risks = {}
    category_scores = {}
    for k in risks.keys():
        category_scores[k] = [0, 0, 0] ## low, mid, high count

    for k, v in cluster_scores.items():
        avg_score = v[0]/v[1] if v[1] != 0 else 0
        i = 0
        if avg_score <= 1:
            cluster_risks[k] = 'Low'
            i = 0
        elif avg_score <= 2.5:
            cluster_risks[k] = 'Medium'
            i = 1
        else:
            cluster_risks[k] = 'High'
            i = 2

        if (income == 'High' or income == 'Medium') and k in income_risks_make_high:
          i = 1 if income == 'High' else 2
          cluster_risks[k] = income
        elif income == 'Low' and k in income_risks_make_low:
          i = 0
          cluster_risks[k] = income

        if (education == 'High' or education == 'Medium') and k in education_risks_make_high:
          i = 1 if education == 'High' else 2
          cluster_risks[k] = education
        elif education == 'Low' and k in education_risks_make_low:
          i = 0
          cluster_risks[k] = education
        
        category_scores[cluster_name_to_category[k]][i] += 1

    category_risks = {}
    """
        If atleast 1 high risk cluster in a category with 3 or less clusters or atleast 2 high risk clusters in a category with 4 or more clusters -> High Risk
        If 1 high risk cluster or 2 mid risk clusters in a category with 4 or more clusters or 1 mid risk cluster in a category with 3 or less clusters -> Medium Risk
        Else Low Risk
    """
    for k,v in category_scores.items():
        if (len(risks[k]) <= 3 and v[2] >= 1) or (len(risks[k]) > 3 and v[2] >= 2): 
            category_risks[k] = 'High'
        elif (len(risks[k]) > 3 and (v[2] >= 1 or v[1] >= 2)) or (len(risks[k]) <= 3 and v[1] >= 1): 
            category_risks[k] = 'Medium'
        else:
            category_risks[k] = 'Low'
        
        if (income == 'High' or income == 'Medium') and k in income_risks_make_high:
          category_risks[k] = income
        elif income == 'Low' and k in income_risks_make_low:
          category_risks[k] = income

        if (education == 'High' or education == 'Medium') and k in education_risks_make_high:
          category_risks[k] = education
        elif education == 'Low' and k in education_risks_make_low:
          category_risks[k] = education

    calculated_risks = {}
    for k, v in risks.items():
        # if(category_risks[k] != 'Low'): ## only select High/Mid risk categories and their High/Mid risk clusters
        risky_clusters = []
        for cluster in v:
            if category_risks[k] != 'Low' and cluster_risks[cluster] != 'Low':
                risky_clusters.append(cluster)
        calculated_risks[k] = risky_clusters

    ## Returns Risky clusters, confidence score
    return calculated_risks, valid_variable_cnt/total_variable_cnt if total_variable_cnt != 0 else 0, category_risks, cluster_risks

def get_life_data(zipcode):
    tract = cross_walk[zipcode]
    life_data = df_life[df_life['TRACTFIPS'].apply(lambda x: x in tract)].mean().to_dict()
    return life_data

def get_life_expectancy_risks(life_data):
    risky = []
    if life_data is None:
        return risky
    for key, value in life_data.items():
        if key.startswith('e(x)'):
            if value < life_thresh_dict[key]['low']:
                risky.append(life_thresh_dict[key]['range'])
    return risky

def get_health_data(zipcode):
    try:
        county = zip_county[zipcode]
        health_data = df_disease[df_disease['COUNTYFIPS'] == county].mean().to_dict()
        return health_data
    except:
        return None

def get_health_risks(health_data):
    risky = []
    if health_data is None:
        return risky
    for key, value in health_data.items():
        if key in disease_to_breakpoint:
            if value > disease_to_breakpoint[key]:
                risky.append(key)
    return risky

# zipcode, tract, age, is_male, race, income, education, veteran_status
# feature_data = features_finder(zipcode=2472)

# print(calculate_risk_scores(feature_data))
# calculate_risks,valid_variable_cnt, category_risks, cluster_risks = calculate_risk_scores(feature_data)
# # print("\n\ncalculate risks",calculate_risks)
# print("\n\n category",cluster_risks)