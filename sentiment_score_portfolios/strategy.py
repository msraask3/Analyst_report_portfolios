import pandas as pd
import warnings
from tqdm import tqdm
import copy
from dateutil.relativedelta import relativedelta
from config import DATA_PATH, DEFAULT_TRANSACTION_COST
from utils import mkdir, prev_month, next_month
import os 
import FinanceDataReader as fdr
import logging

warnings.filterwarnings('ignore')


def get_price_data(codes):

    mkdir(DATA_PATH)
    
    for code in codes:
        if not os.path.exists(f"{DATA_PATH}/{code}.csv"):
            try:
                price_df = fdr.DataReader(code)
                price_df.to_csv(f"{DATA_PATH}/{code}.csv")
            except Exception as e:
                print(f"Error fetching data for code {code}: {e}")


def calculate_returns(codes, returns_dict, j, s, file_path=DATA_PATH, is_short=False, transaction_cost=DEFAULT_TRANSACTION_COST):

    if len(codes) == 0: 
        date_range = pd.date_range(start=j, end=next_month(j)) 
        returns_dict["empty"] = pd.Series([0]*len(date_range), index=date_range)
    else:
        for code in codes:
            try:
                target_price = pd.read_csv(f'{file_path}/{code}.csv').set_index('Date')
                target_price.index = pd.to_datetime(target_price.index)

                price_open = target_price.loc[s].iloc[-1]['Close']  # assume to buy at the close price of the last day of the previous month
                price_close = target_price.loc[j]['Close'][0]  # assume to sell at the close price of the first day of the month

                if is_short:
                    initial_return = (price_close - price_open) / price_open - 2 * transaction_cost
                else:
                    initial_return = (price_close - price_open) / price_open - transaction_cost 

                daily_pct_return = target_price.loc[j]['Close'].pct_change()
                daily_pct_return.iloc[0] = initial_return  # the first day return includes the transaction cost
                returns_dict[code] = daily_pct_return  # save the daily return for the stock
            except Exception as e:
                print(f"Error with code {code}: {e}")
                continue


def incremental_long_short_portfolio(dataset_name, months, df, file_path=DATA_PATH):
    port_daily_returns = {}
    all_long_daily_returns = {}
    all_short_daily_returns = {}

    for j in tqdm(months[1:]):
        st = j
        s = prev_month(st)

        if dataset_name == "kr_finbert":
            prev_df = df.loc[s].rename(columns={'pos_score': 'prev_pos_score', 'neg_score': 'prev_neg_score'})
            current_df = df.loc[st].rename(columns={'pos_score': 'current_pos_score', 'neg_score': 'current_neg_score'})
            df_change = pd.merge(prev_df, current_df, on='code', how='inner')
            counts = df_change['code'].value_counts()
            overlap_codes = counts[counts >= 2].index
            mean_values = df_change[df_change['code'].isin(overlap_codes)].groupby('code')[['prev_pos_score', 'current_pos_score','prev_neg_score','current_neg_score']].mean()
            df_change = df_change.merge(mean_values, on='code', how='left', suffixes=('', '_mean'))
            mask = df_change['code'].isin(overlap_codes)
            df_change.loc[mask, 'prev_pos_score'] = df_change.loc[mask, 'prev_pos_score_mean']
            df_change.loc[mask, 'current_pos_score'] = df_change.loc[mask, 'current_pos_score_mean']
            df_change.loc[mask, 'prev_neg_score'] = df_change.loc[mask, 'prev_neg_score_mean']
            df_change.loc[mask, 'current_neg_score'] = df_change.loc[mask, 'current_neg_score_mean']
            df_change.drop(columns=['prev_pos_score_mean', 'current_pos_score_mean','prev_neg_score_mean','current_neg_score_mean'], inplace=True)
            df_change['pos_change'] = (df_change['current_pos_score'] - df_change['prev_pos_score']) / df_change['prev_pos_score'] 
            df_change['neg_change'] = (df_change['current_neg_score'] - df_change['prev_neg_score']) / df_change['prev_neg_score']
            df_change = df_change[(df_change['pos_change'] < 10) & (df_change['neg_change'] < 10)]
            df_month_pos = df_change[df_change['pos_change'] >= df_change['pos_change'].quantile(0.8)]
            df_month_neg = df_change[df_change['neg_change'] >= df_change['neg_change'].quantile(0.8)]
            df_month_pos_code = df_month_pos['code'].tolist()
            df_month_neg_code = df_month_neg['code'].tolist()
            df_month_pos_codes = list(set(df_month_pos_code) - set(df_month_neg_code))
            df_month_neg_codes = list(set(df_month_neg_code) - set(df_month_pos_code))

        else:
            prev_df = df.loc[s].rename(columns={'pos_score': 'prev_pos_score'})
            current_df = df.loc[st].rename(columns={'pos_score': 'current_pos_score'})
            df_change = pd.merge(prev_df, current_df, on='code', how='inner')
            counts = df_change['code'].value_counts()
            overlap_codes = counts[counts >= 2].index
            mean_values = df_change[df_change['code'].isin(overlap_codes)].groupby('code')[
                ['prev_pos_score', 'current_pos_score']].mean()
            df_change = df_change.merge(mean_values, on='code', how='left', suffixes=('', '_mean'))
            mask = df_change['code'].isin(overlap_codes)
            df_change.loc[mask, 'prev_pos_score'] = df_change.loc[mask, 'prev_pos_score_mean']
            df_change.loc[mask, 'current_pos_score'] = df_change.loc[mask, 'current_pos_score_mean']
            df_change.drop(columns=['prev_pos_score_mean', 'current_pos_score_mean'], inplace=True)

            df_change['pos_change'] = (df_change['current_pos_score'] - df_change['prev_pos_score']) / df_change[
                'prev_pos_score']
            df_change = df_change[(df_change['pos_change'] < 10)]

            df_month_pos = df_change[df_change['pos_change'] >= df_change['pos_change'].quantile(0.8)]
            df_month_neg = df_change[df_change['pos_change'] <= df_change['pos_change'].quantile(0.2)]
            df_month_pos_code = df_month_pos['code'].tolist()
            df_month_neg_code = df_month_neg['code'].tolist()
            df_month_pos_codes = list(set(df_month_pos_code) - set(df_month_neg_code))
            df_month_neg_codes = list(set(df_month_neg_code) - set(df_month_pos_code))

        long_daily_returns = {}  
        short_daily_returns = {}

        calculate_returns(df_month_pos_codes, long_daily_returns, j, s, DATA_PATH, False, DEFAULT_TRANSACTION_COST)
        calculate_returns(df_month_neg_codes, short_daily_returns, j, s, DATA_PATH, True, DEFAULT_TRANSACTION_COST)

        all_long_daily_returns[j] = pd.DataFrame(long_daily_returns)
        all_short_daily_returns[j] = pd.DataFrame(short_daily_returns)

        long_daily_returns_mean = all_long_daily_returns[j].mean(axis=1)
        short_daily_returns_mean = all_short_daily_returns[j].mean(axis=1)

        portfolio_daily_returns = long_daily_returns_mean - short_daily_returns_mean
        port_daily_returns[j] = portfolio_daily_returns

    return port_daily_returns


