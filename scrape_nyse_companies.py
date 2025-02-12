import requests
from bs4 import BeautifulSoup
import wikipediaapi
import pandas as pd
import re
import os
import time
from urllib.parse import urljoin

BASE_URL = 'https://en.wikipedia.org'
START_CATEGORY_URL = 'https://en.wikipedia.org/wiki/Category:Companies_listed_on_the_Pakistan_Stock_Exchange'
HEADERS = {
    'User-Agent': 'CompanyDataScraper/1.0 (your.email@example.com)' 
}
DELAY_BETWEEN_REQUESTS = 0.1  

company_names = set()
processed_categories = set()
company_data_list = []

wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent='CompanyDataScraper/1.0 (your.email@example.com)'  
)

def process_category(url):
    if url in processed_categories:
        return
    processed_categories.add(url)
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve {url}: {e}")
        return
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    for li in soup.select('div.mw-category div.mw-category-group ul li'):
        link = li.find('a')
        if link and 'href' in link.attrs:
            company_title = link.get_text()
            company_names.add(company_title)
    
    subcategories = soup.find_all('div', class_='CategoryTreeItem')
    for subcat in subcategories:
        subcat_link = subcat.find('a')
        if subcat_link and 'href' in subcat_link.attrs:
            subcat_url = urljoin(BASE_URL, subcat_link['href'])
            process_category(subcat_url)
            time.sleep(DELAY_BETWEEN_REQUESTS)  
    
    next_page = soup.find('a', string='next page') 
    if next_page and 'href' in next_page.attrs:
        next_page_url = urljoin(BASE_URL, next_page['href'])
        process_category(next_page_url)
        time.sleep(DELAY_BETWEEN_REQUESTS) 

def fetch_company_details(company_name):
    print(f"Fetching details for {company_name}...")
    try:
        page = wiki_wiki.page(company_name)
        if not page.exists():
            print(f"Wikipedia page does not exist for {company_name}.")
            return
        
        company_data = {
            'Company Name': company_name,
            'Description': page.summary,
            'Headcount': '',
            'Industry': '',
            'Founding Year': '',
            'Revenue': '',
            'Website': '',
            'Address': ''
        }
        
        page_html = requests.get(page.fullurl, headers=HEADERS).content
        page_soup = BeautifulSoup(page_html, 'html.parser')
        
        infobox = None
        for cls in ['infobox vcard', 'infobox', 'infobox hproduct', 'infobox geography vcard']:
            infobox = page_soup.find('table', {'class': cls})
            if infobox:
                break
        
        if infobox:
            year_regex = re.compile(r'\b\d{4}\b')
            
            for row in infobox.find_all('tr'):
                header = row.find(['th', 'td'], {'scope': 'row'})
                value = row.find('td')
                if header and value:
                    header_text = header.get_text(separator=' ', strip=True)
                    value_text = value.get_text(separator=' ', strip=True)
                    
                    if 'Industry' in header_text or 'Type' in header_text:
                        company_data['Industry'] = value_text
                    elif 'Founded' in header_text or 'Foundation' in header_text or 'Established' in header_text:
                        year_match = year_regex.search(value_text)
                        if year_match:
                            company_data['Founding Year'] = year_match.group()
                    elif 'Headquarters' in header_text:
                        company_data['Address'] = value_text
                    elif 'Revenue' in header_text:
                        company_data['Revenue'] = value_text
                    elif 'Number of employees' in header_text or 'Employees' in header_text:
                        company_data['Headcount'] = value_text
                    elif 'Website' in header_text:
                        link = value.find('a', href=True)
                        if link:
                            company_data['Website'] = link['href']
                        else:
                            company_data['Website'] = value_text.strip()
        else:
            print(f"No infobox found for {company_name}.")
        
        company_data_list.append(company_data)
    
    except Exception as e:
        print(f"An error occurred while processing {company_name}: {e}")

def main():
    print(f"Starting to scrape companies from {START_CATEGORY_URL}")
    process_category(START_CATEGORY_URL)
    
    print(f"Total unique companies found: {len(company_names)}")
    
    companies_to_process = list(company_names)
    
    for idx, company in enumerate(companies_to_process, 1):
        fetch_company_details(company)
        if idx % 100 == 0:
            print(f"Processed {idx} companies.")
        time.sleep(DELAY_BETWEEN_REQUESTS)  
    
    df = pd.DataFrame(company_data_list)
    
    directory = 'output_data'  
    file_name = 'nyse_companies_details.csv'
    output_file_path = os.path.join(directory, file_name)
    
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    df.to_csv(output_file_path, index=False)
    
    print(f"Data saved to {output_file_path}")

if __name__ == "__main__":
    main()