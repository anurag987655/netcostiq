import pandas as pd
import ipaddress
from datetime import datetime
import socket

class FlowEnricher:
    def __init__(self):
        # Define internal network (adjust based on your setup)
        self.internal_network = ipaddress.ip_network('192.168.0.0/16')
        
        # Cloud provider IP ranges (simplified - expand as needed)
        self.cloud_ranges = {
            'AWS': ['13.248.118.0/24', '52.95.0.0/16'],
            'Azure': ['20.42.65.0/24', '20.44.10.0/24'],
            'Google': ['8.8.8.0/24'],
        }
        
        # Peak hours (9 AM - 5 PM)
        self.peak_hours = range(9, 17)
        
    def is_internal(self, ip):
        """Check if IP is internal/private"""
        try:
            return ipaddress.ip_address(ip) in self.internal_network
        except:
            return False
    
    def get_traffic_direction(self, src_ip, dst_ip):
        """Determine if traffic is upload or download"""
        src_internal = self.is_internal(src_ip)
        dst_internal = self.is_internal(dst_ip)
        
        if src_internal and not dst_internal:
            return 'UPLOAD'  # Costly - egress from internal
        elif not src_internal and dst_internal:
            return 'DOWNLOAD'  # Usually free
        else:
            return 'INTERNAL'  # Within network
    
    def identify_destination_type(self, dst_ip):
        """Classify destination (Cloud, CDN, Internet, etc.)"""
        # Check for well-known services
        if dst_ip.startswith(('20.', '13.', '52.')):  # Azure/AWS
            return 'CLOUD'
        elif dst_ip in ['8.8.8.8', '8.8.4.4']:  # Google DNS
            return 'DNS'
        elif dst_ip == '127.0.0.1':  # Localhost
            return 'LOCAL'
        else:
            return 'INTERNET'
    
    def calculate_cost_category(self, flow):
        """Categorize traffic for cost analysis"""
        direction = flow['direction']
        dest_type = flow['destination_type']
        bytes_gb = flow['total_bytes'] / 1e9  # Convert to GB
        
        # Cost logic
        if direction == 'UPLOAD' and dest_type == 'CLOUD':
            return 'CLOUD_EGRESS'  # Most expensive
        elif direction == 'UPLOAD':
            return 'INTERNET_EGRESS'
        elif direction == 'DOWNLOAD' and bytes_gb > 0.1:  # Large downloads
            return 'BULK_DOWNLOAD'
        else:
            return 'OTHER'

def main():
    # Load your flows
    df = pd.read_csv('data/flows.csv')
    
    # Initialize enricher
    enricher = FlowEnricher()
    
    # Add new features
    print("[+] Enriching flows with cost features...")
    
    # Traffic direction
    df['direction'] = df.apply(lambda x: enricher.get_traffic_direction(x['src_ip'], x['dst_ip']), axis=1)
    
    # Destination classification
    df['destination_type'] = df['dst_ip'].apply(enricher.identify_destination_type)
    
    # Time features (if you had timestamp)
    # df['hour'] = pd.to_datetime(df['start_time']).dt.hour
    # df['is_peak'] = df['hour'].apply(lambda x: x in enricher.peak_hours)
    
    # Cost category
    df['cost_category'] = df.apply(enricher.calculate_cost_category, axis=1)
    
    # Calculate GB for cost estimation
    df['total_gb'] = df['total_bytes'] / 1e9
    
    # Save enriched data
    df.to_csv('data/enriched_flows.csv', index=False)
    print(f"[✓] Enriched {len(df)} flows")
    print(df[['src_ip', 'dst_ip', 'direction', 'destination_type', 'cost_category', 'total_gb']].head())
    
    return df

if __name__ == "__main__":
    df = main()