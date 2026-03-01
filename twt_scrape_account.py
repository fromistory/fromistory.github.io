import csv
import os
from io import StringIO

import requests
from selenium.webdriver.common.options import PageLoadStrategy

import json
import time

from selenium import webdriver
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.firefox import GeckoDriverManager

# --- Configuration ---
SEARCH_QUERY = "\"171129\" fromis_9"  # The text you want to search for

SCROLL_PAUSE_TIME = 2  # How long to wait for new content to load after scroll
MAX_CONSECUTIVE_SCROLLS_WITHOUT_NEW_MATCHES = 2  # Stop if N scrolls yield no new matching tweets
HEADLESS_MODE = False  # Run Chrome in headless mode (True) or with UI (False)

# --- Helper Functions ---
def setup_driver():
    """Sets up the Selenium WebDriver."""
    options = webdriver.FirefoxOptions()
    if HEADLESS_MODE:
        options.add_argument("--headless")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--window-size=1920,1080")
    # options.add_argument("--no-sandbox")
    # options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    profile_path = rf'{os.getenv("APPDATA")}\Mozilla\Firefox\Profiles\3uj5owbw.default-release'
    options.add_argument("-profile")
    options.add_argument(profile_path)
    service = FirefoxService(GeckoDriverManager().install())

    options.set_capability("pageLoadStrategy", PageLoadStrategy.eager)
    driver = webdriver.Firefox(service=service, options=options)

    return driver


def search_twitter(driver, query):
    """Navigates to the Twitter search results page."""
    # encoded_query = quote_plus(query)
    # search_url = f"https://twitter.com/search?q={encoded_query}&src=typed_query&f=live"  # f=live for latest tweets
    search_url = query
    print(f"Navigating to search URL: {search_url}")
    driver.get(search_url)

    # At the beginning of your script, after driver setup:
    with open("twitter_xhr_hook.js", "r") as f:
        xhr_hook_script = f.read()
    driver.execute_script(xhr_hook_script)

    if 'search?' in query:
        # Wait for tweets to appear (initial load)
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='tweet']")))
            print("Search results page loaded.")
            return True
        except Exception as e:
            print(
                f"Could not load search results or find initial tweets: {e}")  # driver.save_screenshot("search_load_error.png")
            return False
    else:
        print('Waiting for 10s')
        WebDriverWait(driver, 10)
        return True

def parse_search(driver, out_name, search):
    found_tweets = {}  # Use a dictionary with tweet ID as key to store unique tweets

    search_twitter(driver, search)

    time.sleep(SCROLL_PAUSE_TIME)  # Allow initial content to load

    driver.execute_script("return document.body.scrollHeight")
    time.sleep(SCROLL_PAUSE_TIME)

    with open("scroll.js", "r") as f:
        scroll_script = f.read()
    driver.execute_script(scroll_script)

    last_size = 0
    while True:
        finished = driver.execute_script("return window.scroll_finished")
        data = driver.execute_script("return window.interceptedTwitterData;")
        # print('Checking finished', finished, len(data))
        if finished:
            break

        # print(data)

        if last_size != len(data):
            print('NEW DATA', len(data))
            last_size = len(data)

        time.sleep(1)

    with open(f'json/accounts/{out_name}.json', 'w', encoding='utf-8') as out_file:
        data = driver.execute_script("return window.interceptedTwitterData;")
        json.dump(data, out_file, indent=2)

def get_tsv():
    url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRPT5wfb1Eh7r7RqGXJNtXeUhbAlokMvIiZdB6PdAQZoRb4JkwCy5Lw4XylvAwnsr7lmVbqPdPrVsMO/pub?gid=1556948653&single=true&output=tsv'
    response = requests.get(url)
    response.encoding = 'utf-8'
    tsv_data = response.text

    out = []

    reader = csv.reader(StringIO(tsv_data), delimiter='\t')

    headers = next(reader)
    for row in reader:
        elem = {}
        for i, h in enumerate(headers):
            elem[h] = row[i]
        # print(elem)
        out.append(elem)
    return out


member_dict = {
    'SR': '이새롬',
    'HY': '송하영',
    'GY': '장규리',
    'JW': '박지원',
    'JS': '노지선',
    'SY': '이서연',
    'CY': '이채영',
    'NG': '이나경',
    'JH': '백지헌'
}

def search_account(acc):
    driver = setup_driver()

    link = f'https://x.com/{acc}/media'
    parse_search(driver, acc, link)

    driver.quit()

# --- Main Script ---
if __name__ == "__main__":
    # search_account('byfromis_9')
    search_account('eoeowlgnlqks')
    # search_account('chaengmorning')
