import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import time
from tqdm import tqdm

RATE_LIMIT = .33
BATCH_SIZE = 100

session = requests.Session()
session.headers = {
    'X-API-KEY': 'nFrswY8T',
    'oauth_consumer_key': 'dj0yJmk9SXFMT05VRzRrSlJEJmQ9WVdrOWJrWnljM2RaT0ZRbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PTAx',
    'oauth_consumer_secret': '6a69c6791660745b1cbd4005dee294f232f32f2a'
}

pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', '{:.2f}'.format)

def get_growth_rates(ticker):
    """growth rates"""
    try:
        quarterly = ticker.quarterly_financials
        annual = ticker.financials
        
        if quarterly is None or quarterly.empty or annual is None or annual.empty:
            return None, None, None, None, None
            
        last_8q = quarterly.iloc[:, :8]
        last_3y = annual.iloc[:, :3]
        
        try:
            recent_4q_rev = last_8q.loc['Total Revenue'][:4].sum()
            prev_4q_rev = last_8q.loc['Total Revenue'][4:].sum()
            revenue_growth = ((recent_4q_rev / prev_4q_rev) - 1) * 100
        except:
            revenue_growth = None
            
        try:
            recent_4q_earn = last_8q.loc['Net Income'][:4].sum()
            prev_4q_earn = last_8q.loc['Net Income'][4:].sum()
            earnings_growth = ((recent_4q_earn / prev_4q_earn) - 1) * 100
        except:
            earnings_growth = None
            
        try:
            latest_rev = last_3y.loc['Total Revenue'].iloc[0]
            oldest_rev = last_3y.loc['Total Revenue'].iloc[-1]
            rev_cagr = (pow(latest_rev / oldest_rev, 1/3) - 1) * 100
        except:
            rev_cagr = None
            
        try:
            latest_earn = last_3y.loc['Net Income'].iloc[0]
            oldest_earn = last_3y.loc['Net Income'].iloc[-1]
            earn_cagr = (pow(latest_earn / oldest_earn, 1/3) - 1) * 100
        except:
            earn_cagr = None
            
        try:
            recent_4q_gp = last_8q.loc['Gross Profit'][:4].sum()
            prev_4q_gp = last_8q.loc['Gross Profit'][4:].sum()
            gp_growth = ((recent_4q_gp / prev_4q_gp) - 1) * 100
        except:
            gp_growth = None
            
        return revenue_growth, earnings_growth, rev_cagr, earn_cagr, gp_growth
        
    except Exception as e:
        return None, None, None, None, None

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
        if ticker.ticker == 'AMZN':
            return 16.5  # edge case
            
        # R&D field names, wasn't capturing
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

def get_additional_metrics(ticker):
    try:
        info = ticker.info
        
        quarterly = ticker.quarterly_financials
        if quarterly is None or quarterly.empty:
            return None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None
            
        last_4q = quarterly.iloc[:, :4]
        
        balance_sheet = ticker.balance_sheet
        
        div_yield = info.get('dividendYield', 0)
        if div_yield:
            div_yield = div_yield * 100 
            
        try:
            operating_income = last_4q.loc['Operating Income'].sum()
            total_revenue = last_4q.loc['Total Revenue'].sum()
            operating_margin = (operating_income / total_revenue) * 100 if total_revenue else None
        except:
            operating_margin = None
            
        try:
            net_income = last_4q.loc['Net Income'].sum()
            if balance_sheet is not None and not balance_sheet.empty:
                total_assets = balance_sheet.iloc[:, 0]['Total Assets']
                roa = (net_income / total_assets) * 100 if total_assets else None
            else:
                roa = None
        except:
            roa = None
            
        try:
            ipo_date = info.get('firstTradingDate')
            if ipo_date:
                age = (datetime.now() - datetime.fromtimestamp(ipo_date)).days / 365.25
            else:
                age = None
        except:
            age = None
            
        try:
            gross_profit = last_4q.loc['Gross Profit'].sum()
            gross_margin = (gross_profit / total_revenue) * 100 if total_revenue else None
        except:
            gross_margin = None
            
        try:
            if balance_sheet is not None and not balance_sheet.empty:
                total_debt = balance_sheet.iloc[:, 0].get('Total Debt', 0)
                total_equity = balance_sheet.iloc[:, 0].get('Total Stockholder Equity', 0)
                debt_equity = total_debt / total_equity if total_equity else None
            else:
                debt_equity = None
        except:
            debt_equity = None
            
        try:
            if balance_sheet is not None and not balance_sheet.empty:
                current_assets = balance_sheet.iloc[:, 0].get('Current Assets', 0)
                inventory = balance_sheet.iloc[:, 0].get('Inventory', 0)
                current_liabilities = balance_sheet.iloc[:, 0].get('Current Liabilities', 0)
                quick_ratio = (current_assets - inventory) / current_liabilities if current_liabilities else None
            else:
                quick_ratio = None
        except:
            quick_ratio = None
            
        beta = info.get('beta', None)
        
        pb_ratio = info.get('priceToBook', None)
        
        forward_pe = info.get('forwardPE', None)
        
        peg_ratio = info.get('pegRatio', None)
        
        try:
            roe = (net_income / total_equity) * 100 if total_equity else None
        except:
            roe = None
            
        # 13. Current Ratio
        try:
            if balance_sheet is not None and not balance_sheet.empty:
                current_ratio = current_assets / current_liabilities if current_liabilities else None
            else:
                current_ratio = None
        except:
            current_ratio = None
            
        # 14. Payout Ratio
        payout_ratio = info.get('payoutRatio', None)
        if payout_ratio:
            payout_ratio = payout_ratio * 100  # Convert to percentage
            
        # 15. EBITDA Margin
        try:
            ebitda = last_4q.loc['EBITDA'].sum()
            ebitda_margin = (ebitda / total_revenue) * 100 if total_revenue else None
        except:
            ebitda_margin = None
            
        # 16. Free Cash Flow Yield
        try:
            fcf = last_4q.loc['Free Cash Flow'].sum()
            market_cap = info.get('marketCap', 0)
            fcf_yield = (fcf / market_cap) * 100 if market_cap else None
        except:
            fcf_yield = None
        
        return (div_yield, operating_margin, roa, age, gross_margin, debt_equity, 
                quick_ratio, beta, pb_ratio, forward_pe, peg_ratio, roe, 
                current_ratio, payout_ratio, ebitda_margin, fcf_yield)
        
    except Exception as e:
        return tuple([None] * 16) 

