import pandas as pd
import numpy as np
import FinanceDataReader as fdr

def fetch_kospi_data(start_date, end_date):
    """Fetches KOSPI daily returns data."""
    kospi_daily_returns = fdr.DataReader('KS11', start_date, end_date)
    kospi_daily_returns = kospi_daily_returns['Close'].pct_change().dropna()
    return kospi_daily_returns

def evaluate_portfolio(port_daily_returns, kospi_daily_returns, dataset_name):
    """Evaluates and compares the performance of the portfolio and KOSPI."""
    port_cumul_returns = (1 + port_daily_returns).cumprod()
    kospi_cumul_returns = (1 + kospi_daily_returns).cumprod()

    num_years = (port_daily_returns.index[-1] - port_daily_returns.index[0]).days / 365.25
    port_annualized_return = (port_cumul_returns.iloc[-1] / port_cumul_returns.iloc[0]) ** (1/num_years) - 1
    kospi_annualized_return = (kospi_cumul_returns.iloc[-1] / kospi_cumul_returns.iloc[0]) ** (1/num_years) - 1

    port_volatility = port_daily_returns.std() * np.sqrt(252)
    kospi_volatility = kospi_daily_returns.std() * np.sqrt(252)

    sharpe_ratio_port = port_annualized_return / port_volatility
    sharpe_ratio_kospi = kospi_annualized_return / kospi_volatility

    mdd_port = (port_cumul_returns / port_cumul_returns.cummax() - 1).min()
    mdd_kospi = (kospi_cumul_returns / kospi_cumul_returns.cummax() - 1).min()

    # Print the evaluation results
    print("Annualised Return")
    print(f"{dataset_name} Annualised Return: {port_annualized_return * 100:.2f}%")
    print(f"KOSPI Annualised Return: {kospi_annualized_return * 100:.2f}%")
    
    print("\nAnnualised Volatility")
    print(f"{dataset_name} Annualised Volatility: {port_volatility * 100:.2f}%")
    print(f"KOSPI Annualised Volatility: {kospi_volatility * 100:.2f}%")
    
    print("\nSharpe Ratio")
    print(f"{dataset_name} Annualised Sharpe Ratio: {sharpe_ratio_port:.4f}")
    print(f"KOSPI Sharpe Ratio: {sharpe_ratio_kospi:.4f}")
    
    print("\nMDD")
    print(f"{dataset_name} MDD: {mdd_port * 100:.2f}%")
    print(f"KOSPI MDD: {mdd_kospi * 100:.2f}%")

    return {
        'port_annualized_return': port_annualized_return,
        'kospi_annualized_return': kospi_annualized_return,
        'port_volatility': port_volatility,
        'kospi_volatility': kospi_volatility,
        'sharpe_ratio_port': sharpe_ratio_port,
        'sharpe_ratio_kospi': sharpe_ratio_kospi,
        'mdd_port': mdd_port,
        'mdd_kospi': mdd_kospi
    }
