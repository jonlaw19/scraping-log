import requests
import time

# Your Polygon.io API key
API_KEY = "cH9BirWQYxJeQNLwYIs6itnmoYgHMxpU"

# Base URL
BASE_URL = "https://api.polygon.io/v3/reference/tickers"

def fetch_all_tickers():
    """Fetch a list of all tickers from Polygon.io"""
    tickers = []
    url = BASE_URL
    params = {
        "apiKey": API_KEY,
        "limit": 1000  # Maximum limit per request
    }

    while url:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            tickers.extend(data.get("results", []))
            # Check if there is a next_url for pagination
            url = data.get("next_url")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            break
        time.sleep(0.25)  # Add delay to respect API rate limits
    return tickers

def fetch_market_cap(ticker):
    """Fetch market cap and company name for a given ticker"""
    url = f"https://api.polygon.io/v3/reference/tickers/{ticker}"
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
    all_tickers = fetch_all_tickers()
    print(f"Found {len(all_tickers)} tickers.")

    results = []
    for ticker_data in all_tickers:
        ticker = ticker_data["ticker"]
        company_name, market_cap = fetch_market_cap(ticker)
        if company_name and market_cap:
            results.append((ticker, company_name, market_cap))
            print(f"{ticker}: {company_name}, Market Cap: {market_cap}")
        time.sleep(0.5)  # Add delay to respect API rate limits

    # Save to CSV
    import csv
    with open("market_cap_data.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Ticker", "Company Name", "Market Cap"])
        writer.writerows(results)

    print("Data saved to market_cap_data.csv.")
