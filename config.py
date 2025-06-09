# ==============================================================================
# DATA SOURCE CONFIGURATION
# ==============================================================================

# Default data provider (change this to switch data sources)
DEFAULT_DATA_PROVIDER = "openbb"  # Options: "openbb" (real data) or "mock" (demo data)
# DEFAULT_DATA_PROVIDER = "mock"

# Cache configuration
CACHE_TTL_SECONDS = 300  # 5 minutes cache for market data 

# OpenBB Data Provider Choice
OPENBB_PROVIDER = "fmp"

# API Keys
FMP_API_KEY = ""


# ==============================================================================
# SYMBOL CONFIGURATION
# ==============================================================================

# Stock symbols to screen
# Add/remove symbols here to change what assets are screened
STOCK_SYMBOLS = [
    # Tech Giants
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "NFLX",
    
    # Enterprise & Software
    "ORCL", "CRM", "ADBE", "SNOW", "PLTR", "ZM", "DOCU", "TWLO",
    
    # Semiconductors & Hardware
    "AMD", "INTC",
    
    # Finance & Fintech
    "PYPL", "SQ", "COIN", "HOOD",
    
    # Transportation & Consumer
    "UBER", "ABNB", "TSLA",
    
    # Entertainment & Media
    "ROKU", "PINS", "SNAP", "SPOT", "RBLX", "SHOP"
]

# Cryptocurrency symbols to screen
CRYPTO_SYMBOLS = [
    # Major Cryptocurrencies
    "BTC-USD", "ETH-USD"
]

# ==============================================================================
# SCREENING PARAMETERS
# ==============================================================================

# Default screening criteria (educational starting points)
DEFAULT_SCREENING_PARAMS = {
    "min_volume_ratio": 2.0,        # 200% of normal volume (indicates unusual activity)
    "min_price_change_1d": -50.0,   # Allow both up and down movements
    "max_price_change_1d": 50.0,    # Cap extreme movements to avoid outliers
    "min_market_cap": 1_000_000,    # $1M minimum (focuses on liquid assets)
    "max_results": 20,              # Top 20 candidates
}

# Parameter ranges for Streamlit sliders (helps with UI boundaries)
PARAM_RANGES = {
    "volume_ratio": (1.0, 10.0, 0.1),      # (min, max, step)
    "price_change": (-100.0, 100.0, 1.0),   # (min, max, step)
    "market_cap": (100_000, 10_000_000_000, 100_000),  # (min, max, step)
    "max_results": (5, 50, 5),              # (min, max, step)
}

# ==============================================================================
# UI CONFIGURATION
# ==============================================================================

# Streamlit page configuration
PAGE_CONFIG = {
    "page_title": "Tomorrow's Movers Screener",
    "page_icon": "📈",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Color scheme for different momentum types
MOMENTUM_COLORS = {
    "bullish": "#00C851",    # Green
    "bearish": "#FF4444",    # Red
    "neutral": "#33B5E5",    # Blue
}

# Chart configuration
CHART_CONFIG = {
    "height": 400,
    "use_container_width": True,
    "theme": "streamlit" 
}

# Sample educational queries for the screener
EXAMPLE_SCENARIOS = {
    "High Volume Breakouts": {
        "min_volume_ratio": 3.0,
        "min_price_change_1d": 5.0,
        "max_price_change_1d": 50.0,
        "min_market_cap": 1_000_000,
        "max_results": 20,
        "description": "Find assets breaking out with high volume"
    },
    
    "Volume Spike Dips": {
        "min_volume_ratio": 3.0,
        "min_price_change_1d": -50.0,
        "max_price_change_1d": -5.0,
        "min_market_cap": 1_000_000,
        "max_results": 20,
        "description": "Find oversold assets with unusual volume"
    },
    
    "Moderate Momentum": {
        "min_volume_ratio": 1.5,
        "min_price_change_1d": -10.0,
        "max_price_change_1d": 10.0,
        "min_market_cap": 1_000_000,
        "max_results": 20,
        "description": "Conservative screening for steady movers"
    }
} 