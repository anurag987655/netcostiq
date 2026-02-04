#!/usr/bin/env python3
"""
cost_model.py
Calculate network costs in Nepalese Rupees (NRS)
"""

import pandas as pd
import json
from datetime import datetime
import sys
import os

class CostCalculatorNRS:
    def __init__(self):
        # All prices in Nepalese Rupees (NRS) per GB
        self.pricing = {
            'CLOUD_EGRESS': 85,          # NRS per GB (AWS/Azure egress to internet)
            'INTERNET_EGRESS': 75,       # NRS per GB (Upload to internet)
            'INTERNET_INGRESS': 15,      # NRS per GB (Download from internet)
            'INTERNAL': 0,               # NRS per GB (Internal traffic)
            'CDN_TRAFFIC': 45,           # NRS per GB (Akamai, CloudFront)
            'VIDEO_STREAMING': 60,       # NRS per GB (YouTube, Netflix, Zoom)
            'BACKUP_TRAFFIC': 35,        # NRS per GB (Cloud backup/restore)
            'OTHER': 10,                 # NRS per GB (Default)
        }
        
        # Peak hour surcharge multiplier
        self.peak_surcharge = 1.5  # 50% more expensive during peak hours
        
        # Peak hours (9 AM - 11 PM Nepal time)
        self.peak_hours = range(9, 23)
        
        # Cloud provider IP ranges
        self.cloud_prefixes = [
            '20.', '13.', '52.', '54.',  # Azure, AWS
            '35.', '34.', '8.8.',       # Google Cloud
            '23.', '45.', '51.',        # Netflix, Dropbox
        ]
        
        # Internal network ranges
        self.internal_prefixes = [
            '192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.',
            '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.',
            '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.',
        ]
    
    def classify_traffic(self, src_ip, dst_ip):
        """Classify traffic type for cost calculation"""
        
        # Check if internal traffic
        if any(src_ip.startswith(p) for p in self.internal_prefixes) and \
           any(dst_ip.startswith(p) for p in self.internal_prefixes):
            return 'INTERNAL'
        
        # Determine direction
        src_is_internal = any(src_ip.startswith(p) for p in self.internal_prefixes)
        
        # Check for cloud destinations
        is_cloud_dest = any(dst_ip.startswith(p) for p in self.cloud_prefixes)
        
        # Classify based on direction and destination
        if src_is_internal and is_cloud_dest:
            return 'CLOUD_EGRESS'
        elif src_is_internal:
            return 'INTERNET_EGRESS'
        elif not src_is_internal and any(dst_ip.startswith(p) for p in self.internal_prefixes):
            return 'INTERNET_INGRESS'
        else:
            return 'OTHER'
    
    def calculate_flow_cost_nrs(self, flow):
        """Calculate cost in Nepalese Rupees for a flow"""
        
        # Get traffic classification
        traffic_type = flow.get('traffic_type', 'OTHER')
        
        # Convert bytes to GB
        total_gb = flow['total_bytes'] / (1024**3)
        
        # Base cost per GB
        base_rate = self.pricing.get(traffic_type, 10)  # Default 10 NRS/GB
        
        # Calculate base cost
        cost_nrs = total_gb * base_rate
        
        # Apply peak hour surcharge
        if flow.get('is_peak', False):
            cost_nrs *= self.peak_surcharge
        
        return round(cost_nrs, 4)
    
    def enrich_flows_with_costs(self, df):
        """Add traffic classification and costs to flows dataframe"""
        
        print("[+] Classifying traffic and calculating costs...")
        
        # Add traffic classification
        df['traffic_type'] = df.apply(
            lambda row: self.classify_traffic(row['src_ip'], row['dst_ip']), 
            axis=1
        )
        
        # Add peak hour flag (if hour column exists)
        if 'hour' in df.columns:
            df['is_peak'] = df['hour'].apply(lambda x: x in self.peak_hours)
        else:
            df['is_peak'] = False
        
        # Calculate cost for each flow
        df['cost_nrs'] = df.apply(self.calculate_flow_cost_nrs, axis=1)
        
        # Convert bytes to GB for reporting
        df['total_gb'] = df['total_bytes'] / (1024**3)
        
        return df
    
    def generate_cost_report(self, df):
        """Generate comprehensive cost analysis report"""
        
        # Ensure numeric columns
        df['total_bytes'] = pd.to_numeric(df['total_bytes'], errors='coerce').fillna(0)
        
        # Calculate total cost
        total_cost_nrs = df['cost_nrs'].sum()
        total_data_gb = df['total_gb'].sum()
        
        # Monthly projection (assuming this is one hour of data)
        monthly_projection_nrs = total_cost_nrs * 24 * 30
        
        # Cost breakdown by traffic type
        cost_breakdown = df.groupby('traffic_type').agg({
            'total_gb': 'sum',
            'cost_nrs': 'sum',
            'src_ip': 'count'
        }).round(4).to_dict('index')
        
        # Top 10 most expensive flows
        top_expensive = df.nlargest(10, 'cost_nrs')[[
            'src_ip', 'dst_ip', 'traffic_type', 'total_gb', 'cost_nrs'
        ]].to_dict('records')
        
        # Cost by source IP
        top_sources = df.groupby('src_ip').agg({
            'cost_nrs': 'sum',
            'total_gb': 'sum'
        }).nlargest(5, 'cost_nrs').to_dict('index')
        
        # Peak vs off-peak analysis
        if 'is_peak' in df.columns:
            peak_df = df[df['is_peak'] == True]
            off_peak_df = df[df['is_peak'] == False]
            
            peak_cost = peak_df['cost_nrs'].sum()
            off_peak_cost = off_peak_df['cost_nrs'].sum()
            
            peak_percentage = (peak_cost / total_cost_nrs * 100) if total_cost_nrs > 0 else 0
        else:
            peak_cost = 0
            off_peak_cost = total_cost_nrs
            peak_percentage = 0
        
        # Generate recommendations
        recommendations = self._generate_recommendations(df, total_cost_nrs)
        
        # Compile report
        report = {
            'metadata': {
                'currency': 'NRS',
                'unit': 'per GB',
                'generated_at': datetime.now().isoformat(),
                'peak_hours': '09:00 - 23:00',
                'peak_surcharge': '50%'
            },
            'summary': {
                'total_flows': int(len(df)),
                'total_data_gb': round(total_data_gb, 4),
                'total_cost_nrs': round(total_cost_nrs, 2),
                'average_cost_per_gb': round(total_cost_nrs / max(total_data_gb, 1), 2),
                'monthly_projection_nrs': round(monthly_projection_nrs, 2),
                'peak_traffic_cost_nrs': round(peak_cost, 2),
                'peak_traffic_percentage': round(peak_percentage, 1),
                'off_peak_cost_nrs': round(off_peak_cost, 2)
            },
            'breakdown': cost_breakdown,
            'top_expensive_flows': top_expensive,
            'top_costly_sources': top_sources,
            'recommendations': recommendations,
            'estimated_savings': self._estimate_savings(df, total_cost_nrs)
        }
        
        return report
    
    def _generate_recommendations(self, df, total_cost_nrs):
        """Generate cost optimization recommendations"""
        
        recommendations = []
        
        # Check for expensive cloud egress
        cloud_egress = df[df['traffic_type'] == 'CLOUD_EGRESS']
        if not cloud_egress.empty:
            cloud_cost = cloud_egress['cost_nrs'].sum()
            cloud_percentage = (cloud_cost / total_cost_nrs * 100) if total_cost_nrs > 0 else 0
            
            if cloud_cost > 100:  # More than 100 NRS
                recommendations.append({
                    'id': 'CLOUD_EGRESS_OPT',
                    'title': 'Cloud Egress Optimization',
                    'description': f'Cloud egress traffic accounts for {cloud_percentage:.1f}% of total cost',
                    'suggestion': 'Use CDN for static content, schedule backups during off-peak hours',
                    'potential_savings_nrs': round(cloud_cost * 0.3, 2),  # 30% savings
                    'priority': 'HIGH'
                })
        
        # Check for peak hour expensive traffic
        if 'is_peak' in df.columns:
            peak_traffic = df[df['is_peak'] == True]
            peak_cost = peak_traffic['cost_nrs'].sum()
            
            if peak_cost > total_cost_nrs * 0.6:  # More than 60% during peak
                recommendations.append({
                    'id': 'PEAK_HOUR_OPT',
                    'title': 'Peak Hour Traffic Management',
                    'description': f'{peak_cost/total_cost_nrs*100:.1f}% of traffic occurs during peak hours',
                    'suggestion': 'Schedule large transfers for off-peak hours (11 PM - 9 AM)',
                    'potential_savings_nrs': round(peak_cost * 0.4, 2),  # 40% savings
                    'priority': 'MEDIUM'
                })
        
        # Check for large flows
        large_flows = df[df['total_gb'] > 0.5]  # Flows larger than 0.5 GB
        if len(large_flows) > 3:
            large_flow_cost = large_flows['cost_nrs'].sum()
            recommendations.append({
                'id': 'LARGE_FLOW_OPT',
                'title': 'Large Flow Optimization',
                'description': f'{len(large_flows)} large flows detected (>0.5 GB each)',
                'suggestion': 'Implement traffic shaping or compression for large transfers',
                'potential_savings_nrs': round(large_flow_cost * 0.2, 2),  # 20% savings
                'priority': 'MEDIUM'
            })
        
        # Add general recommendations
        recommendations.extend([
            {
                'id': 'TRAFFIC_MONITORING',
                'title': 'Continuous Traffic Monitoring',
                'description': 'Regular monitoring can identify new cost patterns',
                'suggestion': 'Set up daily cost alerts and weekly reports',
                'potential_savings_nrs': round(total_cost_nrs * 0.15, 2),
                'priority': 'LOW'
            },
            {
                'id': 'BANDWIDTH_UPGRADE',
                'title': 'Consider Bandwidth Upgrade',
                'description': 'High utilization during peak may indicate need for more bandwidth',
                'suggestion': 'Analyze if upgrading bandwidth plan reduces overall cost',
                'potential_savings_nrs': round(total_cost_nrs * 0.25, 2),
                'priority': 'LOW'
            }
        ])
        
        return recommendations
    
    def _estimate_savings(self, df, total_cost_nrs):
        """Estimate potential savings"""
        
        # Calculate total potential savings from recommendations
        total_potential_savings = sum(rec['potential_savings_nrs'] for rec in self._generate_recommendations(df, total_cost_nrs))
        
        # Monthly savings projection
        monthly_savings = total_potential_savings * 24 * 30
        
        return {
            'immediate_savings_nrs': round(total_potential_savings, 2),
            'monthly_savings_nrs': round(monthly_savings, 2),
            'savings_percentage': round((total_potential_savings / max(total_cost_nrs, 1)) * 100, 1)
        }

