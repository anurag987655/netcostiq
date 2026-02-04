#!/usr/bin/env python3
"""
flow_enricher.py
Add business features to network flows for cost analysis
"""

import pandas as pd
import sys
import os

def enrich_flows(input_file="data/flows_scaled.csv", output_file="data/enriched_flows.csv"):
    """
    Add business-relevant features to flows
    """
    print(f"[+] Loading: {input_file}")
    
    if not os.path.exists(input_file):
        print(f"[!] Error: {input_file} not found!")
        print(f"[!] Run real_scale.py first")
        return None
    
    df = pd.read_csv(input_file)
    
    print(f"[+] Enriching {len(df)} flows...")
    
    # 1. Calculate GB for cost analysis
    df['total_gb'] = df['total_bytes'] / (1024**3)
    
    # 2. Add hour column (for peak hour analysis)
    # Default: alternate between peak (9-17) and off-peak
    df['hour'] = [14 if i % 2 == 0 else 3 for i in range(len(df))]  # 2 PM or 3 AM
    
    # 3. Add traffic direction
    def get_direction(src_ip, dst_ip):
        if src_ip.startswith(('192.168.', '10.', '172.')):
            if dst_ip.startswith(('192.168.', '10.', '172.', '127.')):
                return 'INTERNAL'
            else:
                return 'UPLOAD'  # Expensive!
        else:
            return 'DOWNLOAD'  # Usually cheaper
    
    df['direction'] = df.apply(lambda x: get_direction(x['src_ip'], x['dst_ip']), axis=1)
    
    # 4. Add flow size categories
    def categorize_size(gb):
        if gb > 10:
            return 'VERY_LARGE'
        elif gb > 1:
            return 'LARGE'
        elif gb > 0.1:
            return 'MEDIUM'
        else:
            return 'SMALL'
    
    df['size_category'] = df['total_gb'].apply(categorize_size)
    
    # 5. Add peak hour flag
    df['is_peak_hour'] = df['hour'].between(9, 17)
    
    # 6. Identify destination type
    def get_destination_type(ip):
        # Cloud providers
        if ip.startswith(('20.', '13.', '52.', '54.', '35.', '34.')):
            return 'CLOUD'
        # Internal/Localhost
        elif ip.startswith(('192.168.', '10.', '172.', '127.')):
            return 'INTERNAL'
        # Well-known services
        elif ip.startswith(('8.8.', '140.82.', '173.194.', '185.199.')):
            return 'SERVICE'
        else:
            return 'INTERNET'
    
    df['destination_type'] = df['dst_ip'].apply(get_destination_type)
    
    # 7. Add cost urgency flag
    df['cost_urgency'] = (df['direction'] == 'UPLOAD') & (df['size_category'].isin(['LARGE', 'VERY_LARGE'])) & df['is_peak_hour']
    
    # Save enriched data
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"[✓] Enriched {len(df)} flows")
    print(f"[✓] Added columns: hour, direction, size_category, destination_type, is_peak_hour, cost_urgency")
    print(f"[✓] Saved to: {output_file}")
    
    # Show summary
    print("\nEnrichment Summary:")
    print(f"  Peak hour flows: {df['is_peak_hour'].sum()} ({df['is_peak_hour'].mean()*100:.1f}%)")
    print(f"  Upload flows: {(df['direction'] == 'UPLOAD').sum()} ({(df['direction'] == 'UPLOAD').mean()*100:.1f}%)")
    print(f"  Cloud destinations: {(df['destination_type'] == 'CLOUD').sum()}")
    print(f"  Cost-urgent flows: {df['cost_urgency'].sum()}")
    
    return df

def main():
    """Main function when run directly"""
    print("="*60)
    print("Flow Enricher: Add Business Features")
    print("="*60)
    
    # Get input file from command line or use default
    input_file = sys.argv[1] if len(sys.argv) > 1 else "data/flows_scaled.csv"
    
    # Enrich flows
    df = enrich_flows(input_file)
    
    if df is not None:
        print("\nEnriched data preview:")
        print(df[['src_ip', 'dst_ip', 'direction', 'size_category', 'hour', 'is_peak_hour']].head(10))

if __name__ == "__main__":
    main()