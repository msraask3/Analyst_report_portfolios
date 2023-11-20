import argparse
from config import DEFAULT_START_DATE, DEFAULT_END_DATE, DEFAULT_TRANSACTION_COST, DATA_PATH
from utils import next_month
from evaluation import evaluate_portfolio, fetch_kospi_data
from strategy import get_price_data, score_4_5_buy_signals, score_upwards_buy_signals, compute_daily_returns
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description='Evaluate stock portfolio strategies')
    parser.add_argument('--dataset_name', type=str, required=True, help='Path to the dataset')
    parser.add_argument('--transaction_cost', type=float, default=DEFAULT_TRANSACTION_COST, help='Transaction cost for trades')
    parser.add_argument('--strategy_name', type=str, required=True, choices=['score_4_5', 'score_upwards'], help='Name of the strategy to use')
    args = parser.parse_args()


    # Load the dataset
    dataset_path = f'/Users/kimseonmi/Desktop/NLP/Analyst/코드/monthly_portfolio/score/{args.dataset_name}.csv'
    df = pd.read_csv(dataset_path, index_col=0)
    df.index = pd.to_datetime(df.index)
    # Extract stock codes
    df['code'] = df['code'].str.replace("'", "")
    codes = list(set(df['code']))
    
    print("Fetching price data for the stock codes...")
    # Fetch price data
    get_price_data(codes)

    # Generate buy signals based on the selected strategy
    if args.strategy_name == 'score_4_5':
        signal = score_4_5_buy_signals(df)
    elif args.strategy_name == 'score_upwards':
        signal = score_upwards_buy_signals(df)

        # Define the months range
    month_current = '2016-01'
    months = []
    while(month_current < '2023-03'):
        months.append(month_current)
        month_current = next_month(month_current)

    port_daily_returns = compute_daily_returns(signal, months, args.transaction_cost)

    # Fetch KOSPI data
    kospi_daily_returns = fetch_kospi_data(DEFAULT_START_DATE, DEFAULT_END_DATE)

    # Evaluate the portfolio
    evaluation_results = evaluate_portfolio(port_daily_returns, kospi_daily_returns, args.dataset_name)
    print(evaluation_results)

if __name__ == "__main__":
    main()
