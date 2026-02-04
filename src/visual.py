#!/usr/bin/env python3
"""
visual.py
Create visualizations for FlowSpend network cost analysis
Saves plots as images in reports/ directory
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def ensure_reports_dir():
    """Ensure reports directory exists"""
    os.makedirs('reports', exist_ok=True)
    os.makedirs('reports/plots', exist_ok=True)

def create_basic_plots(df):
    """Create basic static plots and save as images"""
    print("[+] Creating basic plots...")
    
    # 1. Histogram of flow costs
    plt.figure(figsize=(10, 6))
    plt.hist(df['cost_nrs'], bins=50, edgecolor='black', alpha=0.7)
    plt.xlabel('Cost (NRS)')
    plt.ylabel('Number of Flows')
    plt.title('Distribution of Flow Costs')
    plt.grid(True, alpha=0.3)
    plt.savefig('reports/plots/cost_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: cost_distribution.png")
    
    # 2. Top 10 most expensive flows
    top_10 = df.nlargest(10, 'cost_nrs')
    plt.figure(figsize=(12, 6))
    bars = plt.barh(
        [f"{row['src_ip']}\n→ {row['dst_ip']}" for _, row in top_10.iterrows()],
        top_10['cost_nrs'],
        color='coral'
    )
    plt.xlabel('Cost (NRS)')
    plt.title('Top 10 Most Expensive Flows')
    plt.gca().invert_yaxis()  # Highest at top
    
    # Add value labels
    for bar in bars:
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2, 
                f' NRS {width:,.2f}', ha='left', va='center')
    
    plt.tight_layout()
    plt.savefig('reports/plots/top_10_flows.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: top_10_flows.png")
    
    # 3. Cost breakdown by traffic type
    cost_by_type = df.groupby('traffic_type')['cost_nrs'].sum().sort_values(ascending=False)
    plt.figure(figsize=(10, 6))
    cost_by_type.plot(kind='bar', color='skyblue', edgecolor='black')
    plt.xlabel('Traffic Type')
    plt.ylabel('Total Cost (NRS)')
    plt.title('Total Cost by Traffic Type')
    plt.xticks(rotation=45, ha='right')
    
    # Add value labels on bars
    for i, v in enumerate(cost_by_type):
        plt.text(i, v + max(cost_by_type)*0.01, f'{v:,.0f}', 
                ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('reports/plots/cost_by_traffic_type.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: cost_by_traffic_type.png")
    
    # 4. Pie chart of traffic distribution
    plt.figure(figsize=(8, 8))
    cost_by_type.plot(kind='pie', autopct='%1.1f%%', startangle=90,
                     colors=plt.cm.Paired.colors, textprops={'fontsize': 10})
    plt.title('Cost Distribution by Traffic Type')
    plt.ylabel('')
    plt.savefig('reports/plots/cost_pie_chart.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: cost_pie_chart.png")
    
    # 5. Scatter plot: Size vs Cost
    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(df['total_gb'], df['cost_nrs'], 
                         c=df['cost_nrs'], cmap='viridis', 
                         alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
    plt.colorbar(scatter, label='Cost (NRS)')
    plt.xlabel('Flow Size (GB)')
    plt.ylabel('Cost (NRS)')
    plt.title('Flow Size vs Cost')
    plt.grid(True, alpha=0.3)
    
    # Log scale if data is skewed
    if df['total_gb'].max() / df['total_gb'].min() > 100:
        plt.xscale('log')
        plt.xlabel('Flow Size (GB) - Log Scale')
    
    plt.tight_layout()
    plt.savefig('reports/plots/size_vs_cost.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved: size_vs_cost.png")
    
    # 6. Peak vs Off-Peak cost comparison
    if 'is_peak' in df.columns:
        peak_cost = df[df['is_peak']]['cost_nrs'].sum()
        off_peak_cost = df[~df['is_peak']]['cost_nrs'].sum()
        
        plt.figure(figsize=(8, 6))
        plt.bar(['Peak Hours', 'Off-Peak Hours'], [peak_cost, off_peak_cost], 
               color=['red', 'green'], edgecolor='black')
        plt.ylabel('Total Cost (NRS)')
        plt.title('Cost Comparison: Peak vs Off-Peak Hours')
        
        # Add value labels
        for i, v in enumerate([peak_cost, off_peak_cost]):
            plt.text(i, v + max(peak_cost, off_peak_cost)*0.01, 
                    f'NRS {v:,.0f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig('reports/plots/peak_vs_offpeak.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✓ Saved: peak_vs_offpeak.png")

def create_interactive_plots(df):
    """Create interactive HTML plots using Plotly"""
    try:
        print("[+] Creating interactive plots...")
        
        # 1. Interactive bar chart of top flows
        top_20 = df.nlargest(20, 'cost_nrs')
        fig1 = px.bar(top_20, 
                     x=[f"{src}<br>→ {dst}" for src, dst in zip(top_20['src_ip'], top_20['dst_ip'])],
                     y='cost_nrs',
                     title='Top 20 Most Expensive Flows',
                     labels={'x': 'Flow (Source → Destination)', 'y': 'Cost (NRS)'},
                     color='cost_nrs',
                     color_continuous_scale='viridis')
        fig1.update_layout(xaxis_tickangle=-45)
        fig1.write_html('reports/plots/top_flows_interactive.html')
        print("  ✓ Saved: top_flows_interactive.html")
        
        # 2. Interactive pie chart
        cost_by_type = df.groupby('traffic_type')['cost_nrs'].sum().reset_index()
        fig2 = px.pie(cost_by_type, values='cost_nrs', names='traffic_type',
                     title='Cost Distribution by Traffic Type',
                     hole=0.3)
        fig2.write_html('reports/plots/cost_pie_interactive.html')
        print("  ✓ Saved: cost_pie_interactive.html")
        
        # 3. Interactive scatter plot
        fig3 = px.scatter(df, x='total_gb', y='cost_nrs', 
                         color='traffic_type',
                         size='cost_nrs',
                         hover_data=['src_ip', 'dst_ip', 'traffic_type'],
                         title='Flow Size vs Cost by Traffic Type',
                         labels={'total_gb': 'Flow Size (GB)', 'cost_nrs': 'Cost (NRS)'})
        fig3.write_html('reports/plots/scatter_interactive.html')
        print("  ✓ Saved: scatter_interactive.html")
        
    except ImportError:
        print("[!] Plotly not installed. Skipping interactive plots.")
        print("[!] Install with: pip install plotly")

def create_summary_report(df):
    """Create a text summary report with statistics"""
    print("[+] Creating summary report...")
    
    total_flows = len(df)
    total_cost = df['cost_nrs'].sum()
    total_data = df['total_gb'].sum()
    avg_cost_per_gb = total_cost / total_data if total_data > 0 else 0
    
    # Get top sources
    top_sources = df.groupby('src_ip').agg({
        'cost_nrs': 'sum',
        'total_gb': 'sum'
    }).nlargest(5, 'cost_nrs')
    
    # Get top destinations
    top_dests = df.groupby('dst_ip').agg({
        'cost_nrs': 'sum',
        'total_gb': 'sum'
    }).nlargest(5, 'cost_nrs')
    
    with open('reports/visualization_summary.txt', 'w') as f:
        f.write("="*60 + "\n")
        f.write("FLOWSPEND VISUALIZATION SUMMARY REPORT\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Flows Analyzed: {total_flows:,}\n")
        f.write(f"Total Data Transferred: {total_data:.2f} GB\n")
        f.write(f"Total Cost: NRS {total_cost:,.2f}\n")
        f.write(f"Average Cost per GB: NRS {avg_cost_per_gb:.2f}\n")
        f.write(f"Monthly Projection: NRS {total_cost * 24 * 30:,.2f}\n\n")
        
        f.write("TOP 5 COSTLY SOURCE IPs:\n")
        f.write("-" * 40 + "\n")
        for ip, data in top_sources.iterrows():
            f.write(f"{ip:15} : NRS {data['cost_nrs']:,.2f} ({data['total_gb']:.2f} GB)\n")
        
        f.write("\nTOP 5 COSTLY DESTINATION IPs:\n")
        f.write("-" * 40 + "\n")
        for ip, data in top_dests.iterrows():
            f.write(f"{ip:20} : NRS {data['cost_nrs']:,.2f} ({data['total_gb']:.2f} GB)\n")
        
        f.write("\nTRAFFIC TYPE BREAKDOWN:\n")
        f.write("-" * 40 + "\n")
        for traffic_type, group in df.groupby('traffic_type'):
            cost = group['cost_nrs'].sum()
            percentage = (cost / total_cost * 100) if total_cost > 0 else 0
            f.write(f"{traffic_type:20} : NRS {cost:,.2f} ({percentage:.1f}%)\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("VISUALIZATION FILES GENERATED:\n")
        f.write("="*60 + "\n\n")
        
        f.write("Static Plots (PNG):\n")
        plots = ['cost_distribution.png', 'top_10_flows.png', 'cost_by_traffic_type.png',
                'cost_pie_chart.png', 'size_vs_cost.png']
        if 'is_peak' in df.columns:
            plots.append('peak_vs_offpeak.png')
        
        for plot in plots:
            f.write(f"  • reports/plots/{plot}\n")
        
        f.write("\nInteractive Plots (HTML - Open in browser):\n")
        interactive = ['top_flows_interactive.html', 'cost_pie_interactive.html', 
                      'scatter_interactive.html']
        for plot in interactive:
            f.write(f"  • reports/plots/{plot}\n")

def main():
    """Main function"""
    print("="*60)
    print("FLOWSPEND VISUALIZATION GENERATOR")
    print("="*60)
    
    # Ensure directories exist
    ensure_reports_dir()
    
    # Try to load data from different possible locations
    data_files = [
        'data/final_analysis.csv',
        'data/final_nrs_analysis.csv',
        'data/ai_enhanced_flows.csv'
    ]
    
    df = None
    for file in data_files:
        if os.path.exists(file):
            print(f"[+] Loading data from: {file}")
            df = pd.read_csv(file)
            print(f"    Loaded {len(df)} flows")
            break
    
    if df is None:
        print("[!] Error: No data file found!")
        print("[!] Please run the cost analysis pipeline first.")
        print("[!] Expected files: data/final_analysis.csv or data/final_nrs_analysis.csv")
        return
    
    # Create visualizations
    create_basic_plots(df)
    create_interactive_plots(df)
    create_summary_report(df)
    
    print("\n" + "="*60)
    print("VISUALIZATION GENERATION COMPLETE!")
    print("="*60)
    print("\n📁 Files saved in 'reports/plots/' directory:")
    print("\n📊 Static Plots (PNG):")
    print("  • cost_distribution.png     - Distribution of flow costs")
    print("  • top_10_flows.png          - Top 10 most expensive flows")
    print("  • cost_by_traffic_type.png  - Cost by traffic type (bar)")
    print("  • cost_pie_chart.png        - Cost distribution (pie)")
    print("  • size_vs_cost.png          - Flow size vs cost scatter")
    
    if 'is_peak' in df.columns:
        print("  • peak_vs_offpeak.png       - Peak vs off-peak comparison")
    
    print("\n🌐 Interactive Plots (HTML - open in browser):")
    print("  • top_flows_interactive.html")
    print("  • cost_pie_interactive.html")
    print("  • scatter_interactive.html")
    
    print("\n📋 Summary Report:")
    print("  • visualization_summary.txt")
    
    print("\n📈 Quick Stats:")
    print(f"  Total flows: {len(df):,}")
    print(f"  Total cost: NRS {df['cost_nrs'].sum():,.2f}")
    print(f"  Total data: {df['total_gb'].sum():.2f} GB")
    
    # Show top flow
    top_flow = df.nlargest(1, 'cost_nrs').iloc[0]
    print(f"  Most expensive flow: {top_flow['src_ip']} → {top_flow['dst_ip']}")
    print(f"    Cost: NRS {top_flow['cost_nrs']:.2f}, Size: {top_flow['total_gb']:.2f} GB")
    
    print("\n💡 Tip: Open HTML files in your web browser for interactive charts!")
    print("="*60)

if __name__ == "__main__":
    # Install required packages if missing
    try:
        import pandas as pd
    except ImportError:
        print("[!] pandas not installed. Installing...")
        import subprocess
        subprocess.check_call(["pip", "install", "pandas", "matplotlib", "seaborn"])
    
    main()