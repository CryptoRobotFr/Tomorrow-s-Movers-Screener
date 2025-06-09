import asyncio
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import pandas as pd
from openbb import obb

from config import CRYPTO_SYMBOLS, STOCK_SYMBOLS


class MarketDataProvider(ABC):
    """Abstract interface for market data providers.
    
    This allows easy swapping between different data sources
    (Yahoo Finance, Alpha Vantage, CoinGecko, etc.)
    """
    
    @abstractmethod
    async def get_market_data(self, symbols: List[str], period: str = "10D") -> pd.DataFrame:
        """
        Get market data for given symbols.
        
        Args:
            symbols: List of ticker symbols
            period: Time period (1D, 1W, 1M, 3M, 6M, 1Y)
            
        Returns:
            DataFrame with columns: symbol, current_price, price_change_1d, 
            price_change_7d, volume_24h, avg_volume_7d, market_cap
        """
        pass
    
    @abstractmethod
    def search_symbols(self, query: str, limit: int = 50) -> List[Dict]:
        """Search for symbols matching query."""
        pass
    
    @abstractmethod
    def get_top_symbols(self, limit: int = 100) -> List[str]:
        """Get top symbols by market cap."""
        pass


class MockDataProvider(MarketDataProvider):
    """Mock data provider for demonstration purposes.
    
    Replace this with real data providers like:
    - YahooFinanceProvider
    - AlphaVantageProvider  
    - CoinGeckoProvider
    """
    
    def __init__(self):
        self.mock_symbols = STOCK_SYMBOLS + CRYPTO_SYMBOLS
    
    async def get_market_data(self, symbols: List[str], period: str = "10D") -> pd.DataFrame:
        """Generate realistic mock market data."""
        data = []
        
        for symbol in symbols:
            if "-USD" in symbol:  # Crypto
                base_price = random.uniform(0.01, 100000) 
            else:  # Stocks
                base_price = random.uniform(10, 1000)
            
            price_change_1d = random.uniform(-15, 15)
            price_change_7d = price_change_1d + random.uniform(-10, 10)
            
            base_volume = random.uniform(1000000, 100000000)
            volume_multiplier = random.choices([1, 1.5, 2, 3, 5], weights=[60, 20, 10, 7, 3])[0]
            current_volume = base_volume * volume_multiplier
            
            data.append({
                'symbol': symbol,
                'current_price': round(base_price, 2),
                'price_change_1d': round(price_change_1d, 2),
                'price_change_7d': round(price_change_7d, 2),
                'volume_24h': int(current_volume),
                'avg_volume_7d': int(base_volume),
                'volume_ratio': round(current_volume / base_volume, 2)
            })
        
        return pd.DataFrame(data)
    
    def search_symbols(self, query: str, limit: int = 50) -> List[Dict]:
        """Mock symbol search."""
        matches = [s for s in self.mock_symbols if query.upper() in s.upper()]
        return [{"symbol": s, "name": f"{s} Mock Company"} for s in matches[:limit]]
    
    def get_top_symbols(self, limit: int = 100) -> List[str]:
        """Return top mock symbols."""
        return self.mock_symbols[:limit]


