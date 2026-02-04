#!/usr/bin/env python3
"""
run_project.py
One-click runner for FlowSpend network cost analysis
"""

import sys
import os
import subprocess

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print project header"""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                   FLOWSPEND ANALYZER                     ║")
    print("║     Network Cost Optimization in Nepalese Rupees         ║")
    print("╚══════════════════════════════════════════════════════════╝")

def run_pipeline():
    """Run complete pipeline"""
    print("\n[1/4] Extracting flows from PCAP...")
    from pcap_to_flows import extract_flows
    extract_flows()
    
    print("\n[2/4] Scaling data to business levels...")
    from real_scale import scale_flows
    scale_flows()
    
    print("\n[3/4] Adding business features...")
    from flow_enricher import enrich_flows
    enrich_flows()
    
    print("\n[4/4] Calculating NRS costs and generating report...")
    from cost_model import main as cost_main
    cost_main()

def show_menu():
    """Show main menu"""
    clear_screen()
    print_header()
    
    print("\n" + "═" * 60)
    print("MAIN MENU")
    print("═" * 60)
    
    print("\n1. 🚀 Run Complete Pipeline (PCAP → Report)")
    print("2. 📊 Calculate Costs Only (using existing data)")
    print("3. 🔄 Run Individual Steps")
    print("4. 📋 View Generated Reports")
    print("5. 🗑️  Clean Data & Start Fresh")
    print("6. ❌ Exit")
    
    print("\n" + "═" * 60)
    choice = input("Enter your choice (1-6): ").strip()
    
    return choice

def individual_steps():
    """Show individual steps menu"""
    clear_screen()
    print_header()
    
    print("\n" + "═" * 60)
    print("INDIVIDUAL STEPS")
    print("═" * 60)
    
    print("\n1. Extract flows from PCAP")
    print("2. Scale flows to business levels")
    print("3. Enrich flows with business features")
    print("4. Calculate NRS costs")
    print("5. Back to Main Menu")
    
    print("\n" + "═" * 60)
    choice = input("Enter your choice (1-5): ").strip()
    
    if choice == "1":
        from pcap_to_flows import extract_flows
        extract_flows()
        input("\nPress Enter to continue...")
    elif choice == "2":
        from real_scale import scale_flows
        scale_flows()
        input("\nPress Enter to continue...")
    elif choice == "3":
        from flow_enricher import enrich_flows
        enrich_flows()
        input("\nPress Enter to continue...")
    elif choice == "4":
        from cost_model import main as cost_main
        cost_main()
        input("\nPress Enter to continue...")
    
    return choice

def view_reports():
    """Show available reports"""
    clear_screen()
    print_header()
    
    print("\n" + "═" * 60)
    print("AVAILABLE REPORTS")
    print("═" * 60)
    
    reports_dir = "reports"
    data_dir = "data"
    
    print("\n📊 DATA FILES:")
    if os.path.exists(data_dir):
        for file in sorted(os.listdir(data_dir)):
            if file.endswith('.csv'):
                path = os.path.join(data_dir, file)
                size = os.path.getsize(path) / 1024  # KB
                print(f"  • {file} ({size:.1f} KB)")
    
    print("\n📋 REPORT FILES:")
    if os.path.exists(reports_dir):
        for file in sorted(os.listdir(reports_dir)):
            path = os.path.join(reports_dir, file)
            size = os.path.getsize(path) / 1024  # KB
            print(f"  • {file} ({size:.1f} KB)")
            
            # Show preview for text files
            if file.endswith('.txt'):
                print("    Preview:")
                try:
                    with open(path, 'r') as f:
                        lines = f.readlines()[:5]
                        for line in lines:
                            print(f"      {line.rstrip()}")
                except:
                    pass
    
    print("\n" + "═" * 60)
    input("\nPress Enter to continue...")

def clean_data():
    """Clean generated data files"""
    clear_screen()
    print_header()
    
    print("\n" + "═" * 60)
    print("CLEAN DATA FILES")
    print("═" * 60)
    
    print("\n⚠️  WARNING: This will delete all generated files!")
    print("Only raw data (sample.pcap) will be kept.")
    
    confirm = input("\nAre you sure? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        files_to_keep = ['sample.pcap', 'README.md', 'requirements.txt']
        files_to_delete = []
        
        # List files in data directory
        if os.path.exists('data'):
            for file in os.listdir('data'):
                if file not in files_to_keep:
                    files_to_delete.append(os.path.join('data', file))
        
        # List files in reports directory
        if os.path.exists('reports'):
            for file in os.listdir('reports'):
                files_to_delete.append(os.path.join('reports', file))
        
        # Delete files
        deleted_count = 0
        for file in files_to_delete:
            try:
                os.remove(file)
                print(f"  Deleted: {file}")
                deleted_count += 1
            except Exception as e:
                print(f"  Error deleting {file}: {e}")
        
        print(f"\n✓ Deleted {deleted_count} files")
    
    else:
        print("\nOperation cancelled.")
    
    print("\n" + "═" * 60)
    input("\nPress Enter to continue...")

def main():
    """Main function"""
    while True:
        choice = show_menu()
        
        if choice == "1":
            clear_screen()
            print_header()
            run_pipeline()
            print("\n" + "═" * 60)
            print("PIPELINE COMPLETE!")
            print("═" * 60)
            input("\nPress Enter to continue...")
        
        elif choice == "2":
            clear_screen()
            print_header()
            print("\n[+] Calculating costs from existing data...")
            try:
                from cost_model import main as cost_main
                cost_main()
            except Exception as e:
                print(f"[!] Error: {e}")
                print("[!] Please run the complete pipeline first")
            input("\nPress Enter to continue...")
        
        elif choice == "3":
            individual_steps()
        
        elif choice == "4":
            view_reports()
        
        elif choice == "5":
            clean_data()
        
        elif choice == "6":
            print("\nThank you for using FlowSpend!")
            print("Goodbye! 👋")
            break
        
        else:
            print("\nInvalid choice! Please try again.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required")
        sys.exit(1)
    
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    os.makedirs('src', exist_ok=True)
    
    main()