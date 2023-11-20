import os
import pandas as pd
from dateutil.relativedelta import relativedelta
import logging

logging.basicConfig(level=logging.INFO)

def mkdir(name):
    try:
        os.mkdir(name)
        logging.info(f"Directory {name} created successfully!")
    except Exception as e:
        logging.error(f"Error creating directory {name}: {str(e)}")
        return False
    return True

def prev_month(time_point):
    # print(time_point)
    time_point = pd.to_datetime(time_point) - relativedelta(months=1)
    return str(time_point)[:7]

def next_month(time_point):
    time_point = pd.to_datetime(time_point) + relativedelta(months=1)
    return str(time_point)[:7]
