import json
import os

import pandas as pd

PATH = os.path.dirname(__file__)
REPORTS_PATH = os.path.abspath(f"{PATH}/../../data")


def sort_by_date(df):
    df["date_of_report"] = pd.to_datetime(df["date_of_report"], format='%d/%m/%Y')
    df.sort_values(by="date_of_report", inplace=True, ascending=False)
    df["date_of_report"] = df["date_of_report"].dt.strftime('%d/%m/%Y')
    df.to_csv(input_csv, index=False)


input_csv = os.path.abspath(f"{REPORTS_PATH}/reports-corrected.csv")
reports = pd.read_csv(input_csv)
sort_by_date(reports)
