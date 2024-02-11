import os

import pandas as pd

PATH = os.path.dirname(__file__)
DATA_PATH = os.path.abspath(f"{PATH}/data")
REPORTS_PATH = os.path.abspath(f"{PATH}/../../data")
CORRECT_PATH = os.path.abspath(f"{PATH}/../../correct")

input_csv = os.path.abspath(f"{os.path.dirname(__file__)}/../../data/reports-corrected.csv")
reports = pd.read_csv(input_csv)

reports["date_of_report"] = pd.to_datetime(reports["date_of_report"], format='%d/%m/%Y')

reports.sort_values(by="date_of_report", inplace=True, ascending=False)

reports["date_of_report"] = reports["date_of_report"].dt.strftime('%d/%m/%Y')

reports.to_csv(input_csv, index=False)
