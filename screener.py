from typing import Dict

import pandas as pd

from data_provider import MarketDataProvider


class TomorrowsMoversScreener:
    """
    Screener to find potential "tomorrow's movers" based on:
    1. Volume spikes (unusual trading activity)
    2. Price momentum (directional movement)
    """
    
    def __init__(self, data_provider: MarketDataProvider):
        self.data_provider = data_provider
    
    async def screen_movers(self, 
                     min_volume_ratio: float = 2.0,
                     min_price_change_1d: float = -50.0,
                     max_price_change_1d: float = 50.0) -> pd.DataFrame:
        """
        Find potential movers based on volume and momentum criteria.
        
        Args:
            min_volume_ratio: Minimum volume vs 7-day average (2.0 = 200% of normal)
            min_price_change_1d: Minimum 1-day price change %
            max_price_change_1d: Maximum 1-day price change %
            
        Returns:
            Filtered DataFrame sorted by potential (volume_ratio * abs(price_change))
        """
        
        symbols = self.data_provider.get_top_symbols(limit=100)
        
        df = await self.data_provider.get_market_data(symbols)
        
        filtered_df = self._apply_filters(
            df, min_volume_ratio, min_price_change_1d, 
            max_price_change_1d
        )
        
        filtered_df = self._calculate_momentum_score(filtered_df)
        
        return filtered_df
    
    def _apply_filters(self, df: pd.DataFrame, 
                      min_volume_ratio: float,
                      min_price_change_1d: float,
                      max_price_change_1d: float) -> pd.DataFrame:
        """Apply screening filters to the dataframe."""
        
        df = df[df['volume_ratio'] >= min_volume_ratio]
        
        df = df[
            (df['price_change_1d'] >= min_price_change_1d) & 
            (df['price_change_1d'] <= max_price_change_1d)
        ]
        
        return df.copy()
    
    def _calculate_momentum_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate a momentum score combining volume spike and price momentum.
        Higher score = more interesting potential mover.
        """
        if len(df) == 0:
            return df
        
        df['trend_consistency'] = 1.0  # Start with base score
        
        same_direction = (df['price_change_1d'] * df['price_change_7d']) > 0
        df.loc[same_direction, 'trend_consistency'] = 1.5
        
        df['momentum_score'] = (
            df['volume_ratio'] * 
            abs(df['price_change_1d']) * 
            df['trend_consistency']
        ).round(2)
        
        df = df.sort_values('momentum_score', ascending=False)
        
        return df
    
    def get_screening_summary(self, df: pd.DataFrame) -> Dict:
        """Generate a summary of screening results."""
        if len(df) == 0:
            return {
                "total_found": 0,
                "avg_volume_ratio": 0,
                "avg_momentum_score": 0,
                "top_categories": []
            }
        
        bullish = df[df['price_change_1d'] > 0]
        bearish = df[df['price_change_1d'] < 0]
        
        categories = []
        if len(bullish) > 0:
            categories.append(f"Bullish Momentum: {len(bullish)} assets")
        if len(bearish) > 0:
            categories.append(f"Bearish Momentum: {len(bearish)} assets")
        
        return {
            "total_found": len(df),
            "avg_volume_ratio": round(df['volume_ratio'].mean(), 2),
            "avg_momentum_score": round(df['momentum_score'].mean(), 2),
            "top_categories": categories
        }
    
    def format_for_display(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format the dataframe for nice display in Streamlit."""
        if len(df) == 0:
            return pd.DataFrame()
        
        display_df = df[[
            'symbol', 'current_price', 'price_change_1d', 'price_change_7d',
            'volume_ratio', 'momentum_score'
        ]].copy()
        
        display_df['current_price'] = display_df['current_price'].apply(lambda x: f"${x:,.2f}")
        display_df['price_change_1d'] = display_df['price_change_1d'].apply(
            lambda x: f"{'📈' if x > 0 else '📉'} {x:+.1f}%"
        )
        display_df['price_change_7d'] = display_df['price_change_7d'].apply(
            lambda x: f"{'📈' if x > 0 else '📉'} {x:+.1f}%"
        )
        display_df['volume_ratio'] = display_df['volume_ratio'].apply(lambda x: f"{x:.1f}x")
        
        display_df.columns = [
            'Symbol', 'Price', '1D Change', '7D Change', 
            'Volume Spike', 'Momentum Score'
        ]
        
        return display_df 