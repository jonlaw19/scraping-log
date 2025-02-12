import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import logging
import threading

# ======================== Configuration ========================

API_ENDPOINT = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "Public_Revenue_Mission/3.6 (jwlsplam@gmail.com)"  
BATCH_SIZE = 50 
OUTPUT_DIR = "output_data"
CSV_BATCH_SIZE = 10000
MAX_WORKERS = 5 
RETRIES = 3  
DELAY_BETWEEN_REQUESTS = 0.2  

# ======================== Logging Setup ========================

logging.basicConfig(
    filename='scraping.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ======================== Global Variables ========================

company_data_list = []
data_lock = threading.Lock()
csv_batch_number = 1
batch_lock = threading.Lock()

# ======================== Utility Functions ========================

def read_company_names(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            companies = [line.strip() for line in f if line.strip()]
        logging.info(f"Loaded {len(companies)} company names from {file_path}.")
        return companies
    except Exception as e:
        logging.error(f"Error reading company names from {file_path}: {e}")
        return []

def chunk_list(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

def extract_infobox_data(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    infobox = soup.find('table', {'class': re.compile(r'infobox')})
    data = {
        'Description': '',
        'Headcount': '',
        'Industry': '',
        'Founding Year': '',
        'Revenue': '',
        'Website': '',
        'Address': ''
    }
    if infobox:
        for row in infobox.find_all('tr'):
            header = row.find(['th', 'td'], {'scope': 'row'})
            value = row.find('td')
            if header and value:
                header_text = header.get_text(separator=' ', strip=True)
                value_text = value.get_text(separator=' ', strip=True)
                
                # Map headers to data fields
                if 'Industry' in header_text or 'Type' in header_text:
                    data['Industry'] = value_text
                elif any(x in header_text for x in ['Founded', 'Foundation', 'Established']):
                    year_match = re.search(r'\b\d{4}\b', value_text)
                    if year_match:
                        data['Founding Year'] = year_match.group()
                elif 'Headquarters' in header_text or 'Location' in header_text:
                    data['Address'] = value_text
                elif 'Revenue' in header_text:
                    data['Revenue'] = value_text
                elif any(x in header_text for x in ['Number of employees', 'Employees', 'Headcount']):
                    data['Headcount'] = value_text
                elif 'Website' in header_text:
                    link = value.find('a', href=True)
                    if link:
                        data['Website'] = link['href']
                    else:
                        data['Website'] = value_text
    return data

def save_to_csv(data_batch, batch_number):
    df = pd.DataFrame(data_batch)
    csv_filename = f"companies_batch_{batch_number}.csv"
    csv_path = os.path.join(OUTPUT_DIR, csv_filename)
    try:
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        logging.info(f"Saved {len(data_batch)} records to {csv_path}.")
    except Exception as e:
        logging.error(f"Error saving CSV {csv_path}: {e}")

def process_batch(session, company_batch):
    params = {
        "action": "query",
        "titles": "|".join(company_batch),
        "prop": "revisions",
        "rvprop": "content",
        "format": "json",
        "redirects": 1,
        "formatversion": 2
    }
    headers = {
        "User-Agent": USER_AGENT
    }
    
    for attempt in range(RETRIES):
        try:
            response = session.get(API_ENDPOINT, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            break  # Successful request
        except requests.exceptions.RequestException as e:
            wait = 2 ** attempt
            logging.warning(f"Batch {company_batch} - Attempt {attempt + 1} failed: {e}. Retrying in {wait} seconds...")
            time.sleep(wait)
    else:
        logging.error(f"Batch {company_batch} - All {RETRIES} attempts failed.")
        return 
    
    if 'query' not in data:
        logging.error(f"Batch {company_batch} - No 'query' in response.")
        return
    
    pages = data['query'].get('pages', [])
    for page in pages:
        company_name = page.get('title', '')
        if 'missing' in page:
            # Page does not exist
            company_data = {
                'Company Name': company_name,
                'Description': '',
                'Headcount': '',
                'Industry': '',
                'Founding Year': '',
                'Revenue': '',
                'Website': '',
                'Address': ''
            }
        else:
            page_title = company_name.replace(' ', '_')
            page_url = f"https://en.wikipedia.org/wiki/{page_title}"
            try:
                page_response = session.get(page_url, headers=headers, timeout=10)
                page_response.raise_for_status()
                description = ''
                soup = BeautifulSoup(page_response.content, 'html.parser')
                first_paragraph = soup.find('p')
                if first_paragraph:
                    description = first_paragraph.get_text(separator=' ', strip=True)
                infobox_data = extract_infobox_data(page_response.content)
                company_data = {
                    'Company Name': company_name,
                    'Description': description,
                    'Headcount': infobox_data['Headcount'],
                    'Industry': infobox_data['Industry'],
                    'Founding Year': infobox_data['Founding Year'],
                    'Revenue': infobox_data['Revenue'],
                    'Website': infobox_data['Website'],
                    'Address': infobox_data['Address']
                }
            except requests.exceptions.RequestException as e:
                logging.error(f"Company {company_name} - Failed to retrieve page: {e}")
                company_data = {
                    'Company Name': company_name,
                    'Description': '',
                    'Headcount': '',
                    'Industry': '',
                    'Founding Year': '',
                    'Revenue': '',
                    'Website': '',
                    'Address': ''
                }
            except Exception as e:
                logging.error(f"Company {company_name} - Error parsing page: {e}")
                company_data = {
                    'Company Name': company_name,
                    'Description': '',
                    'Headcount': '',
                    'Industry': '',
                    'Founding Year': '',
                    'Revenue': '',
                    'Website': '',
                    'Address': ''
                }
    
        with data_lock:
            company_data_list.append(company_data)
            # If CSV_BATCH_SIZE is reached, save to CSV
            if len(company_data_list) >= CSV_BATCH_SIZE:
                global csv_batch_number
                current_batch = company_data_list[:CSV_BATCH_SIZE]
                company_data_list[:] = company_data_list[CSV_BATCH_SIZE:]
                save_to_csv(current_batch, csv_batch_number)
                csv_batch_number += 1

def main():
    global csv_batch_number
    csv_batch_number = 1  
    
    company_names = read_company_names('company_names.txt') 
    total_companies = len(company_names)
    if total_companies == 0:
        logging.error("No company names to process. Exiting.")
        return
    logging.info(f"Starting to process {total_companies} companies.")
    
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    
    # Create batches
    company_batches = list(chunk_list(company_names, BATCH_SIZE))
    total_batches = len(company_batches)
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all batches to the executor
        futures = [executor.submit(process_batch, session, batch) for batch in company_batches]
        
        for _ in tqdm(as_completed(futures), total=total_batches, desc="Processing Batches"):
            pass  # All processing is handled in process_batch
            
    with data_lock:
        if company_data_list:
            save_to_csv(company_data_list, csv_batch_number)
            csv_batch_number += 1
            company_data_list.clear()
    
    logging.info("Scraping completed successfully.")

if __name__ == "__main__":
    main()