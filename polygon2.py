import requests
import time
import csv

# Your Polygon.io API key
API_KEY = "YOUR_API_KEY"

# Base URL
BASE_URL_TICKERS = "https://api.polygon.io/v3/reference/tickers"
BASE_URL_DETAILS = "https://api.polygon.io/v3/reference/tickers/{ticker}"

def fetch_global_tickers(exchange="LSE"):
    """Fetch global tickers from a specific exchange (e.g., LSE for London Stock Exchange)"""
    tickers = []
    url = BASE_URL_TICKERS
    params = {
        "apiKey": API_KEY,
        "limit": 1000,  # Max per request
        "exchange": exchange  # Filter by exchange
    }

    while url:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            tickers.extend(data.get("results", []))
            url = data.get("next_url")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            break
    return tickers

def fetch_market_cap_and_name(ticker):
    """Fetch market cap and company name for a given ticker"""
    url = BASE_URL_DETAILS.format(ticker=ticker)
    params = {"apiKey": API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        details = data.get("results", {})
        return details.get("name"), details.get("market_cap")
    else:
        print(f"Error fetching data for {ticker}: {response.status_code}")
        return None, None

# Main script
if __name__ == "__main__":
    print("Fetching all tickers...")
    exchange = "LSE"  # Example: London Stock Exchange (can change to other exchanges)
    all_tickers = fetch_global_tickers(exchange)
    print(f"Found {len(all_tickers)} tickers from {exchange}.")

    results = []
    for ticker_data in all_tickers:
        ticker = ticker_data["ticker"]
        company_name, market_cap = fetch_market_cap_and_name(ticker)
        if company_name and market_cap:
            results.append((ticker, company_name, market_cap))
            print(f"{ticker}: {company_name}, Market Cap: {market_cap}")
        time.sleep(0.5)  # Add delay to respect API rate limits

    # Save to CSV
    with open("global_market_cap_data.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Ticker", "Company Name", "Market Cap"])
        writer.writerows(results)

    print("Data saved to global_market_cap_data.csv.")