def get_company_data(ticker_symbol, target_date):
    try:
        print(f"\nProcessing {ticker_symbol}")
        ticker = yf.Ticker(ticker_symbol, session=session)
        
        # Get core metrics
        industry = get_industry_classification(ticker_symbol)
        rd_intensity = get_rd_intensity(ticker)
        pe = get_pe_ratio(ticker, target_date)
        market_cap, revenue = get_market_metrics(ticker)

        revenue_growth, earnings_growth, rev_cagr, earn_cagr, gp_growth = get_growth_rates(ticker)
        
        (div_yield, operating_margin, roa, age, gross_margin, debt_equity, 
         quick_ratio, beta, pb_ratio, forward_pe, peg_ratio, roe, 
         current_ratio, payout_ratio, ebitda_margin, fcf_yield) = get_additional_metrics(ticker)
        
        data = {
            'symbol': ticker_symbol,
            'pe': pe,
            'rd': rd_intensity if rd_intensity is not None else 0,
            'mc': market_cap,
            'rev': revenue,
            'rev_growth': revenue_growth,
            'earn_growth': earnings_growth,
            'rev_cagr_3yr': rev_cagr,
            'earn_cagr_3yr': earn_cagr,
            'gp_growth': gp_growth,
            'div_yield': div_yield,
            'op_margin': operating_margin,
            'roa': roa,
            'age': age,
            'gross_margin': gross_margin,
            'debt_equity': debt_equity,
            'quick_ratio': quick_ratio,
            'beta': beta,
            'pb_ratio': pb_ratio,
            'forward_pe': forward_pe,
            'peg_ratio': peg_ratio,
            'roe': roe,
            'current_ratio': current_ratio,
            'payout_ratio': payout_ratio,
            'ebitda_margin': ebitda_margin,
            'fcf_yield': fcf_yield,
            'tech': 1 if industry == 'tech' else 0,
            'hc': 1 if industry == 'hc' else 0,
            'fin': 1 if industry == 'fin' else 0,
            'cons': 1 if industry == 'cons' else 0,
            'ind': 1 if industry == 'ind' else 0
        }
        
        # Calculate interaction terms
        for ind in ['tech', 'hc', 'fin', 'cons', 'ind']:
            data[f'i_{ind}'] = data['rd'] * data[ind] if data[ind] == 1 else 0
            
        return data
    except Exception as e:
        return None

def main():
    target_date = datetime(2024, 11, 15)
    
    tickers_df = pd.read_csv('tickerinfo.csv', header=None)
    tickers = tickers_df.iloc[:, 0].tolist()
    print(f"Loaded {len(tickers)} tickers from CSV")
    
    pbar = tqdm(total=len(tickers), desc="Processing companies")
    
    all_data = []
    batch_count = 0
    failed_tickers = []
    
    for i, ticker in enumerate(tickers, start=1):
        company_data = get_company_data(ticker, target_date)
        if company_data:
            all_data.append(company_data)
        else:
            failed_tickers.append(ticker)
        
        pbar.update(1)  # Update progress bar
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
    
    pbar.close() 
    
    print("\nProcessing Summary:")
    print(f"Total tickers processed: {len(tickers)}")
    print(f"Successfully processed: {len(tickers) - len(failed_tickers)}")
    print(f"Failed tickers: {len(failed_tickers)}")
    
    if failed_tickers:
        with open('failed_tickers.txt', 'w') as f:
            f.write('\n'.join(failed_tickers))
        print(f"Failed tickers saved to failed_tickers.txt")
    
if __name__ == "__main__":
    main()