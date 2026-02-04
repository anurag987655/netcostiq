#!/usr/bin/env python3
"""
real_scale.py
Scale flow data to business levels for realistic cost analysis
"""

import pandas as pd
import numpy as np
import sys
import os

def scale_flows(input_file="data/flows.csv", output_file="data/flows_scaled.csv", scale_factor=1000000):
    """
    Scale flow data to business levels
    Args:
        scale_factor: Multiply all bytes by this factor (default: 1,000,000)
    """
    print(f"[+] Loading: {input_file}")
    
    if not os.path.exists(input_file):
        print(f"[!] Error: {input_file} not found!")
        print(f"[!] Run pcap_to_flows.py first")
        return None
    
    df = pd.read_csv(input_file)
    
    # Show before scaling
    original_bytes = df['total_bytes'].sum()
    original_gb = original_bytes / (1024**3)
    
    print(f"[+] Before scaling:")
    print(f"    Total bytes: {original_bytes:,}")
    print(f"    Total GB: {original_gb:.6f}")
    print(f"    Average flow: {df['total_bytes'].mean():.0f} bytes")
    
    # Apply scaling
    print(f"[+] Scaling by {scale_factor:,}x...")
    df['total_bytes'] = df['total_bytes'] * scale_factor
    
    # Recalculate derived fields
    df['bytes_per_sec'] = df['total_bytes'] / df['duration_sec'].clip(lower=0.1)
    
    # Make some flows extra large for realistic analysis
    np.random.seed(42)
    large_indices = np.random.choice(df.index, size=min(10, len(df)), replace=False)
    df.loc[large_indices, 'total_bytes'] = df.loc[large_indices, 'total_bytes'] * 10
    
    # Show after scaling
    scaled_bytes = df['total_bytes'].sum()
    scaled_gb = scaled_bytes / (1024**3)
    
    print(f"[+] After scaling:")
    print(f"    Total bytes: {scaled_bytes:,}")
    print(f"    Total GB: {scaled_gb:.2f}")
    print(f"    Average flow: {df['total_bytes'].mean():,.0f} bytes")
    
    # Save
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"[✓] Saved scaled data to: {output_file}")
    print(f"[✓] Scaling factor applied: {scale_factor:,}x")
    print(f"[✓] Data ready for business cost analysis")
    
    return df

def main():
    """Main function when run directly"""
    print("="*60)
    print("Flow Data Scaling for Business Analysis")
    print("="*60)
    
    # Get input file from command line or use default
    input_file = sys.argv[1] if len(sys.argv) > 1 else "data/flows.csv"
    
    # Scale flows
    df = scale_flows(input_file)
    
    if df is not None:
        print("\nScaled data preview:")
        print(df[['src_ip', 'dst_ip', 'total_bytes']].head())
        
        total_gb = df['total_bytes'].sum() / (1024**3)
        print(f"\nExpected cost range: NRS {total_gb * 50:,.0f} - NRS {total_gb * 100:,.0f}")

if __name__ == "__main__":
    main()