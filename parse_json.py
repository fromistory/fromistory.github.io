import os
import random
import time

import json
from collections import defaultdict

import twitter_utils as utils
from twitter_utils import Post, gather_all_posts_fast

DOWNLOAD_IMAGES = True
DOWNLOAD_VIDEOS = False

# def main():
#     with open('json/events/180710.json', 'r', encoding='utf-8') as f:
#         data = json.load(f)
#
#     print(len(data))
#     for d in data:
#         if d['content']['__typename'] != 'TimelineTimelineItem':
#             # print(d)
#             continue
#
#         post = Post(d)
#         if len(post.media):
#             print(d)
#             print(post.post_id, post.link)
#
#         # print('\n')

def download_json():
    files = os.scandir('json/events')
    for file in files:
        if file.is_file():
            event_date = file.name.split('.')[0]
            with open(file.path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            out_dir = f'media/events/{event_date}'
            os.makedirs(out_dir, exist_ok=True)

            for d in json_data:
                if not utils.is_tweet(d):
                    continue

                post = Post(d)

                # if post.author == 'ondaia':
                #     print(d)
                #
                # if utils.is_retweet(d):
                #     print(d)
                #     continue

                # if post.author in ignored:
                #     continue

                if len(post.get_images()):
                    # print(d)
                    print(post.post_id, len(post.get_images()))
                    for i, img in enumerate(post.get_images()):
                        # image_id = img['id_str']
                        image_url = img['media_url_https']
                        image_ext = utils.get_img_ext(image_url)
                        image_url = image_url + f'?format={image_ext}&name=orig'
                        image_path = f'{out_dir}/{post.author}-{post.post_id}-{i}.{image_ext}'
                        print(i, image_url, image_path)

                        result = utils.download_file(image_url, image_path, post.date)
                        if result != 0:
                            time.sleep(random.randrange(5, 12))

def get_tweets(folder):
    out_dict = dict()
    files = os.scandir(folder)
    for file in files:
        if file.is_file():
            with open(file.path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            event_date = file.name.split('.')[0]

            for d in json_data:
                if utils.is_tweet(d):
                    # print(d)
                    post = Post(d)
                    post.event_date = event_date
                    out_dict[post.post_id] = post
    return out_dict

def log_authors():
    files = os.scandir('json')
    authors = dict()
    latest = dict()
    earliest = dict()
    for file in files:
        if file.is_file():
            event_date = file.name.split('.')[0]
            with open(file.path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            out_dir = f'media/events/{event_date}'
            os.makedirs(out_dir, exist_ok=True)

            for d in json_data:
                if utils.is_tweet(d):
                    # print(d)
                    post = Post(d)
                    if len(post.get_images()) > 0 or len(post.get_videos()) > 0:
                    # print(post.author)
                        authors.setdefault(post.author, 0)
                        authors[post.author] += 1

                        latest.setdefault(post.author, post.date)
                        if post.date > latest[post.author]:
                            latest[post.author] = post.date

                        earliest.setdefault(post.author, post.date)
                        if post.date < earliest[post.author]:
                            earliest[post.author] = post.date

    tuples = authors.items()

    new_tuples = sorted(tuples, key=lambda x: x[1])
    for name, count in new_tuples:
        print(f'{name}\t{count}\t{earliest[name].strftime("%Y-%m-%d")}\t{latest[name].strftime("%Y-%m-%d")}')

def log_authors2(posts):
    authors = dict()
    total_authors = dict()
    latest = dict()
    earliest = dict()

    for post in posts:
        total_authors.setdefault(post.author, 0)
        total_authors[post.author] += 1
        if len(post.get_images()) > 0 or len(post.get_videos()) > 0:
        # print(post.author)
            authors.setdefault(post.author, 0)
            authors[post.author] += 1

            latest.setdefault(post.author, post.date)
            if post.date > latest[post.author]:
                latest[post.author] = post.date

            earliest.setdefault(post.author, post.date)
            if post.date < earliest[post.author]:
                earliest[post.author] = post.date

    tuples = authors.items()

    new_tuples = sorted(tuples, key=lambda x: x[1])
    for name, count in new_tuples:
        print(f'{name}\t{count}\t{total_authors[name]}\t{earliest[name].strftime("%Y-%m-%d")}\t{latest[name].strftime("%Y-%m-%d")}')

def write_combined():
    tweets_1 = get_tweets('json')
    print(len(tweets_1))
    tweets_2 = get_tweets('json2')
    print(len(tweets_2))
    combined = tweets_2 | tweets_1
    d = [c.data for c in combined.values()]

    with open('combined.json', 'w', encoding='utf-8') as f:
        json.dump(d, f)

def get_posts() -> list[Post]:
    out = []
    with open('combined.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    for d in data:
        out.append(Post(d))
    return out

def log_downloaded_url(url, log_file="downloaded.txt"):
    with open(log_file, "a") as f:
        f.write(url + "\n")

def get_downloaded(log_file="downloaded.txt"):
    if not os.path.exists(log_file):
        return set()

    with open(log_file, "r") as f:
        return set(line.strip() for line in f)


def download_posts(posts, invalid_auth):
    """
    Groups posts by event_date, sorts them by newest, and downloads images
    while showing progress.
    """
    # --- 1. Load initial state ---
    downloaded_set = get_downloaded()
    failed_ids = get_failed_ids()

    # --- 2. Filter and Group Posts ---
    print("Filtering and grouping posts...")
    posts_by_date = defaultdict(list)
    for post in posts:
        # Apply initial filters
        if post.author in invalid_auth:
            continue
        # if post.event_date not in post.full_text:
        #     continue
        if not post.get_images():
            continue

        posts_by_date[post.event_date].append(post)

    # --- 3. Sort the Groups and Posts within them ---
    # Sort event dates from newest to oldest (e.g., 2023-10-27 before 2023-10-26)
    sorted_event_dates = sorted(posts_by_date.keys(), reverse=True)

    # Sort posts within each event date from newest to oldest
    for event_date in posts_by_date:
        # Assuming post.date is a comparable attribute (like a datetime object or ISO string)
        posts_by_date[event_date].sort(key=lambda p: p.date, reverse=True)

    images_to_download = []

    if DOWNLOAD_IMAGES:
        # --- 4. Pre-calculate total images to download for progress tracking ---
        print("Calculating remaining images to download...")
        for event_date in sorted_event_dates:
            for post in posts_by_date[event_date]:
                for i, img in enumerate(post.get_images()):
                    image_url = img['media_url_https']
                    image_ext = utils.get_img_ext(image_url)
                    final_image_url = f"{image_url}?format={image_ext}&name=orig"

                    if final_image_url not in downloaded_set and final_image_url not in failed_ids:
                        out_dir = f'media/events/{post.event_date}'
                        image_path = f'{out_dir}/{post.author}-{post.post_id}-{i}.{image_ext}'

                        if os.path.exists(image_path):
                            continue

                        # Add all necessary info to a queue
                        images_to_download.append({
                            'url': final_image_url,
                            'path': image_path,
                            'post_date': post.date,
                            'event_date': post.event_date,
                            'author': post.author,
                            'post_id': post.post_id,
                            'index': i
                        })

    if DOWNLOAD_VIDEOS:
        # VIDEOS
        print("Calculating remaining videos to download...")
        # images_to_download = []
        for event_date in sorted_event_dates:
            for post in posts_by_date[event_date]:
                for i, vid in enumerate(post.get_videos()):
                    print(vid)

                    if 'yout' in post.full_text:
                        print('Found youtube video preview', post.link)
                        continue

                    vid_url = utils.get_video_url(vid)

                    if vid_url and vid_url not in downloaded_set and vid_url not in failed_ids:
                        out_dir = f'media/events/{post.event_date}'
                        video_ext = utils.get_video_ext(vid_url)
                        vid_path = f'{out_dir}/{post.author}-{post.post_id}-{i}.{video_ext}'

                        if os.path.exists(vid_path):
                            continue

                        # Add all necessary info to a queue
                        images_to_download.append({
                            'url': vid_url,
                            'path': vid_path,
                            'post_date': post.date,
                            'event_date': post.event_date,
                            'author': post.author,
                            'post_id': post.post_id,
                            'index': i
                        })

    total_remaining = len(images_to_download)
    if total_remaining > 0:
        print(f"Found {total_remaining} new images to download.\n")

        log_test = dict()
        for item in images_to_download:
            log_test.setdefault(item['event_date'], 0)
            log_test[item['event_date']] += 1

        for item, val in log_test.items():
            print(item, ': ', val)

        # --- 5. Process the download queue ---
        for i, image_data in enumerate(images_to_download):
            current_count = i + 1
            image_url = image_data['url']
            image_path = image_data['path']
            out_dir = os.path.dirname(image_path)  # Get directory from the path

            # Create directory if it doesn't exist
            os.makedirs(out_dir, exist_ok=True)

            if os.path.exists(image_path):
                continue

            print(f"[{current_count}/{total_remaining}] Downloading image for post {image_data['post_id']}")
            print(f"  URL: {image_url}")
            print(f"  Path: {image_path}")
            # continue

            result = utils.download_file(image_url, image_path, image_data['post_date'])

            if result != -1:
                log_downloaded_url(image_url)
            else:
                print(f"  -> FAILED to download. Logging to failed.txt")
                with open('failed.txt', 'a', encoding='utf-8') as f:
                    f.write(
                        f"{image_data['event_date']}\t{image_data['author']}\t{image_data['post_id']}\t{image_data['index']}\t{image_url}\n")

            # Add a delay, especially if the download was fast or failed
            if i < total_remaining - 1:  # No need to sleep after the last one
                time.sleep(random.randrange(5, 12))

                # image_url = img['media_url_https']
                # image_ext = utils.get_img_ext(image_url)
                # final_image_url = f"{image_url}?format={image_ext}&name=orig"
                #
                # if final_image_url not in downloaded_set and final_image_url not in failed_ids:
                #     out_dir = f'media/events/{post.event_date}'
                #     image_path = f'{out_dir}/{post.author}-{post.post_id}-{i}.{image_ext}'
                #
                #     # Add all necessary info to a queue
                #     videos_to_dl.append({
                #         'url': final_image_url,
                #         'path': image_path,
                #         'post_date': post.date,
                #         'event_date': post.event_date,
                #         'author': post.author,
                #         'post_id': post.post_id,
                #         'index': i
                #     })

        # total_remaining = len(videos_to_dl)
        # if total_remaining > 0:
        #     print(f"Found {total_remaining} new images to download.\n")
        #
        #     # --- 5. Process the download queue ---
        #     for i, image_data in enumerate(videos_to_dl):
        #
        #         current_count = i + 1
        #         image_url = image_data['url']
        #         image_path = image_data['path']
        #         out_dir = os.path.dirname(image_path)  # Get directory from the path
        #
        #         # Create directory if it doesn't exist
        #         os.makedirs(out_dir, exist_ok=True)
        #
        #         print(f"[{current_count}/{total_remaining}] Downloading image for post {image_data['post_id']}")
        #         print(f"  URL: {image_url}")
        #         print(f"  Path: {image_path}")
        #
        #         result = utils.download_file(image_url, image_path, image_data['post_date'])
        #
        #         if result != -1:
        #             log_downloaded_url(image_url)
        #         else:
        #             print(f"  -> FAILED to download. Logging to failed.txt")
        #             with open('failed.txt', 'a', encoding='utf-8') as f:
        #                 f.write(
        #                     f"{image_data['event_date']}\t{image_data['author']}\t{image_data['post_id']}\t{image_data['index']}\t{image_url}\n")
        #
        #         # Add a delay, especially if the download was fast or failed
        #         if i < total_remaining - 1:  # No need to sleep after the last one
        #             time.sleep(random.randrange(5, 12))

def get_failed_ids():
    failed = set()
    with open('failed.txt', 'r', encoding='utf-8') as failed_file:
        failed_lines = failed_file.read().split('\n')
        for line in failed_lines:
            if line:
                rows = line.split('\t')
                print(rows)
                failed.add(rows[4])
    return failed
        # failed_file.split()


def main():
    invalid_auth = utils.get_invalid_authors()

    # download_json()
    # log_authors()
    # main()
    # write_combined()

    # posts = get_posts()
    # for p in posts:
    #     if p.author == 'PromisePollen':
    #         print(p.link, '\t', p.full_text)

    # tweets_1 = get_tweets('json')
    # print(len(tweets_1))
    # tweets_2 = get_tweets('json2')
    # print(len(tweets_2))
    # #
    # combined = tweets_2 | tweets_1
    # print(len(combined))
    #
    # posts = combined.values()
    # log_authors2(posts)

    posts = gather_all_posts_fast()

    download_posts(posts, invalid_auth)

if __name__ == '__main__':
    main()