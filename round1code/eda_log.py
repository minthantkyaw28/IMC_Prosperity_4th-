import os
import sys
import json
import glob

def analyze_log(filepath):
    print(f"\n{'='*50}")
    print(f"Analyzing Log: {os.path.basename(filepath)}")
    print(f"{'='*50}")
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        total_profit = data.get('profit', 0)
        print(f"OVERALL PROFIT (XIRECS): {total_profit:,.2f}")
        
        activities = data.get('activitiesLog', '')
        if not activities:
            print("No activitiesLog found in this file.")
            return
            
        lines = activities.strip().split('\n')
        if len(lines) <= 1:
            print("activitiesLog is completely empty.")
            return
        
        # We track the final PNL recorded for each product in the activities array
        final_pnl = {}
        for line in lines[1:]:
            parts = line.split(';')
            if len(parts) >= 17: # Checking if it fits the schema
                product = parts[2]
                try:
                    pnl = float(parts[-1])
                    final_pnl[product] = pnl
                except ValueError:
                    pass
                    
        print("\n--- Final PNL per Product ---")
        for prod, pnl in final_pnl.items():
            # Color code prints for positive vs negative technically requires ANSI codes, 
            # but we can just use clear text formatting.
            marker = "🟢" if pnl >= 0 else "🔴"
            print(f"{marker} {prod:<22} : {pnl:>10,.2f}")
            
        positions = data.get('positions', [])
        if positions:
            print("\n--- Final Held Inventory ---")
            for item in positions:
                sym = item.get('symbol', 'UNKNOWN')
                qty = item.get('quantity', 0)
                if sym != 'XIRECS':  # XIRECS is the currency, not an inventory asset
                    print(f"{sym:<25}: {qty:>5}")
                    
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(script_dir, 'logs')

    # If the user provides a specific file or name
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            # Auto-resolve "log2" -> "logs/log2.json"
            if not arg.endswith('.json'):
                target_file = os.path.join(logs_dir, f"{arg}.json")
            else:
                if os.path.isabs(arg) or os.sep in arg:
                    target_file = arg
                else:
                    target_file = os.path.join(logs_dir, arg)
                    
            if os.path.exists(target_file):
                analyze_log(target_file)
            else:
                print(f"File not found: {target_file}")
    else:
        # Otherwise, dynamically find all .json files in the 'logs' folder next to this script
        
        if not os.path.exists(logs_dir):
            print(f"Could not find logs directory at: {logs_dir}")
            return
            
        json_files = glob.glob(os.path.join(logs_dir, '*.json'))
        json_files.sort(key=os.path.getmtime) # Sort by modification time (oldest to newest)
        
        if not json_files:
            print(f"No .json log files found in {logs_dir}!")
            return
            
        for filepath in json_files:
            analyze_log(filepath)

if __name__ == '__main__':
    main()