class OpenBBDataProvider(MarketDataProvider):
    """OpenBB data provider for real market data.
    
    Uses the OpenBB Platform to fetch real-time stock and crypto data.
    """
    
    def __init__(self):
        
        from config import FMP_API_KEY, OPENBB_PROVIDER
        self.stock_symbols = STOCK_SYMBOLS
        self.crypto_symbols = CRYPTO_SYMBOLS
        self.provider = OPENBB_PROVIDER
        
        if self.provider == "fmp" and FMP_API_KEY:
            obb.user.credentials.fmp_api_key = FMP_API_KEY
        
        print(f"🔌 OpenBB configured with provider: {self.provider}")
    
    async def get_market_data(self, symbols: List[str], period: str = "10D") -> pd.DataFrame:
        """Get real market data using OpenBB with parallel processing."""
        print(f"🔍 Fetching data for {len(symbols)} symbols...")
        
        tasks = [self._fetch_symbol_data_async(symbol, period) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        data = []
        failed_symbols = []
        error_symbols = []
        
        for i, result in enumerate(results):
            symbol = symbols[i]
            if isinstance(result, Exception):
                error_symbols.append(f"{symbol}: {str(result)}")
            elif result is not None:
                data.append(result)
            else:
                failed_symbols.append(symbol)
        
        print(f"📊 Successfully fetched data for {len(data)}/{len(symbols)} symbols")
        if failed_symbols:
            print(f"⚠️ Failed to process: {', '.join(failed_symbols)}")
        if error_symbols:
            print(f"❌ Errors occurred: {', '.join(error_symbols)}")
        
        if len(data) == 0:
            error_msg = """
            ❌ OpenBB Data Fetch Failed
            
            No market data could be retrieved from OpenBB. This could be due to:
            • Network connectivity issues
            • OpenBB API service problems
            • Rate limiting or authentication issues
            • Invalid symbols or API endpoints
            
            Please check:
            1. Your internet connection
            2. OpenBB service status
            3. Try refreshing the data
            
            If problems persist, you may need to switch to mock data in config.py
            """
            raise ConnectionError(error_msg.strip())
        
        return pd.DataFrame(data)
    
    async def _fetch_symbol_data_async(self, symbol: str, period: str) -> Optional[Dict]:
        """Fetch data for a single symbol asynchronously."""
        try:
            historical_data = await self._get_historical_data(symbol, period)
            if historical_data is None:
                return None
            
            return self._process_market_data(symbol, historical_data)
            
        except Exception as e:
            raise Exception(f"Error processing {symbol}: {e}")
    
    async def _get_historical_data(self, symbol: str, period: str = "10D") -> Optional[pd.DataFrame]:
        """Get historical data for volume analysis."""
        try:
            days = {"1D": 10, "1W": 10, "10D": 10, "2W": 14, "1M": 30, "3M": 90, "6M": 180, "1Y": 365}.get(period, 10)
            
            if "-USD" in symbol: 
                data = obb.crypto.price.historical(
                    symbol=symbol.replace("-USD", "").lower(), 
                    interval="1d", 
                    limit=days,
                    provider=self.provider
                )
            else:  
                data = obb.equity.price.historical(
                    symbol=symbol, 
                    interval="1d", 
                    limit=days,
                    provider=self.provider
                )
            
            if data is not None and hasattr(data, 'results') and data.results:
                if hasattr(data.results[0], '__dict__'):
                    df = pd.DataFrame([item.__dict__ for item in data.results])
                else:
                    df = pd.DataFrame(data.results)
                return df
            
            return None
            
        except Exception:
            return None
    
    def _process_market_data(self, symbol: str, historical_data: pd.DataFrame) -> Optional[Dict]:
        """Process historical data to extract all needed metrics."""
        
        if len(historical_data) < 2:
            raise ValueError(f"Insufficient historical data for {symbol}. Need at least 2 days, got {len(historical_data)}")
            
        latest_close = historical_data.iloc[-1]['close']
        prev_close = historical_data.iloc[-2]['close']
        price_change_1d = ((latest_close - prev_close) / prev_close * 100)
        
        if len(historical_data) < 7:
            raise ValueError(f"Insufficient historical data for {symbol}. Need at least 7 days, got {len(historical_data)}")
            
        week_ago_close = historical_data.iloc[-7]['close']
        price_change_7d = ((latest_close - week_ago_close) / week_ago_close * 100)
        
        current_volume = historical_data.iloc[-1]['volume']
        avg_volume_7d = historical_data['volume'].tail(7).mean()
        volume_ratio = current_volume / avg_volume_7d
        
        return {
            'symbol': symbol,
            'current_price': round(float(latest_close), 2),
            'price_change_1d': round(float(price_change_1d), 2),
            'price_change_7d': round(float(price_change_7d), 2),
            'volume_24h': int(current_volume),
            'avg_volume_7d': int(avg_volume_7d),
            'volume_ratio': round(float(volume_ratio), 2)
        }
    
    def search_symbols(self, query: str, limit: int = 50) -> List[Dict]:
        """Search for symbols matching query."""
        try:
            stock_matches = [s for s in self.stock_symbols if query.upper() in s.upper()]
            crypto_matches = [s for s in self.crypto_symbols if query.upper() in s.upper()]
            all_matches = stock_matches + crypto_matches
            
            return [{"symbol": s, "name": f"{s} (OpenBB)"} for s in all_matches[:limit]]
            
        except Exception as e:
            print(f"Error searching symbols: {e}")
            return []
    
    def get_top_symbols(self, limit: int = 100) -> List[str]:
        """Get top symbols by market cap."""
        all_symbols = self.stock_symbols + self.crypto_symbols
        return all_symbols[:limit]


def create_data_provider(provider_type: str = "mock") -> MarketDataProvider:
    """Factory function to create data providers."""
    if provider_type == "mock":
        return MockDataProvider()
    elif provider_type == "openbb":
        return OpenBBDataProvider()
    else:
        raise ValueError(f"Unknown provider type: {provider_type}") 