import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob

def load_data(base_path):
    """Loads and aggregates prices and trades data."""
    prices_files = glob.glob(os.path.join(base_path, 'prices_round_1_day_*.csv'))
    trades_files = glob.glob(os.path.join(base_path, 'trades_round_1_day_*.csv'))
    
    # Sort files to ensure chronological order: day -2, -1, 0
    prices_files.sort(key=lambda x: int(os.path.basename(x).split('_')[-1].split('.')[0]))
    trades_files.sort(key=lambda x: int(os.path.basename(x).split('_')[-1].split('.')[0]))
    
    prices_list = []
    for f in prices_files:
        df = pd.read_csv(f, sep=';')
        prices_list.append(df)
    prices_df = pd.concat(prices_list, ignore_index=True)
    
    trades_list = []
    for f in trades_files:
        df = pd.read_csv(f, sep=';')
        # Add day column to trades based on filename to align with prices
        day = int(os.path.basename(f).split('_')[-1].split('.')[0])
        df['day'] = day
        trades_list.append(df)
    trades_df = pd.concat(trades_list, ignore_index=True)
    
    # Create continuous time index (each day has timestamps 0 to 999900 in increments of 100)
    # Assuming each day has 1,000,000 max timestamps.
    prices_df['continuous_time'] = (prices_df['day'] + 2) * 1000000 + prices_df['timestamp']
    trades_df['continuous_time'] = (trades_df['day'] + 2) * 1000000 + trades_df['timestamp']
    
    return prices_df, trades_df

def run_eda(prices_df, trades_df, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'charts'), exist_ok=True)
    
    products = prices_df['product'].unique()
    
    # Correlation Analysis
    print("--- Correlation Analysis ---")
    pivoted = prices_df.pivot(index='continuous_time', columns='product', values='mid_price')
    corr = pivoted.corr()
    print(corr)
    
    # Plotting each product
    for product in products:
        prod_data = prices_df[prices_df['product'] == product].copy()
        
        # 1. Price Trajectory
        plt.figure(figsize=(12, 6))
        plt.plot(prod_data['continuous_time'], prod_data['mid_price'], label='Mid Price')
        plt.title(f'{product} - Price Trajectory')
        plt.xlabel('Continuous Time')
        plt.ylabel('Price')
        plt.legend()
        plt.savefig(os.path.join(output_dir, f'charts/{product}_price_trajectory.png'))
        plt.close()
        
        # 2. Spread Analysis
        prod_data['spread'] = prod_data['ask_price_1'] - prod_data['bid_price_1']
        plt.figure(figsize=(12, 6))
        plt.plot(prod_data['continuous_time'], prod_data['spread'], alpha=0.5, color='orange')
        plt.title(f'{product} - Bid-Ask Spread')
        plt.xlabel('Continuous Time')
        plt.ylabel('Spread')
        plt.savefig(os.path.join(output_dir, f'charts/{product}_spread.png'))
        plt.close()
        
        # 3. Volume Imbalance
        prod_data['volume_imbalance'] = prod_data['bid_volume_1'] - prod_data['ask_volume_1']
        plt.figure(figsize=(12, 6))
        plt.plot(prod_data['continuous_time'], prod_data['volume_imbalance'], alpha=0.3, color='purple')
        plt.title(f'{product} - Top of Book Volume Imbalance (Bid - Ask)')
        plt.xlabel('Continuous Time')
        plt.ylabel('Volume Imbalance')
        plt.savefig(os.path.join(output_dir, f'charts/{product}_volume_imbalance.png'))
        plt.close()
        
        print(f"\nStats for {product}:")
        print(f"Average Spread: {prod_data['spread'].mean():.2f}")
        print(f"Median Spread: {prod_data['spread'].median():.2f}")
        print(f"Volatility (std of mid_price): {prod_data['mid_price'].std():.2f}")

    # Trade executions summary
    print("\n--- Trade Executions Summary ---")
    summary = trades_df.groupby('symbol')['quantity'].agg(['mean', 'sum', 'count'])
    print(summary)


if __name__ == "__main__":
    base_path = '../ROUND1'
    output_dir = '.'
    
    print("Loading data...")
    prices, trades = load_data(base_path)
    
    print("Running EDA...")
    run_eda(prices, trades, output_dir)
    print("EDA completed. Charts saved to 'charts/' directory.")
