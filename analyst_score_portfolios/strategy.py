import pandas as pd
from utils import prev_month, mkdir
import FinanceDataReader as fdr
from config import DATA_PATH
import os


def get_price_data(codes):

    mkdir(DATA_PATH)
    
    for code in codes:
        if not os.path.exists(f"{DATA_PATH}/{code}.csv"):
            try:
                price_df = fdr.DataReader(code)
                price_df.to_csv(f"{DATA_PATH}/{code}.csv")
            except Exception as e:
                print(f"Error fetching data for code {code}: {e}")



def score_4_5_buy_signals(df):
    """
    Generates buy signals for stocks where the score is either 4 or 5.
    
    Args:
    df (pd.DataFrame): DataFrame containing stock data with 'score' column.

    Returns:
    pd.DataFrame: DataFrame with buy signals.
    """
    signal = pd.DataFrame(columns=['name', 'code', 'target_price', 'score'])
    for code in df['code'].unique():
        target_report = df[df['code'] == code]
        for i in range(len(target_report)):
            if target_report.iloc[i]['score'] in [4, 5]:
                dt = target_report.iloc[i].name
                signal.loc[dt] = target_report.iloc[i]
    return signal.sort_index()


def score_upwards_buy_signals(df):
    """
    Generates buy signals for stocks where the score has increased from the previous report.
    
    Args:
    df (pd.DataFrame): DataFrame containing stock data with 'score' column.

    Returns:
    pd.DataFrame: DataFrame with buy signals.
    """
    signal = pd.DataFrame(columns=['name', 'code', 'target_price', 'score'])
    for code in df['code'].unique():
        target_report = df[df['code'] == code]
        for i in range(1, len(target_report)):
            if target_report.iloc[i]['score'] >= target_report.iloc[i - 1]['score']:
                dt = target_report.iloc[i].name
                signal.loc[dt] = target_report.iloc[i]
    return signal.sort_index()

def compute_daily_returns(signal, months, transaction_cost):

    port_monthly_returns = {}

    for month in months[1:]:

        port_daily_returns = {}
        st = prev_month(month)
        target_signal = signal.loc[st]
        # # Skip if no data for that month
        # if st not in signal.index:
        #     continue

        port_codes = list(set(target_signal['code']))

        for code in port_codes:
            try:
                target_price = pd.read_csv(DATA_PATH + f'/{code}.csv', parse_dates=['Date'], index_col='Date')
                if month not in target_price.index:
                    print(f"Month {month} data is not available for code {code}")
                    continue

                price_open = target_price.loc[st].iloc[-1]['Close']
                price_close = target_price.loc[month]['Close'][0]

                initial_return = (price_close - price_open) / price_open - 2 * transaction_cost
                daily_pct_return = target_price.loc[month]['Close'].pct_change()
                daily_pct_return.iloc[0] = initial_return
                port_daily_returns[code] = daily_pct_return

            except Exception as e:
                print(f"Error processing code {code} for month {month}: {e}")

        port_daily_returns = pd.DataFrame(port_daily_returns)
        port_monthly_returns[month] = port_daily_returns.mean(axis=1)

    return pd.concat(port_monthly_returns.values(), axis=0)