def incremental_long_only_portfolio(months, df, file_path= DATA_PATH):
    port_daily_returns = {}
    all_long_daily_returns = {}

    for j in tqdm(months[1:]):
        st = j
        s = prev_month(st)

        prev_df = df.loc[s].rename(columns={'pos_score': 'prev_pos_score'})
        current_df = df.loc[st].rename(columns={'pos_score': 'current_pos_score'})
        df_change = pd.merge(prev_df, current_df, on='code', how='inner')
        counts = df_change['code'].value_counts()
        overlap_codes = counts[counts >= 2].index
        mean_values = df_change[df_change['code'].isin(overlap_codes)].groupby('code')[
            ['prev_pos_score', 'current_pos_score']].mean()
        df_change = df_change.merge(mean_values, on='code', how='left', suffixes=('', '_mean'))
        mask = df_change['code'].isin(overlap_codes)
        df_change.loc[mask, 'prev_pos_score'] = df_change.loc[mask, 'prev_pos_score_mean']
        df_change.loc[mask, 'current_pos_score'] = df_change.loc[mask, 'current_pos_score_mean']
        df_change.drop(columns=['prev_pos_score_mean', 'current_pos_score_mean'], inplace=True)

        df_change['pos_change'] = (df_change['current_pos_score'] - df_change['prev_pos_score']) / df_change[
            'prev_pos_score']
        df_change = df_change[(df_change['pos_change'] < 10)]

        df_month_pos = df_change[df_change['pos_change'] >= df_change['pos_change'].quantile(0.8)]
        df_month_pos_code = df_month_pos['code'].tolist()
        df_month_pos_codes = list(set(df_month_pos_code))

        long_daily_returns = {}  
        calculate_returns(df_month_pos_codes, long_daily_returns, j, s, DATA_PATH, False, DEFAULT_TRANSACTION_COST)
        all_long_daily_returns[j] = pd.DataFrame(long_daily_returns)
        long_daily_returns_mean = all_long_daily_returns[j].mean(axis=1)
        port_daily_returns[j] = long_daily_returns_mean

    return port_daily_returns


