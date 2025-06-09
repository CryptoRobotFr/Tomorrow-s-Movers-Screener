import asyncio
import sys

from openbb import obb

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# Get this from https://site.financialmodelingprep.com/developer/docs after creating an account
FMP_API_KEY = ""  

ticker = "NVDA"  

obb.user.credentials.fmp_api_key = FMP_API_KEY 

try:
    df = obb.equity.price.historical(
        symbol=ticker,
        start_date="2020-01-01",
        provider="fmp" 
    ).to_df()
    
    print(f"Successfully loaded data for {ticker}")
    print("\nFirst 5 rows:")
    print(df.head())
    print("\nLast 5 rows:")
    print(df.tail())
    
except Exception as e:
    print(f"Failed to load data for {ticker}: {e}")