def main():
    """Main function to run the cost analysis"""
    
    print("="*60)
    print("FlowSpend: NRS Cost Analysis")
    print("="*60)
    
    # Get input file from command line or use default
    input_file = sys.argv[1] if len(sys.argv) > 1 else "data/enriched_flows.csv"
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"[!] Error: {input_file} not found!")
        print("[!] Please run the pipeline first:")
        print("    1. python pcap_to_flows.py")
        print("    2. python real_scale.py")
        print("    3. python flow_enricher.py")
        return None
    
    # Load enriched flows
    print(f"[+] Loading data: {input_file}")
    df = pd.read_csv(input_file)
    print(f"[+] Loaded {len(df)} flows")
    
    # Initialize cost calculator
    calculator = CostCalculatorNRS()
    
    # Enrich flows with costs
    df_with_costs = calculator.enrich_flows_with_costs(df)
    
    # Generate cost report
    report = calculator.generate_cost_report(df_with_costs)
    
    # Save enriched data
    output_file = "data/final_analysis.csv"
    df_with_costs.to_csv(output_file, index=False)
    print(f"[✓] Saved enriched flows to: {output_file}")
    
    # Save report to JSON
    os.makedirs("reports", exist_ok=True)
    with open('reports/cost_analysis_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    print(f"[✓] Saved detailed report to: reports/cost_analysis_report.json")
    
    # Create simple text summary
    with open('reports/executive_summary.txt', 'w') as f:
        f.write("="*60 + "\n")
        f.write("EXECUTIVE SUMMARY: NETWORK COST ANALYSIS\n")
        f.write("="*60 + "\n\n")
        f.write(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Flows Analyzed: {report['summary']['total_flows']}\n")
        f.write(f"Total Data: {report['summary']['total_data_gb']:.2f} GB\n")
        f.write(f"Total Cost: NRS {report['summary']['total_cost_nrs']:,.2f}\n")
        f.write(f"Monthly Projection: NRS {report['summary']['monthly_projection_nrs']:,.2f}\n")
        f.write(f"Potential Savings: NRS {report['estimated_savings']['monthly_savings_nrs']:,.2f}/month\n\n")
        
        f.write("TOP RECOMMENDATIONS:\n")
        f.write("-"*40 + "\n")
        for rec in report['recommendations'][:3]:
            f.write(f"• [{rec['priority']}] {rec['title']}\n")
            f.write(f"  {rec['suggestion']}\n")
            f.write(f"  Savings: NRS {rec['potential_savings_nrs']:,.2f}\n\n")
    
    print(f"[✓] Saved executive summary to: reports/executive_summary.txt")
    
    # Print summary
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    
    summary = report['summary']
    print(f"📊 Total flows analyzed: {summary['total_flows']}")
    print(f"📊 Total data transferred: {summary['total_data_gb']:.2f} GB")
    print(f"💰 Total cost: NRS {summary['total_cost_nrs']:,.2f}")
    print(f"📅 Monthly projection: NRS {summary['monthly_projection_nrs']:,.2f}")
    print(f"⏰ Peak traffic: {summary['peak_traffic_percentage']}% of total cost")
    
    # Cost breakdown
    print(f"\n💰 COST BREAKDOWN:")
    for traffic_type, data in report['breakdown'].items():
        cost = data.get('cost_nrs', 0)
        gb = data.get('total_gb', 0)
        print(f"  {traffic_type}: NRS {cost:,.2f} ({gb:.2f} GB)")
    
    # Top expensive flows
    print(f"\n🔝 TOP 3 MOST EXPENSIVE FLOWS:")
    for i, flow in enumerate(report['top_expensive_flows'][:3], 1):
        print(f"  {i}. {flow['src_ip']} → {flow['dst_ip']}")
        print(f"     Type: {flow['traffic_type']}")
        print(f"     Size: {flow['total_gb']:.3f} GB")
        print(f"     Cost: NRS {flow['cost_nrs']:.2f}")
    
    # Savings estimate
    savings = report['estimated_savings']
    print(f"\n💡 POTENTIAL SAVINGS:")
    print(f"  Immediate: NRS {savings['immediate_savings_nrs']:,.2f}")
    print(f"  Monthly: NRS {savings['monthly_savings_nrs']:,.2f}")
    print(f"  Percentage: {savings['savings_percentage']}% of current cost")
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE!")
    print("="*60)
    
    return df_with_costs, report

if __name__ == "__main__":
    main()