import os
import re

import pandas as pd

from helpers import percent, monthly_toml_stats


PATH = os.path.dirname(__file__)
DATA_PATH = os.path.abspath(f"{PATH}/data")

reports = pd.read_csv(f"{DATA_PATH}/sent/last_month_reports.csv")

fetched_non_na = reports.dropna(subset=["this_report_is_being_sent_to"])

today = pd.to_datetime("today")
report_date = pd.to_datetime(reports["date_of_report"], dayfirst=True)
report_due = (today - report_date).dt.days > 56


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

equal_replies = non_na.apply(lambda x: len(x["sent_to"]) == len(x["replies"]) and len(x["sent_to"]) > 0, axis=1)
non_na.loc[equal_replies, "status"] = "received"
non_na.loc[~report_due, "status"] = "pending"

exploded = non_na.explode("sent_to", ignore_index=True)
responded = exploded.apply(lambda x: str(x["sent_to"]) in str(x["escaped_urls"]), axis=1)
exploded["status"] = exploded["status"].mask(responded, "received")

sent_types = exploded.value_counts(["sent_to", "status"]).unstack(fill_value=0)
sent_types["no. PFDs"] = exploded["sent_to"].value_counts()
sent_types = sent_types[["no. PFDs", "overdue", "pending", "received"]].sort_values("no. PFDs", ascending=False)
sent_types["% received"] = (sent_types["received"] / sent_types["no. PFDs"] * 100).round(1)

sent_counts = exploded.value_counts("sent_to")
sent_years = exploded.value_counts(["year", "status"]).unstack(fill_value=0)
type_counts = exploded.value_counts("status")


non_na.loc[:, "response status"] = "partial"
responses_from = lambda row: [sent for sent in row["sent_to"] if sent in row["escaped_urls"]]
with_responses = non_na.apply(responses_from, axis=1)
no_responses = (with_responses.str.len() == 0) & (non_na["replies"].str.len() == 0)
non_na.loc[no_responses, "response status"] = "overdue"
equal_len = (non_na["sent_to"].str.len() <= non_na["replies"].str.len()) & (non_na["sent_to"].str.len() > 0)
non_na.loc[equal_len, "response status"] = "completed"
all_responses = with_responses.str.len() >= non_na["sent_to"].str.len()
non_na.loc[all_responses, "response status"] = "completed"
non_na.loc[~report_due & (non_na["response status"] == "overdue"), "response status"] = "pending"
non_na.loc[~report_due & (non_na["response status"] == "partial"), "response status"] = "pending"
reports.loc[:, "response status"] = "failed"
reports.loc[non_na.index, "response status"] = non_na["response status"]
empty_requests = reports["this_report_is_being_sent_to"].isna()
reports.loc[empty_requests, "response status"] = "no requests"
reports.loc[:, "no. recipients"] = 0
reports.loc[non_na.index, "no. recipients"] = non_na["no. recipients"]

reports.loc[:, "no. replies"] = 0
reports.loc[non_na.index, "no. replies"] = non_na["no. replies"]


status_counts = reports.value_counts("response status")


without = len(reports) - len(fetched_non_na)
failed = len(fetched_non_na) - len(non_na)

monthly_toml_stats["this report is sent to"] = statistics = {
    "reports parsed": [float(len(non_na)), percent(len(non_na), len(reports))],
    "reports without recipients": [float(without), percent(without, len(reports))],
    "reports failed": [float(failed), percent(failed, len(reports))],
    "reports pending": [float(status_counts.get("pending", 0)),
                        percent(status_counts.get("pending", 0), len(reports))],
    "reports overdue": [float(status_counts["overdue"]),
                        percent(status_counts["overdue"], len(reports))],
    "reports partial": [float(status_counts.get('partial', 0)),
                        percent(status_counts.get("partial", 0), len(reports))],
    "reports completed": [float(status_counts.get("completed", 0)),
                          percent(status_counts.get("completed", 0), len(reports))],
}

monthly_toml_stats["requests for response"] = {
    "no. recipients with requests": len(sent_counts),
    "no. requests for response": len(exploded),
    "requests pending": [float(type_counts.get("pending", 0)),
                         percent(type_counts.get("pending", 0), len(exploded))],
    "requests received": [float(type_counts.get("received", 0)),
                          percent(type_counts.get("received", 0), len(exploded))],
    "requests overdue": [float(type_counts.get("overdue", 0)),
                         percent(type_counts.get("overdue", 0), len(exploded))],
    "mean no. requests per recipient": round(sent_counts.mean(), 1),
    "median no. requests per recipient": sent_counts.median(),
    "IQR of requests per recipients": list(sent_counts.quantile([0.25, 0.75])),
}
