import json
import pandas as pd
import ast

def load_services_data(file_name, zipcode):
    """Load service data from a specified JSON file for a given zipcode."""
    with open(file_name) as file:
        data_dict = json.load(file)
    return data_dict.get(str(int(zipcode)), [])

def get_services(risk, zipcode, cluster=None):
    """Fetch services based on risk, zipcode, and optional cluster."""
    service_files = {
        'Transportation Risk': 'transportation_services.json',
        'Healthcare Access Risk': ['telehealth_providers.json', 'Home_Health_physical_therapy.json', 'hospitals_with_emergency_services.json'],
        'Food Security': 'food_services.json',
        'Financial Risk': 'medicare_providers.json',
        'Technology Access Risk': 'telehealth_providers.json'
    }

    # Select the appropriate file based on risk and cluster
    if risk in service_files:
        file_name = service_files[risk]
        if isinstance(file_name, list):
            # Adjust file selection based on cluster for Healthcare Access Risk
            cluster_file_map = {0: 1, 3: 2} # Mapping clusters to indexes in the service_files list
            index = cluster_file_map.get(cluster, 0) # Default to telehealth providers
            file_name = file_name[index]
        services = load_services_data(file_name, zipcode)
    else:
        services = []
    
    return services if services else None

def get_suggested_actions(risk, risk_clusters, risk_actions_df, zipcode):
    """Generate suggested actions and services based on risk, risk clusters, and zipcode."""
    # Extract suggested actions for the given risk
    actions_data = risk_actions_df[risk_actions_df['Risk Title'] == risk]['Suggested Actions'].values[0]
    risk_clusters_actions = ast.literal_eval(actions_data)

    # Filter actions based on given clusters
    suggested_actions_dict = {key: value for key, value in risk_clusters_actions.items() if key in risk_clusters}
    services = {}

    # Logic to determine services based on risk and clusters
    if risk == 'Transportation Risk':
        if not any(cluster in ['Public Commute Services', 'Private Transport Conditions'] for cluster in risk_clusters):
            services['Transportation Services'] = get_services(risk, zipcode)
        services['Telehealth Service Providers'] = get_services(risk, zipcode, 1)

    elif risk == 'Food Security':
        if 'Food Service Providers' not in risk_clusters:
            services['Food Service Providers'] = get_services(risk, zipcode)
        if 'Accessibility to Supermarkets' in risk_clusters:
            services['Transportation Services'] = get_services(risk, zipcode, 2)

    elif risk == 'Healthcare Access Risk':
        if risk_clusters:
            services['Telehealth Service Providers'] = get_services(risk, zipcode)
        if 'Rehab Centers' in risk_clusters:
            services['Home Health Physical Therapy Providers'] = get_services(risk, zipcode, 0)
        if 'Hospital Count' in risk_clusters:
            services['Hospitals With Emergency Services'] = get_services(risk, zipcode, 3)

    elif risk == 'Financial Risk':
        if not any(cluster in ['Medicare/ Medicaid Beneficiaries', 'Medicare Utilization'] for cluster in risk_clusters):
            services['Medicare Service Providers'] = get_services(risk, zipcode)

    elif risk == 'Technology Access Risk':
        if 'Internet/Cellular Data Unavailability' in risk_clusters and 'Electronic Device Unavailability' not in risk_clusters:
            services['Transportation Services'] = get_services(risk, zipcode)

    return suggested_actions_dict, services
