import json
import os

import pandas as pd
import re

PATH = os.path.dirname(__file__)
DATA_PATH = os.path.abspath(f"{PATH}/data")
REPORTS_PATH = os.path.abspath(f"{PATH}/../../data")
CORRECT_PATH = os.path.abspath(f"{PATH}/../../correct")


def find_matches(_input_string, _pattern):
    if _input_string:
        _input_string = _input_string.strip('| ')
        matches = re.finditer(_pattern, _input_string)
        list_of_match = [match.group() for match in matches if match.group()]
        cleaned_values = [value.replace(r'\ ', ' ') for value in list_of_match]
        a = ' | '.join(cleaned_values)
        cleaned_string = a.strip('| ')
        return cleaned_string
    return None


def get_pattern(file):
    dictionary = get_replacements(file)
    return '|'.join(re.escape(key) for key in dictionary.values())


def process_csv(file, _pattern):
    df = pd.read_csv(file)
    df['this_report_is_being_sent_to'] = (df['this_report_is_being_sent_to']
                                          .apply(lambda x: find_matches(str(x), _pattern)))
    df.to_csv(file, index=False)
    print("Done...")


def replace_in_csv(file, _replacements):
    df = pd.read_csv(file)
    df['this_report_is_being_sent_to'] = (df['this_report_is_being_sent_to']
                                          .apply(lambda x: replace_elements(str(x), _replacements)))
    df.to_csv(file, index=False)
    print("Replace done...")


def replace_elements(input_string, _replacements):
    if input_string:
        elements = input_string.split('|')
        return ' | '.join([_replacements.get(element.strip(), element.strip()) for element in elements])
    return ''


def get_replacements(file):
    with open(file, 'r') as f:
        dictionary_json = f.read()
    list_of_dicts = json.loads(dictionary_json)
    return {k: v for d in list_of_dicts for k, v in d.items()}


replacements = get_replacements(os.path.abspath(f"{CORRECT_PATH}/manual_replace/destinations.json"))

input_csv = os.path.abspath(f"{REPORTS_PATH}/reports-corrected.csv")

pattern = get_pattern(os.path.abspath(f"{CORRECT_PATH}/manual_replace/destinations.json"))

process_csv(input_csv, pattern)

replace_in_csv(input_csv, replacements)