def static_long_only_portfolio( months, df, file_path=DATA_PATH):
    port_daily_returns = {}
    all_long_daily_returns = {}

    for j in tqdm(months[1:]):
        st = j
        s = prev_month(st)

        target_df = df.loc[st]

        counts = target_df['code'].value_counts()
        overlap_codes = counts[counts >=2].index
        mean_values = target_df[target_df['code'].isin(overlap_codes)].groupby('code')[['pos_score']].mean()

        target_df = target_df.merge(mean_values, on='code', how='left', suffixes=('', '_mean'))

        mask = target_df['code'].isin(overlap_codes)
        target_df.loc[mask, 'pos_score'] = target_df.loc[mask, 'pos_score_mean']
        target_df.drop(columns=['pos_score_mean'], inplace=True)

        df_month_pos = target_df[target_df['pos_score'] >= target_df['pos_score'].quantile(0.8)]
        df_month_pos_code = df_month_pos['code'].tolist()
        df_month_pos_codes = list(set(df_month_pos_code))
        long_daily_returns = {}  
        calculate_returns(df_month_pos_codes, long_daily_returns, j, s, DATA_PATH, False, DEFAULT_TRANSACTION_COST)
        all_long_daily_returns[j] = pd.DataFrame(long_daily_returns)
        long_daily_returns_mean = all_long_daily_returns[j].mean(axis=1)
        port_daily_returns[j] = long_daily_returns_mean

    return port_daily_returns



def static_long_short_portfolio(dataset_name, months, df, file_path=DATA_PATH):
    port_daily_returns = {}
    all_long_daily_returns = {}
    all_short_daily_returns = {}

    for j in tqdm(months[1:]):
        st = j
        s = prev_month(st)
        target_df = df.loc[st]

        if dataset_name == "kr_finbert":
            counts = target_df['code'].value_counts()
            overlap_codes = counts[counts >=2].index
            mean_values = target_df[target_df['code'].isin(overlap_codes)].groupby('code')[['pos_score', 'neg_score']].mean()

            target_df = target_df.merge(mean_values, on='code', how='left', suffixes=('', '_mean'))

            mask = target_df['code'].isin(overlap_codes)
            target_df.loc[mask, 'pos_score'] = target_df.loc[mask, 'pos_score_mean']
            target_df.loc[mask, 'neg_score'] = target_df.loc[mask, 'neg_score_mean']
            target_df.drop(columns=['pos_score_mean', 'neg_score_mean'], inplace=True)

            df_month_pos = target_df[target_df['pos_score'] >= target_df['pos_score'].quantile(0.8)]
            df_month_neg = target_df[target_df['neg_score'] >= target_df['neg_score'].quantile(0.8)]

            df_month_pos_code = df_month_pos['code'].tolist()
            df_month_neg_code = df_month_neg['code'].tolist()
            df_month_pos_codes = list(set(df_month_pos_code) - set(df_month_neg_code))
            df_month_neg_codes = list(set(df_month_neg_code) - set(df_month_pos_code))

        else:
            counts = target_df['code'].value_counts()
            overlap_codes = counts[counts >=2].index
            mean_values = target_df[target_df['code'].isin(overlap_codes)].groupby('code')[['pos_score']].mean()

            target_df = target_df.merge(mean_values, on='code', how='left', suffixes=('', '_mean'))

            mask = target_df['code'].isin(overlap_codes)
            target_df.loc[mask, 'pos_score'] = target_df.loc[mask, 'pos_score_mean']
            target_df.drop(columns=['pos_score_mean'], inplace=True)
            
            df_month_pos = target_df[target_df['pos_score'] >= target_df['pos_score'].quantile(0.8)]
            df_month_neg = target_df[target_df['pos_score'] <= target_df['pos_score'].quantile(0.2)]
            
            df_month_pos_code = df_month_pos['code'].tolist()
            df_month_neg_code = df_month_neg['code'].tolist()
            df_month_pos_codes = list(set(df_month_pos_code) - set(df_month_neg_code))
            df_month_neg_codes = list(set(df_month_neg_code) - set(df_month_pos_code))


        long_daily_returns = {}
        short_daily_returns = {}

        calculate_returns(df_month_pos_codes, long_daily_returns, j, s, DATA_PATH, False, DEFAULT_TRANSACTION_COST)
        calculate_returns(df_month_neg_codes, short_daily_returns, j, s, DATA_PATH, True, DEFAULT_TRANSACTION_COST)

        all_long_daily_returns[j] = pd.DataFrame(long_daily_returns)
        all_short_daily_returns[j] = pd.DataFrame(short_daily_returns)

        long_daily_returns_mean = all_long_daily_returns[j].mean(axis=1)
        short_daily_returns_mean = all_short_daily_returns[j].mean(axis=1)

        portfolio_daily_returns = long_daily_returns_mean - short_daily_returns_mean
        port_daily_returns[j] = portfolio_daily_returns

    return port_daily_returns
