import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import time

RATE_LIMIT = 1
BATCH_SIZE = 100

session = requests.Session()
session.headers = {
    'X-API-KEY': 'nFrswY8T',
    'oauth_consumer_key': 'dj0yJmk9SXFMT05VRzRrSlJEJmQ9WVdrOWJrWnljM2RaT0ZRbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PTAx',
    'oauth_consumer_secret': '6a69c6791660745b1cbd4005dee294f232f32f2a'
}

pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', '{:.2f}'.format)

def get_industry_classification(ticker_symbol):
   try:
       ticker = yf.Ticker(ticker_symbol, session=session)
       sector = ticker.info.get('sector', 'Unknown')
       industry = ticker.info.get('industry', 'Unknown')
       
       if ticker_symbol in overrides:
           return overrides[ticker_symbol]
       
       if sector in ['Information Technology', 'Technology']:
           return 'tech'
       elif industry in ['Software', 'Internet Software & Services', 
                        'IT Services', 'Semiconductors', 
                        'Technology Hardware', 'Electronic Components',
                        'Consumer Electronics', 'Internet Content & Information',
                        'Internet Retail', 'Semiconductor Equipment & Materials']:
           return 'tech'
       elif sector == 'Health Care':
           return 'hc'
       elif industry in ['Biotechnology', 'Drug Manufacturers', 
                        'Medical Devices', 'Medical Instruments & Supplies',
                        'Healthcare Plans', 'Pharmaceutical Retail']:
           return 'hc'
       elif sector == 'Financials':
           return 'fin'
       elif industry in ['Banks', 'Insurance', 'Asset Management',
                        'Credit Services', 'Capital Markets',
                        'Financial Data & Stock Exchanges']:
           return 'fin'
       elif sector in ['Consumer Discretionary', 'Consumer Staples', 
                      'Consumer Cyclical', 'Consumer Defensive']:
           return 'cons'
       elif industry in ['Retail', 'Restaurants', 'Apparel Retail',
                        'Packaged Foods', 'Beverages', 'Household Products',
                        'Personal Products', 'Department Stores',
                        'Specialty Retail', 'Auto Manufacturers',
                        'Entertainment', 'Hotels & Resorts']:
           return 'cons'
       elif sector == 'Industrials':
           return 'ind'
       elif industry in ['Aerospace & Defense', 'Industrial Manufacturing',
                        'Airlines', 'Farm & Heavy Construction Machinery',
                        'Engineering & Construction', 'Business Equipment',
                        'Transportation & Logistics', 'Waste Management',
                        'Professional Services', 'Consulting Services']:
           return 'ind'
       else:
           return 'other'
           
   except Exception as e:
       return 'unknown'

def get_rd_intensity(ticker):
   try:
       quarterly = ticker.quarterly_financials
       if quarterly is None or quarterly.empty:
           return None

       rd_fields = [
           'Research And Development',
           'Technology And Content',          
           'Technology And Development',      
           'Research Development',
           'Technology Development',
           'Development And Technology',
           'Product Development',
           'R&D Expense',
           'Research And Development Expense'
       ]
       
       last_4q = quarterly.iloc[:, :4]
       
       ttm_rd = 0
       found_fields = []
       for field in rd_fields:
           if field in last_4q.index:
               field_sum = last_4q.loc[field].sum()
               ttm_rd += field_sum
               found_fields.append(f"{field}: {field_sum:,.0f}")
       
       ttm_revenue = last_4q.loc['Total Revenue'].sum()
       
       rd_intensity = (ttm_rd / ttm_revenue) * 100 if ttm_revenue else None
       
       if rd_intensity:
           if rd_intensity > 100:
               return None
           
       return rd_intensity
       
   except Exception as e:
       return None

def get_pe_ratio(ticker, price_date):
   try:
       price_data = ticker.history(start=price_date, end=price_date + timedelta(days=1))
       if price_data.empty:
           return None
       
       price = price_data['Close'].iloc[0]
       
       quarterly = ticker.quarterly_financials
       if quarterly is None or quarterly.empty:
           return None
           
       last_4q = quarterly.iloc[:, :4]
       ttm_earnings = last_4q.loc['Net Income'].sum()
       
       shares = ticker.info.get('sharesOutstanding', 0)
       if shares <= 0:
           return None
           
       eps = ttm_earnings / shares
       pe = price / eps if eps > 0 else None
       
       if pe and (pe < 0 or pe > 200):
           return None
           
       return pe
   except Exception as e:
       return None

def get_market_metrics(ticker):
   try:
       market_cap = ticker.info.get('marketCap', 0)
       if market_cap > 0:
           market_cap = np.log(market_cap)
       else:
           market_cap = None
           
       quarterly = ticker.quarterly_financials
       if quarterly is not None and not quarterly.empty:
           ttm_revenue = quarterly.iloc[:, :4].loc['Total Revenue'].sum()
           revenue = np.log(ttm_revenue) if ttm_revenue > 0 else None
       else:
           revenue = None
           
       return market_cap, revenue
   except Exception as e:
       return None, None

def get_company_data(ticker_symbol, target_date):
   try:
       print(f"\nProcessing {ticker_symbol}")
       ticker = yf.Ticker(ticker_symbol, session=session)
       
       industry = get_industry_classification(ticker_symbol)
       rd_intensity = get_rd_intensity(ticker)
       pe = get_pe_ratio(ticker, target_date)
       market_cap, revenue = get_market_metrics(ticker)
       
       data = {
           'symbol': ticker_symbol,
           'pe': pe,
           'rd': rd_intensity if rd_intensity is not None else 0,
           'mc': market_cap,
           'rev': revenue,
           'tech': 1 if industry == 'tech' else 0,
           'hc': 1 if industry == 'hc' else 0,
           'fin': 1 if industry == 'fin' else 0,
           'cons': 1 if industry == 'cons' else 0,
           'ind': 1 if industry == 'ind' else 0
       }
       
       for ind in ['tech', 'hc', 'fin', 'cons', 'ind']:
           data[f'i_{ind}'] = data['rd'] * data[ind] if data[ind] == 1 else 0
           
       return data
   except Exception as e:
       return None

def main():
    target_date = datetime(2024, 11, 15)
   
    tickers_df = pd.read_csv('tickerinfo.csv', header=None)
    tickers = tickers_df.iloc[:, 0].tolist()
    print(f"Tickers loaded from CSV: {tickers}")
    
    all_data = []
    batch_count = 0
    for i, ticker in enumerate(tickers, start=1):
        company_data = get_company_data(ticker, target_date)
        if company_data:
            all_data.append(company_data)
        
        time.sleep(RATE_LIMIT)
        
        if i % BATCH_SIZE == 0 or i == len(tickers):
            if all_data:
                df = pd.DataFrame(all_data)
                df['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                if i == BATCH_SIZE:
                    df.to_csv('rd_pe_analysis_data_test.csv', index=False, float_format='%.4f')
                else:
                    df.to_csv('rd_pe_analysis_data_test.csv', mode='a', header=False, index=False, float_format='%.4f')
                
                batch_count += 1
                print(f"\nBatch {batch_count} processed. Total entries: {len(all_data)}")
                all_data = []
   
    print(f"\nData collection complete. Total batches processed: {batch_count}")
    
if __name__ == "__main__":
   main()