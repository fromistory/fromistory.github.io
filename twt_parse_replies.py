from pathlib import Path

import twitter_utils as utils
from twitter_utils import Post
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

import jmespath

# 220703 https://x.com/JGRfacts/status/1547499683706458113?s=20

# --- Configuration ---
SEARCH_QUERY = "\"171129\" fromis_9"  # The text you want to search for

SCROLL_PAUSE_TIME = 2  # How long to wait for new content to load after scroll
MAX_CONSECUTIVE_SCROLLS_WITHOUT_NEW_MATCHES = 2  # Stop if N scrolls yield no new matching tweets
HEADLESS_MODE = False  # Run Chrome in headless mode (True) or with UI (False)


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
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='tweet']")))
            print("Search results page loaded.")
            return True
        except Exception as e:
            print(
                f"Could not load search results or find initial tweets: {e}")  # driver.save_screenshot("search_load_error.png")
            return False
    else:
        # print('Waiting for 10s')
        WebDriverWait(driver, 10)
        return True

def is_deleted_account(data):
    typename = jmespath.search("content.itemContent.tweet_results.result.__typename", data)
    # text = jmespath.search(
    #     "content.itemContent.tweet_results.result.tombstone.text.text",
    #     data
    # )

    return typename == "TweetTombstone"

    # return (typename == "TweetTombstone"
    #     # and isinstance(text, str)
    #     # and "account that no longer exists" in text
    # )

def is_deleted_tweet(entry: dict) -> bool:
    # for d in data:
    #     if d.get('type') == 'TimelineAddEntries':
    #         for entry in d.get('entries', []):
    #             print(entry)
    #             entry
    tr = entry.get("content", {}) \
             .get("itemContent", {}) \
             .get("tweet_results", {})
    return "result" not in tr

def parse_tweet(driver, folder, out_name, search):
    out_path = Path(f'{folder}/{out_name}.json')
    if out_path.exists():
        return True

    print('Parsing tweet', search, out_path)

    search_twitter(driver, search)

    time.sleep(SCROLL_PAUSE_TIME)  # Allow initial content to load
    driver.execute_script("return document.body.scrollHeight")
    time.sleep(SCROLL_PAUSE_TIME)

    with open("scroll_fast.js", "r") as f:
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
            # print('NEW DATA', len(data))
            last_size = len(data)

        time.sleep(1)

    data = driver.execute_script("return window.interceptedTwitterData;")
    if len(data) == 0:
        return False

    is_deleted = is_deleted_account(data[0])

    # is_deleted_twt = is_deleted_tweet(data)

    # x = '\n'.join([json.dumps(d) for d in data])
    # print(x)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as out_file:
        # byte_size = len(x.encode('utf-8'))
        # if not is_deleted and byte_size < 3 * 1024:
        #     print('Got very small data (probably rate limited!')
        #     print(data)
        #     return False
        print(data)
        json.dump(data, out_file, indent=2)
        print('Wrote to', out_path)

    return True


def scrape_replies():
    driver = setup_driver()

    posts = utils.gather_all_posts_fast(skip_replies=True)

    # parse_tweet(driver, '1547499683706458113', 'https://x.com/JGRfacts/status/1547499683706458113')
    post_ids = set([p.post_id for p in posts])

    # reply_posts = [p for p in posts if p.replies > 0 and p.has_media() and p.reply_to not in post_ids]

    with open('invalid.txt', 'r') as file:
        ignored_auth = set(file.read().split())

    deleted_auth = ['jwwithyou', 'Honeypow_jh']

    def is_valid_post(p):
        if p.replies == 0:
            return False

        if not p.has_media():
            return False

        if p.reply_to in post_ids:
            return False

        if p.author in ignored_auth:
            return False

        if p.author in deleted_auth:
            return False

        out_path = Path(f'json/replies/{p.post_id}.json')
        if out_path.exists():
            return False

        return True

    reply_posts = [p for p in posts if is_valid_post(p)]

    for i, p in enumerate(reply_posts):
        print('Parsing', i, '/', len(reply_posts))
        if not parse_tweet(driver, 'json/replies', p.post_id, p.link):
            breakpoint()
            break
        # time.sleep(10)
            # print('Failed to read')
            # break

        # if i > 5:
        #     break

    driver.quit()

    # print(len(reply_posts), '/', len(posts))

def scrape_by_author(auth):
    driver = setup_driver()

    posts = [p for p in utils.gather_all_posts_fast(True) if p.author == auth]
    for i, p in enumerate(posts):
        print('Parsing', i, '/', len(posts), p.link)
        # curr_path = Path(f'json/replies/{p.post_id}.json')
        # desired_path = Path(f'json/tweets/{p.post_id}.json')
        # if curr_path.exists():
            # print('Rename', curr_path, desired_path)
            # curr_path.rename(desired_path)
        parse_tweet(driver, 'json/tweets', p.post_id, p.link)

    driver.quit()


if __name__ == '__main__':
    # scrape_by_author('Naz_981123')
    scrape_by_author('Syonderella122')
    # scrape_replies()

