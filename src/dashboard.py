# src/dashboard.py
#!/usr/bin/env python3
"""
dashboard.py
Streamlit dashboard for FlowSpend visualization
Run with: streamlit run src/dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Page config
st.set_page_config(
    page_title="FlowSpend Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 FlowSpend: Network Cost Dashboard")
st.markdown("Interactive visualization of network traffic costs in NRS")

@st.cache_data
def load_data():
    """Load data with caching"""
    data_files = [
        'data/final_analysis.csv',
        'data/final_nrs_analysis.csv',
        'data/ai_enhanced_flows.csv'
    ]
    
    for file in data_files:
        if os.path.exists(file):
            df = pd.read_csv(file)
            return df
    
    # If no data, show sample
    st.warning("No data file found. Showing sample data.")
    return pd.DataFrame({
        'src_ip': ['192.168.1.1', '192.168.1.2'],
        'dst_ip': ['20.42.65.90', '8.8.8.8'],
        'cost_nrs': [1500, 800],
        'total_gb': [17.6, 10.5],
        'traffic_type': ['CLOUD_EGRESS', 'INTERNET_EGRESS']
    })

# Load data
df = load_data()

# Sidebar filters
st.sidebar.header("🔍 Filters")

# Cost range filter
min_cost, max_cost = float(df['cost_nrs'].min()), float(df['cost_nrs'].max())
cost_range = st.sidebar.slider(
    "Cost Range (NRS)",
    min_cost, max_cost, (min_cost, max_cost),
    step=100.0
)

# Traffic type filter
traffic_types = st.sidebar.multiselect(
    "Traffic Types",
    options=df['traffic_type'].unique(),
    default=df['traffic_type'].unique()
)

# Apply filters
filtered_df = df[
    (df['cost_nrs'] >= cost_range[0]) & 
    (df['cost_nrs'] <= cost_range[1]) &
    (df['traffic_type'].isin(traffic_types))
]

# Metrics row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Flows", f"{len(filtered_df):,}")
with col2:
    st.metric("Total Cost", f"NRS {filtered_df['cost_nrs'].sum():,.0f}")
with col3:
    st.metric("Total Data", f"{filtered_df['total_gb'].sum():.1f} GB")
with col4:
    monthly = filtered_df['cost_nrs'].sum() * 24 * 30
    st.metric("Monthly Projection", f"NRS {monthly:,.0f}")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Cost Analysis", "🔝 Top Flows", "🌐 Traffic Flow", "📋 Raw Data"])

with tab1:
    # Cost by traffic type
    st.subheader("Cost by Traffic Type")
    cost_by_type = filtered_df.groupby('traffic_type')['cost_nrs'].sum().reset_index()
    fig1 = px.bar(cost_by_type, x='traffic_type', y='cost_nrs',
                 color='cost_nrs', color_continuous_scale='viridis')
    st.plotly_chart(fig1, use_container_width=True)
    
    # Pie chart
    col1, col2 = st.columns(2)
    with col1:
        fig2 = px.pie(cost_by_type, values='cost_nrs', names='traffic_type',
                     title='Cost Distribution')
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        # Size vs Cost scatter
        fig3 = px.scatter(filtered_df, x='total_gb', y='cost_nrs',
                         color='traffic_type', size='cost_nrs',
                         hover_data=['src_ip', 'dst_ip'],
                         title='Size vs Cost')
        st.plotly_chart(fig3, use_container_width=True)

with tab2:
    # Top N flows
    n_flows = st.slider("Number of top flows to show", 5, 50, 10)
    top_flows = filtered_df.nlargest(n_flows, 'cost_nrs')
    
    # Horizontal bar chart
    fig4 = px.bar(top_flows, 
                 y=[f"{src} → {dst}" for src, dst in zip(top_flows['src_ip'], top_flows['dst_ip'])],
                 x='cost_nrs',
                 orientation='h',
                 color='cost_nrs',
                 title=f'Top {n_flows} Most Expensive Flows')
    fig4.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig4, use_container_width=True)
    
    # Data table
    st.dataframe(top_flows[['src_ip', 'dst_ip', 'traffic_type', 'total_gb', 'cost_nrs']],
                column_config={
                    "cost_nrs": st.column_config.NumberColumn(
                        "Cost (NRS)",
                        format="NRS %.2f"
                    ),
                    "total_gb": st.column_config.NumberColumn(
                        "Size (GB)",
                        format="%.2f GB"
                    )
                },
                use_container_width=True)

with tab3:
    # Network flow diagram (simplified)
    st.subheader("Costly Connections")
    
    # Create node-link data
    connections = filtered_df.groupby(['src_ip', 'dst_ip']).agg({
        'cost_nrs': 'sum',
        'total_gb': 'sum'
    }).reset_index()
    
    # Show as table first
    st.dataframe(connections.nlargest(20, 'cost_nrs'),
                column_config={
                    "cost_nrs": st.column_config.NumberColumn(
                        "Total Cost (NRS)",
                        format="NRS %.2f"
                    ),
                    "total_gb": st.column_config.NumberColumn(
                        "Total Data (GB)",
                        format="%.2f GB"
                    )
                },
                use_container_width=True)
    
    # Sankey diagram for top connections
    if len(connections) > 0:
        top_conn = connections.nlargest(10, 'cost_nrs')
        
        # Create Sankey diagram
        fig5 = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=list(top_conn['src_ip']) + list(top_conn['dst_ip'])
            ),
            link=dict(
                source=list(range(len(top_conn))),
                target=list(range(len(top_conn), 2*len(top_conn))),
                value=top_conn['cost_nrs'],
                label=[f"NRS {c:,.0f}" for c in top_conn['cost_nrs']]
            )
        )])
        
        fig5.update_layout(title_text="Top Costly Connections", font_size=10)
        st.plotly_chart(fig5, use_container_width=True)

with tab4:
    # Raw data viewer
    st.subheader("Raw Flow Data")
    st.dataframe(filtered_df, use_container_width=True)
    
    # Export option
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv,
        file_name="filtered_flows.csv",
        mime="text/csv",
    )

# Footer
st.markdown("---")
st.caption(f"FlowSpend Dashboard • {len(filtered_df)} flows • NRS {filtered_df['cost_nrs'].sum():,.0f} total cost")