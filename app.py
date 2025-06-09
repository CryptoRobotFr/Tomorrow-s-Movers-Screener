import asyncio

import plotly.express as px
import streamlit as st

from config import (
    CACHE_TTL_SECONDS,
    DEFAULT_DATA_PROVIDER,
    DEFAULT_SCREENING_PARAMS,
    EXAMPLE_SCENARIOS,
    PAGE_CONFIG,
    PARAM_RANGES,
)
from data_provider import create_data_provider
from screener import TomorrowsMoversScreener

# ==============================================================================
# PAGE SETUP
# ==============================================================================

st.set_page_config(**PAGE_CONFIG)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .explanation-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

@st.cache_data(ttl=CACHE_TTL_SECONDS)  # Cache for 5 minutes - configurable
def load_raw_market_data(provider_type):
    """Load raw market data with longer cache time - independent of filters."""
    data_provider = create_data_provider(provider_type)
    symbols = data_provider.get_top_symbols(limit=100)
    return asyncio.run(data_provider.get_market_data(symbols))

def apply_screening_filters(raw_data_df, min_volume_ratio, min_price_change_1d, max_price_change_1d):
    """Apply screening filters to raw data - no API calls needed."""
    screener = TomorrowsMoversScreener(None)  # No data provider needed for filtering
    
    # Apply filters manually (same logic as in screener)
    filtered_df = raw_data_df[raw_data_df['volume_ratio'] >= min_volume_ratio]
    filtered_df = filtered_df[
        (filtered_df['price_change_1d'] >= min_price_change_1d) & 
        (filtered_df['price_change_1d'] <= max_price_change_1d)
    ]
    
    # Calculate momentum score
    filtered_df = screener._calculate_momentum_score(filtered_df.copy())
    
    return filtered_df

def get_screening_summary(results_df):
    """Get screening summary without creating new data provider."""
    screener = TomorrowsMoversScreener(None)  
    return screener.get_screening_summary(results_df)

def format_for_display(results_df):
    """Format results for display without creating new data provider."""
    screener = TomorrowsMoversScreener(None) 
    return screener.format_for_display(results_df)

def create_momentum_chart(df):
    """Create an interactive chart showing momentum vs volume."""
    if len(df) == 0:
        return None
    
    fig = px.scatter(
        df, 
        x='volume_ratio', 
        y='momentum_score',
        color='price_change_1d',
        hover_data=['symbol', 'current_price', 'price_change_7d'],
        title="Momentum vs Volume Analysis",
        labels={
            'volume_ratio': 'Volume Spike (x normal)',
            'momentum_score': 'Momentum Score',
            'price_change_1d': '1D Price Change (%)'
        },
        color_continuous_scale='RdYlGn'
    )
    
    fig.update_layout(height=500, showlegend=True)
    return fig

# ==============================================================================
# MAIN APPLICATION
# ==============================================================================

def main():
    # Header
    st.markdown('<h1 class="main-header">📈 Tomorrow\'s Movers Screener</h1>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    **Find potential market movers before they move big!** This screener combines volume spikes 
    with price momentum to identify assets that might be tomorrow's big winners (or losers).
    """)
    
    # Sidebar for controls
    with st.sidebar:
        st.header("🎛️ Screening Controls")
        
        # Example scenarios
        st.subheader("Quick Scenarios")
        scenario = st.selectbox(
            "Choose a preset scenario:",
            ["Custom"] + list(EXAMPLE_SCENARIOS.keys()),
            help="Pre-configured screening scenarios for learning"
        )
        
        # Load scenario parameters
        if scenario != "Custom":
            params = EXAMPLE_SCENARIOS[scenario].copy()
            st.info(f"**{scenario}**: {params.pop('description')}")
        else:
            params = DEFAULT_SCREENING_PARAMS.copy()
        
        st.subheader("📊 Screening Parameters")
        
        # Volume ratio filter
        min_volume_ratio = st.slider(
            "Minimum Volume Spike",
            min_value=PARAM_RANGES["volume_ratio"][0],
            max_value=PARAM_RANGES["volume_ratio"][1],
            value=params["min_volume_ratio"],
            step=PARAM_RANGES["volume_ratio"][2],
            help="How much higher than normal volume? (2.0 = 200% of normal)"
        )
        
        # Price change range
        st.write("**Price Change Range (1 Day)**")
        price_range = st.slider(
            "Select price change range (%)",
            min_value=PARAM_RANGES["price_change"][0],
            max_value=PARAM_RANGES["price_change"][1],
            value=(params["min_price_change_1d"], params["max_price_change_1d"]),
            step=PARAM_RANGES["price_change"][2],
            help="Filter by 1-day price movement percentage"
        )
        
        # Refresh button
        if st.button("🔄 Actualiser les Données", type="primary"):
            st.cache_data.clear()
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.empty()
    
    with col1:
        # Loading and screening
        
        with st.spinner("🔍 Analyse des données du marché..."):
            try:
                # Get raw data (cached for 5 minutes)
                raw_data_df = load_raw_market_data(DEFAULT_DATA_PROVIDER)
                
                # Apply filters (no API calls, instant filtering)
                with st.spinner("⚡ Application des filtres (instantané)..."):
                    results_df = apply_screening_filters(raw_data_df, min_volume_ratio, price_range[0], price_range[1])
                
                # Create screener instance for summary
                summary = get_screening_summary(results_df)
                
            except ConnectionError as e:
                # Handle OpenBB connection errors specifically
                st.error("🚫 **Data Connection Failed**")
                st.error(str(e))
                
                # Provide actionable solutions
                st.markdown("### 🔧 **Quick Solutions:**")
                
                col_sol1, col_sol2 = st.columns(2)
                with col_sol1:
                    if st.button("🔄 **Retry Connection**", type="primary"):
                        st.cache_data.clear()
                        st.rerun()
                
                with col_sol2:
                    st.markdown("**Or try mock data:**")
                    st.code('DEFAULT_DATA_PROVIDER = "mock"', language="python")
                    st.caption("Change this in config.py for testing")
                
                return
                
            except Exception as e:
                st.error(f"❌ **Unexpected Error:** {str(e)}")
                st.markdown("Please try refreshing the page or check the logs for more details.")
                return
        
        # Results summary
        st.subheader("📊 Screening Results")
        
        if summary["total_found"] > 0:
            # Summary metrics
            metric_cols = st.columns(3)
            with metric_cols[0]:
                st.metric("Assets Found", summary["total_found"])
            with metric_cols[1]:
                st.metric("Avg Volume Spike", f"{summary['avg_volume_ratio']:.1f}x")
            with metric_cols[2]:
                st.metric("Avg Momentum Score", summary["avg_momentum_score"])
            
            # Categories breakdown
            if summary["top_categories"]:
                st.write("**Momentum Breakdown:**")
                for category in summary["top_categories"]:
                    st.write(f"• {category}")
            
            # Results table
            st.subheader("🎯 Top Candidates")
            display_df = format_for_display(results_df)
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Interactive chart
            st.subheader("📈 Momentum Analysis")
            chart = create_momentum_chart(results_df)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            
        
        else:
            st.warning("🔍 No assets found matching your criteria. Try adjusting the filters.")
            st.info("**Tip**: Lower the volume ratio or widen the price change range to find more results.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>📚 Educational Tool • Built with Streamlit • 
        <a href='#' target='_blank'>View Source Code</a></p>
        <p><small>⚠️ This is for educational purposes only. Not financial advice.</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 