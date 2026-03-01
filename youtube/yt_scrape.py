import os.path
import random
import time

import json
import urllib.parse
from pathlib import Path
from seleniumwire import webdriver  # Keep selenium-wire for the driver
import pandas as pd

import settings

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000) # Adjusts the width of the display in characters
pd.set_option('display.max_colwidth', None) # Ensures full content of each column is displayed

# --- Configuration ---
DELAY_BETWEEN_SEARCHES = 120  # seconds
OUTPUT_FOLDER = Path("json/youtube")  # Use pathlib for robust path handling
REFRESH_DATA = False
LOG_ONLY = False

# HQ_CATEGORIES = ['Concert', 'Mini Fanmeeting', 'Fan Sign', 'Music Show', 'Festival']
# HQ_CATEGORIES = ['Mini Fanmeeting', 'Fan Sign']

CAT_SEARCH_TERMS = {
    # 'Fan Sign': ['사인'],
    # 'Mini Fanmeeting': ['팬미팅'],
}

EVENTS_PATH = Path('json/tables/events.tsv')

def get_dates_to_search():
    # out = []
    #
    # by_date = dict()
    # for r in get_tsv():
    #     by_date.setdefault(r['Date'])


    # print(tsv)
    if not EVENTS_PATH.exists() or REFRESH_DATA:
        EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRPT5wfb1Eh7r7RqGXJNtXeUhbAlokMvIiZdB6PdAQZoRb4JkwCy5Lw4XylvAwnsr7lmVbqPdPrVsMO/pub?gid=1556948653&single=true&output=tsv'
        df = pd.read_csv(url, sep='\t', header=0, encoding='utf-8')
        df.where(pd.notnull(df), '')
        df.to_csv(EVENTS_PATH, sep='\t', encoding='utf-8')
    else:
        df = pd.read_csv(EVENTS_PATH, sep='\t', header=0, encoding='utf-8')
        df = df.where(pd.notnull(df), '')

    # delete = []
    dates = []
    grouped = df.groupby('Date')
    for date, items in grouped:
        if int(date) > settings.DATE_CUTOFF:
            continue


        categories = set(items['Category'].to_list())
        # if 'Fan Sign' in categories and len(items) > 1:
        #     print(date)
        #     os.remove(f'json/{date}.json')

        if len(categories) == 1:
            type = next(iter(categories))
            if type in CAT_SEARCH_TERMS:
                type = CAT_SEARCH_TERMS[type][0]
            else:
                type = ''
        else:
            type = ''

        # if category_str != '':
        #     file_path = f'{date_str}.{category_str}'

        name = date
        if type != '':
            name = f'{name}.{type}'

        file_path = OUTPUT_FOLDER / f'{name}.json'
        if file_path.exists():
            continue

        dates.append((date, type))

    return dates
    # print(dates)
        #
        # if len(items) > 1:
        #
        #     rows = items.to_dict(orient='records')
        #     filtered = [r['Category'] for r in rows]
        #     if len(rows) != len(filtered):
        #         print(date)
        #
        #     # if len(items) != len(items.filter(lambda r: r['Category'] == 'Fan Sign')):
        #     #     print(date)
        #     # print(date, len(items), )
        #     # print()

    # valid_categories = ['Fan Sign']

    # def valid_group(group):
    #     if len(group) <= 1:
    #         return False
    #
    #     if group.name <= 250703:
    #         return False
    #
    #     if ~group['Category'].isin(valid_categories).any():
    #         return True
    #
    #     return False
    #     # Condition 1: Check the group's name (the date)
    #     # return group.name <= 250703 and group['Category'].isin(valid_categories).all()
    #
    # # grouped = df.groupby('Date').filter(valid_group)
    #
    # grouped_dict = {date: group_df.to_dict(orient='records') for date, group_df in df.groupby('Date')}
    #
    # for date, items in grouped_dict.items():
    #     print(date, items)
    # print(grouped_dict)

    # print(grouped.groupby('Date'))
    # for date, group in grouped.groupby('Date'):
    #     print(date, len(group))
    #     print(date, group.to_dict(orient='records'))
    # for g in grouped.groupby('Date').to_dict(orient='records'):
    #     print(g)


def save_data_to_file(data, date_str):
    """Saves the given data dictionary to a JSON file."""
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    file_path = OUTPUT_FOLDER / f"{date_str}.json"

    print(f"Saving data to: {file_path}")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_initial_search_data(driver, search_term, only_hq):
    """
    Navigates directly to a search results page and extracts the embedded
    ytInitialData JSON object.
    """
    # URL-encode the search term to handle spaces and special characters
    encoded_search_term = urllib.parse.quote_plus(search_term)
    url = f"https://www.youtube.com/results?search_query={encoded_search_term}"

    if only_hq:
        url += "&sp=CAMSAnAB"
    # else:
    #     url += "&sp=CAM%253D"

    print(f"\nNavigating to search results for: '{search_term}'")
    driver.get(url)

    # A short wait can help ensure the script variable is available
    time.sleep(5)

    try:
        # This is the core of the new strategy: execute JS to get the data
        # The data is already a Python dictionary after this call.
        data = driver.execute_script("return window.ytInitialData;")

        if data:
            print(f"Successfully extracted ytInitialData for '{search_term}'.")
            return data
        else:
            print(f"ytInitialData was found but was empty for '{search_term}'.")
            return None

    except Exception as e:
        print(f"An error occurred while executing script to get ytInitialData: {e}")
        return None


def run_batch_search(dates_to_process):
    """
    Main function to run the scraper for a given list of dates using the
    ytInitialData method.
    """
    # We still initialize the driver from seleniumwire as requested

    if not LOG_ONLY:
        driver = webdriver.Firefox()

    try:
        by_date = dict()
        for i, row in enumerate(dates_to_process):
            date_str, category_str = row

            file_name = date_str

            if category_str != '':
                file_name = f'{date_str}.{category_str}'

            file_path = OUTPUT_FOLDER / f'{file_name}.json'

            if file_path.exists():
                print('Skipping ', file_name)
                continue

            # only_hq = row['Category'] in HQ_CATEGORIES
            only_hq = False

            # additional_terms = CAT_SEARCH_TERMS.get(row['Category'], [])
            search_term = f'"{date_str}" {category_str} #fromis_9'
            print(search_term, file_path)

            if LOG_ONLY:
                continue

            search_data = get_initial_search_data(driver, search_term, only_hq)

            if search_data:
                save_data_to_file(search_data, file_name)

            if i < len(dates_to_process) - 1:
                delay = DELAY_BETWEEN_SEARCHES + random.randrange(0, 30)

                print(f"Waiting for {delay} seconds before next search...")
                time.sleep(delay)
    finally:
        print("\nBatch process finished. Closing the browser.")
        if not LOG_ONLY:
            driver.quit()


if __name__ == '__main__':
    # print(get_dates_to_search())z
    # # --- Choose which function to run ---
    #
    # # 1. To run the full batch process:
    # # Get the list of dates from our stub function

    main_dates_list = get_dates_to_search()
    print(len(main_dates_list))

    # by_cat = dict()
    # for d in main_dates_list:
    #     by_cat.setdefault(d['Category'], 0)
    #     by_cat[d['Category']] += 1
    #
    # for i, c in by_cat.items():
    #     print(i, c)


    # for m in main_dates_list:
    #     print(m)
    #
    run_batch_search(main_dates_list)
