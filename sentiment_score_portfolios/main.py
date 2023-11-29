import strategy
import pandas as pd  # It seems you were using pandas without importing it.
from config import DEFAULT_START_DATE, DEFAULT_END_DATE, DEFAULT_TRANSACTION_COST
from evaluation import fetch_kospi_data, evaluate_portfolio
import logging
from utils import next_month 
import argparse 

logging.basicConfig(level=logging.INFO)

def main(args):
    dataset_path = f'./score/{args.dataset_name}.csv'
    logging.info(f"Loading dataset from {dataset_path}")
    df = pd.read_csv(dataset_path, index_col=0)
    df.index = pd.to_datetime(df.index)
    df = df[(df.index >= args.start_date) & (df.index <= args.end_date)]
    
    df['code'] = df['code'].str.replace("'", "")
    codes = df['code'].unique()

    
    print("Fetching price data for the stock codes...")
    # Fetch price data
    strategy.get_price_data(codes)

    month_current = '2016-01'
    months = []
    while(month_current < '2023-03'):
        months.append(month_current)
        month_current = next_month(month_current)


    if args.strategy_name == 'incremental_long_short':
        result = strategy.incremental_long_short_portfolio(args.dataset_name, months, df, dataset_path)
    elif args.strategy_name == 'incremental_long_only':
        result = strategy.incremental_long_only_portfolio(months, df, dataset_path)
    elif args.strategy_name == 'static_long_short':
        result = strategy.static_long_short_portfolio(args.dataset_name, months, df, dataset_path) 
    elif args.strategy_name == 'static_long_only':
        result = strategy.static_long_only_portfolio(months, df, dataset_path)
    else:
        logging.error(f"Strategy {args.strategy_name} is not recognized.")
        return
    
    logging.info("Evaluating the portfolio against KOSPI")    
    port_daily_returns = result 
    combined_port_daily_returns = pd.concat(port_daily_returns.values()).sort_index()

    # Fetch KOSPI data
    kospi_daily_returns = fetch_kospi_data(args.start_date, args.end_date)

    
    # Evaluate the portfolio against KOSPI
    evaluate_portfolio(combined_port_daily_returns, kospi_daily_returns, args.dataset_name)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run stock strategies with different parameters.')
    parser.add_argument('--dataset_name', required=True, help='Name of the dataset (excluding .csv)')
    parser.add_argument('--transaction_cost', type=float, default=DEFAULT_TRANSACTION_COST, help='Transaction cost to be considered')
    parser.add_argument('--strategy_name', required=True, help='strategy to use (e.g., incremental_long_short, incremental_long_only, etc.)')
    parser.add_argument('--start_date', type=str, default=DEFAULT_START_DATE, help="Start date for portfolio evaluation and KOSPI data")
    parser.add_argument('--end_date', type=str, default=DEFAULT_END_DATE, help="End date for portfolio evaluation and KOSPI data")
    
    args = parser.parse_args()
    main(args)
