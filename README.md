# Analyst_report_portfolios

## Description
This project is the implementation of the paper 'LLMs Analyzing the Analysts: Do BERT and GPT Extract More
Value from Financial Analyst Reports?'

Portfolios were constructed based on sentiment scores or analyst score extracted from analyst reports.
- Sentiment scores were extracted using three models; GPT-3.5, KoBERT, KR-FinBERT.
- Analyst scores were obtained by quantifing the opinions provided in the analyst reports. Analyst opinions were manually translated into numerical values using the following scale: 1 for sell, sell (maintain), underweight, and market underperform, 2 for neutral, market perform, 3 for hold, 4 for buy, market outperform, short-term buy, and buy (maintain), and 5 for strong buy.

## How to run the code
Each folder contains following files
- `config.py`: Contains configuration variables like start and end dates for data analysis, default transaction cost, and the path to store price data.
- `utils.py`: Provides utility functions including directory creation (mkdir), and functions to get previous (prev_month) and next months (next_month). Also, it sets up basic logging.
- `evaluation.py` : Contains functions to fetch KOSPI data (fetch_kospi_data) and evaluate the portfolio (evaluate_portfolio). It calculates and compares various metrics like annualized return, volatility, Sharpe ratio, and maximum drawdown (MDD) for the portfolio and KOSPI.
- `strategy.py`: Includes functions to fetch price data for stock codes (get_price_data), and generate buy signals based on different strategies.
- `main.py`: Serves as the entry point for the application./
/



Example usage
```
python main.py --dataset_name gpt_3.5 --strategy_name incremental_long_short

```
This command will run the `main.py` script using scores extracted from 'gpt 3.5' as the dataset and the 'incremental_long_short' strategy.
