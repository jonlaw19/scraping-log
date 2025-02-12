import requests
import pandas as pd
import urllib.parse
import json

# Read the CSV file into a DataFrame
df = pd.read_csv('customers.csv', dtype={'number': str})

# Function to get provider name using NPI number
def get_provider_name(npi_number):
    base_url = 'https://npiregistry.cms.hhs.gov/api/'
    params = {
        'number': npi_number,
        'version': '2.1'
    }
    try:
        # Build the full URL with parameters
        query_string = urllib.parse.urlencode(params)
        full_url = f'{base_url}?{query_string}'
        # Debug: Print the request URL
        print(f'Requesting NPI {npi_number} with URL: {full_url}')
        response = requests.get(full_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        # Debug: Print the response status code and data
        print(f'Response status code: {response.status_code}')
        print(f'Response data: {json.dumps(data)}')
        if data.get('result_count', 0) == 1:
            provider = data['results'][0]
            enumeration_type = provider.get('enumeration_type', '')
            basic_info = provider.get('basic', {})
            if enumeration_type == 'NPI-2':
                # Organizational provider
                organization_name = basic_info.get('organization_name', 'N/A')
                return organization_name
            elif enumeration_type == 'NPI-1':
                # Individual provider
                name_parts = [
                    basic_info.get('first_name', ''),
                    basic_info.get('middle_name', '_'),
                    basic_info.get('last_name', '')
                ]
                # Filter out empty strings
                name_parts = [name for name in name_parts if name]
                full_name = ' '.join(name_parts)
                return full_name if full_name else 'N/A'
            else:
                return 'Unknown enumeration type'
        else:
            return 'No data found or multiple results'
    except requests.exceptions.RequestException as e:
        print(f'Error fetching NPI {npi_number}: {e}')
        return 'Error'

# Apply the function to each NPI number
df['organization_name'] = df['number'].apply(get_provider_name)

# Save the updated DataFrame to a new CSV file
df.to_csv('customers_updated.csv', index=False)

print('Organization names have been updated and saved to customers_updated.csv')


# python npi.py > terminal_output.txt 
# python parse_terminal_output.py
