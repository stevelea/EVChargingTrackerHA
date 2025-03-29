"""
Test script for the data visualizer module to check if it's handling Series data properly
"""

import sys
import pandas as pd
from data_storage import load_charging_data
from data_visualizer import create_visualizations

def run_test():
    """Run a simple test of the data visualizer with existing data"""
    print("Loading test data...")
    charging_data = load_charging_data()
    
    if not charging_data:
        print("No data found. The test will use a small sample dataframe.")
        # Create a small sample dataframe
        data = {
            'date': ['2025-03-01', '2025-03-15', '2025-03-20', '2025-03-25'],
            'total_kwh': [10.5, 15.2, 8.3, 12.1],
            'peak_kw': [7.2, 8.1, 6.5, 7.8],
            'cost_per_kwh': [0.25, 0.28, 0.22, 0.26],
            'total_cost': [2.62, 4.26, 1.83, 3.15],
            'location': ['Location A', 'Location B', 'Location A', 'Location C'],
            'provider': ['Provider X', 'Provider Y', 'Provider X', 'Provider Z']
        }
        df = pd.DataFrame(data)
    else:
        print(f"Found {len(charging_data)} data records. Converting to DataFrame...")
        df = pd.DataFrame(charging_data)
        
    print("Dataframe columns:", df.columns.tolist())
    print("Sample row:", df.iloc[0].to_dict())
    
    print("\nCreating visualizations...")
    try:
        figures = create_visualizations(df)
        print(f"Successfully created {len(figures)} figures:")
        for fig_name in figures.keys():
            print(f"- {fig_name}")
        print("\nTest completed successfully! The fix for Series data is working.")
    except Exception as e:
        print(f"Error creating visualizations: {str(e)}")
        print("\nFull error details:")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)