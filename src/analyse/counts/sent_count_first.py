# %% [markdown]
# ## Process
# We count the number of reports in each death category, ignoring reports that
# don't match any known category. We then save the results to a .csv file.
# %% [markdown]
# ### Importing libraries

import os
import re

import pandas as pd

PATH = os.path.dirname(__file__)
REPORTS_PATH = os.path.abspath(f"{PATH}/../../data")
CORRECT_PATH = os.path.abspath(f"{PATH}/../../correct")

# %% [markdown]
# ### Reading the reports

reports = pd.read_csv(f"{REPORTS_PATH}/reports-analysed.csv")
fetched = pd.read_csv(f"{REPORTS_PATH}/reports.csv")

fetched_non_na = fetched.dropna(subset=["this_report_is_being_sent_to"])

# %% [markdown]
# ### Calculating the due status for each report

today = pd.to_datetime("today")
report_date = pd.to_datetime(reports["date_of_report"], dayfirst=True)
report_due = (today - report_date).dt.days > 56

# %% [markdown]
# ### Splitting the sent to and reply urls

vbar = re.compile(r"\s*\|\s*")
non_na = reports.assign(year=report_date.dt.year).dropna(subset=["this_report_is_being_sent_to"]).copy()
non_na["status"] = "overdue"
non_na["sent_to"] = non_na["this_report_is_being_sent_to"].str.split(vbar)
non_na["no. recipients"] = non_na["sent_to"].str.len()

non_na["replies"] = (
    non_na["reply_urls"]
    .fillna("")
    .str.split(vbar)
    .apply(lambda replies: [reply for reply in replies if "Response" in reply])
)
non_na["no. replies"] = non_na["replies"].str.len()

non_na["escaped_urls"] = non_na["reply_urls"].str.replace(r"[-_]|%20", " ", regex=True).fillna("")

# %% [markdown]
# ### Status based on no. recipients vs replies

equal_replies = non_na.apply(lambda x: len(x["sent_to"]) == len(x["replies"]) and len(x["sent_to"]) > 0, axis=1)
non_na.loc[equal_replies, "status"] = "received"
non_na.loc[~report_due, "status"] = "pending"

# %% [markdown]
# ### Status based on recipients in replies

exploded = non_na.explode("sent_to", ignore_index=True)
responded = exploded.apply(lambda x: str(x["sent_to"]) in str(x["escaped_urls"]), axis=1)
exploded["status"] = exploded["status"].mask(responded, "received")

# %% [markdown]
# ### Calculating the counts for each recipient

sent_types = exploded.value_counts(["sent_to", "status"]).unstack(fill_value=0)
sent_types["no. PFDs"] = exploded["sent_to"].value_counts()
sent_types = sent_types[["no. PFDs", "overdue", "pending", "received"]].sort_values("no. PFDs", ascending=False)
sent_types["% received"] = (sent_types["received"] / sent_types["no. PFDs"] * 100).round(1)

sent_counts = exploded.value_counts("sent_to")
sent_years = exploded.value_counts(["year", "status"]).unstack(fill_value=0)
type_counts = exploded.value_counts("status")

# %% [markdown]
# ### Calculating the status of each report

non_na.loc[:, "response status"] = "partial"

# for each report, calculate the list of recipients with responses
responses_from = lambda row: [sent for sent in row["sent_to"] if sent in row["escaped_urls"]]
with_responses = non_na.apply(responses_from, axis=1)

# if there's none, mark overdue
# no_responses = with_responses.str.len() == 0
no_responses = (with_responses.str.len() == 0) & (non_na["replies"].str.len() == 0)
non_na.loc[no_responses, "response status"] = "overdue"

# if there's an equal number of recipients and replies, mark completed
equal_len = (non_na["sent_to"].str.len() <= non_na["replies"].str.len()) & (non_na["sent_to"].str.len() > 0)
non_na.loc[equal_len, "response status"] = "completed"

# if all are responded to, mark completed
all_responses = with_responses.str.len() >= non_na["sent_to"].str.len()
non_na.loc[all_responses, "response status"] = "completed"

# if a report is pending or overdue and less than 56 days old, mark pending
non_na.loc[~report_due & (non_na["response status"] == "overdue"), "response status"] = "pending"
non_na.loc[~report_due & (non_na["response status"] == "partial"), "response status"] = "pending"

# %% [markdown]
# ### Adding the non_na rows back to the reports

reports.loc[:, "response status"] = "failed"
reports.loc[non_na.index, "response status"] = non_na["response status"]
empty_requests = reports["this_report_is_being_sent_to"].isna()
reports.loc[empty_requests, "response status"] = "no requests"

reports.loc[:, "no. recipients"] = 0
reports.loc[non_na.index, "no. recipients"] = non_na["no. recipients"]

reports.loc[:, "no. replies"] = 0
reports.loc[non_na.index, "no. replies"] = non_na["no. replies"]

print(reports[["ref", "response status"]].head(10))
print(reports["response status"].value_counts())

# %% [markdown]
# ### Calculating response status over time

status_years = reports.assign(year=report_date.dt.year).value_counts(["year", "response status"]).unstack(fill_value=0)

failed_index = True
try:
    status_years = status_years[["no requests", "failed", "pending", "overdue", "partial", "completed"]]
except KeyError:
    failed_index = False
    status_years = status_years[["no requests", "pending", "overdue", "partial", "completed"]]

# %% [markdown]
# ### Writing back the reports with the status

# Add our new columns to the reports
report_columns = reports.columns.tolist()
report_columns.insert(0, "response status")
count_idx = report_columns.index("this_report_is_being_sent_to") + 1
report_columns.insert(count_idx, "no. replies")
report_columns.insert(count_idx, "no. recipients")
report_columns = list(dict.fromkeys(report_columns))

reports[report_columns].to_csv(f"{REPORTS_PATH}/reports-analysed.csv", index=False)
