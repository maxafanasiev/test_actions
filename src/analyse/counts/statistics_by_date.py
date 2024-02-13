import pandas as pd
from datetime import datetime
import os

from helpers import toml_stats

PATH = os.path.dirname(__file__)
file_path = os.path.abspath(f"{PATH}/data/sent/received_percents.csv")
date = datetime.now().strftime("%d/%m/%Y")
percent = ','.join(str(toml_stats["requests for response"]["requests received"][1]).split('.'))
new_data = pd.DataFrame({
    "Date": [date],
    "Requests Received Percent": [percent]
})

if os.path.exists(file_path):
    existing_data = pd.read_csv(file_path)
    updated_data = pd.concat([existing_data, new_data], ignore_index=True)
else:
    updated_data = new_data

updated_data.to_csv(file_path, index=False)
