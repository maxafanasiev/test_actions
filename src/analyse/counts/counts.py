# %% [markdown]
# ### Importing libraries
import os
import sys
import shutil
import time

sys.path.append(".")

time.sleep(1)
import sort_by_date as _

PATH = os.path.dirname(__file__)
C_REPORTS_PATH = os.path.abspath(f"{PATH}/../../data/reports-corrected.csv")
A_REPORTS_PATH = os.path.abspath(f"{PATH}/../../data/reports-analysed.csv")

shutil.copyfile(C_REPORTS_PATH, A_REPORTS_PATH)

# %% [markdown]
# ### Running the counts
import area_counts as _
import category_counts as _
import gender_counts as _
import name_counts as _
import sent_count_first as _
import sent_counts as _
import year_counts as _
