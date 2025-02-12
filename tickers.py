import requests
import pandas as pd
import time
from datetime import datetime
from ratelimit import limits, sleep_and_retry

CALLS = 5
RATE_LIMIT = 60

@sleep_and_retry
@limits(calls=CALLS, period=RATE_LIMIT)
def call_api(url, params):
   response = requests.get(url, params=params)
   if response.status_code == 429: 
       raise Exception("Rate limit exceeded")
   return response

def get_all_tickers_polygon():
   API_KEY = 'xx'
   base_url = "https://api.polygon.io/v3/reference/tickers"
   
   params = {
       'active': True,
       'limit': 1000,
       'market': 'stocks',
       'type': 'CS',
       'exchange': 'NYSE,NASDAQ',  
       'apiKey': API_KEY
   }
   
   all_tickers = []
   next_url = base_url
   
   print("Fetching US stock tickers from Polygon.io...")
   
   while next_url:
       try:
           response = call_api(next_url, params)
           data = response.json()
           
           if response.status_code != 200:
               print(f"Error: {data.get('error')}")
               break
               
           tickers = data.get('results', [])
           
           for ticker in tickers:
               if (ticker.get('market') == 'stocks' and 
                   ticker.get('type') == 'CS' and 
                   ticker.get('currency_name') == 'USD' and
                   ticker.get('primary_exchange') in ['NYSE', 'NASDAQ']):
                   
                   all_tickers.append({
                       'ticker': ticker.get('ticker'),
                       'name': ticker.get('name'),
                       'exchange': ticker.get('primary_exchange'),
                       'market_cap': ticker.get('market_cap', 0)
                   })
           
           print(f"Fetched {len(all_tickers)} US stocks so far...")
           
           next_url = data.get('next_url')
           if next_url:
               params = {'apiKey': API_KEY}
           
       except Exception as e:
           print(f"Error fetching data: {str(e)}")
           time.sleep(60) 
           continue
   
   df = pd.DataFrame(all_tickers)
   
   if not df.empty:
       df = df.sort_values('market_cap', ascending=False, na_position='last')
   
   df.to_csv('us_stocks.csv', index=False)
   
   with open('us_stock_tickers.txt', 'w') as f:
       for ticker in df['ticker']:
           f.write(f"{ticker}\n")
   
   print(f"\nResults:")
   print(f"Total US stocks found: {len(df)}")
   print(f"Exchanges represented: {df['exchange'].value_counts().to_dict()}")
   print(f"\nFiles saved:")
   print("- us_stocks.csv (detailed info)")
   print("- us_stock_tickers.txt (ticker list)")

   print("\nFirst 10 tickers by market cap:")
   print(df['ticker'].head(10).tolist())
   
   return df['ticker'].tolist()

if __name__ == "__main__":
   tickers = get_all_tickers_polygon()