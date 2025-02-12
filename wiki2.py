import requests
import pandas as pd
import time

API_KEY = 'YOUR_API_KEY_HERE'

company_names = [
    #insert
]

company_data_list = []

for company_name in company_names:
    print(f"Processing {company_name}...")
    
    search_url = 'https://api.opencorporates.com/v0.4/companies/search'
    search_params = {
        'q': company_name,
        'api_token': API_KEY,
    }
    
    try:
        search_response = requests.get(search_url, params=search_params)
        search_response.raise_for_status()
        search_data = search_response.json()
        
        if search_data['results']['total_count'] > 0:
            # Get the first matching company
            company = search_data['results']['companies'][0]['company']
            
            company_number = company.get('company_number')
            jurisdiction_code = company.get('jurisdiction_code')
            
            detail_url = f'https://api.opencorporates.com/v0.4/companies/{jurisdiction_code}/{company_number}'
            detail_params = {
                'api_token': API_KEY,
            }
            
            detail_response = requests.get(detail_url, params=detail_params)
            detail_response.raise_for_status()
            detail_data = detail_response.json()
            company_detail = detail_data['results']['company']
            
            company_data = {
                'Company Name': company_detail.get('name', ''),
                'Company Description': '',  # Placeholder
                'Headcount': '',            # Not available in OpenCorporates data
                'Industry': '',             # Will extract from industry codes
                'Founding Year': company_detail.get('incorporation_date', '')[:4] if company_detail.get('incorporation_date') else '',
                'Revenue': '',              # Not available in OpenCorporates data
                'Website': '',              # Placeholder
                'Address': company_detail.get('registered_address_in_full', ''),
            }
            
            industry_codes = company_detail.get('industry_codes', [])
            if industry_codes:
                industry_descriptions = [code.get('description', '') for code in industry_codes]
                company_data['Industry'] = '; '.join(industry_descriptions)
            
            company_data_list.append(company_data)
        else:
            print(f"No records found for {company_name}")
    
        time.sleep(1)  
    
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error for {company_name}: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting for {company_name}: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error for {company_name}: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"An error occurred for {company_name}: {err}")


df = pd.DataFrame(company_data_list)


df.to_csv('opencorporates_company_data.csv', index=False)

print("Data collection complete. Saved to opencorporates_company_data.csv")