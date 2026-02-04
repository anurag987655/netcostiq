#!/usr/bin/env python3
"""
pcap_to_flows.py
Extract network flows from PCAP files
"""

from scapy.all import rdpcap, IP, TCP, UDP
import pandas as pd
from collections import defaultdict
import sys
import os

def extract_flows(pcap_file="data/sample.pcap", output_file="data/flows.csv"):
    """
    Extract flows from PCAP file and save to CSV
    """
    print(f"[+] Reading PCAP: {pcap_file}")
    
    # Check if file exists
    if not os.path.exists(pcap_file):
        print(f"[!] Error: {pcap_file} not found!")
        return None
    
    # Dictionary to store flows
    flows = defaultdict(lambda: {
        "start_time": None,
        "end_time": None,
        "total_bytes": 0,
        "packet_count": 0
    })
    
    try:
        packets = rdpcap(pcap_file)
    except Exception as e:
        print(f"[!] Error reading PCAP: {e}")
        return None
    
    print(f"[+] Processing {len(packets)} packets...")
    
    for pkt in packets:
        if IP not in pkt:
            continue
        
        # Get protocol
        if TCP in pkt:
            proto = "TCP"
            sport = pkt[TCP].sport
            dport = pkt[TCP].dport
        elif UDP in pkt:
            proto = "UDP"
            sport = pkt[UDP].sport
            dport = pkt[UDP].dport
        else:
            continue
        
        # Get IP and packet info
        src = pkt[IP].src
        dst = pkt[IP].dst
        timestamp = pkt.time
        size = len(pkt)
        
        # Create flow key (5-tuple)
        flow_key = (src, dst, sport, dport, proto)
        flow = flows[flow_key]
        
        # Update flow stats
        if flow["start_time"] is None:
            flow["start_time"] = timestamp
        
        flow["end_time"] = timestamp
        flow["total_bytes"] += size
        flow["packet_count"] += 1
    
    # Convert to DataFrame
    rows = []
    for key, data in flows.items():
        src, dst, sport, dport, proto = key
        duration = data["end_time"] - data["start_time"]
        
        rows.append({
            "src_ip": src,
            "dst_ip": dst,
            "src_port": sport,
            "dst_port": dport,
            "protocol": proto,
            "duration_sec": round(duration, 2),
            "total_bytes": data["total_bytes"],
            "packet_count": data["packet_count"],
            "bytes_per_sec": round(data["total_bytes"] / max(duration, 0.1), 2)
        })
    
    df = pd.DataFrame(rows)
    
    # Save to CSV
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"[✓] Extracted {len(df)} flows")
    print(f"[✓] Saved to: {output_file}")
    print(f"[✓] Total data: {df['total_bytes'].sum() / (1024**3):.6f} GB")
    
    return df

def main():
    """Main function when run directly"""
    print("="*60)
    print("PCAP to Flow Extractor")
    print("="*60)
    
    # Get PCAP file from command line or use default
    pcap_file = sys.argv[1] if len(sys.argv) > 1 else "data/sample.pcap"
    
    # Extract flows
    df = extract_flows(pcap_file)
    
    if df is not None:
        print("\nFirst 5 flows:")
        print(df[['src_ip', 'dst_ip', 'protocol', 'total_bytes']].head())
    else:
        print("[!] Failed to extract flows")

if __name__ == "__main__":
    main()