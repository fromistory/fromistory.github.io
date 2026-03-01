import os

import json

import twitter_utils as utils
from twitter_utils import Post, get_authors, gather_all_posts_fast


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
    auth_dict = dict()

    curr_data = get_authors()
    for data in curr_data:
        auth_dict[data['Name']] = data
    # for a, d in auth_dict.items():
    #     print(a, d)
    #
    # return

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

    new_tuples = sorted(tuples, key=lambda x: x[1], reverse=True)

    rows = []
    for name, count in new_tuples:
        if count >= 5:
            download = ''
            deleted = ''

            if d := auth_dict.get(name):
                download = d.get('Download', '')
                deleted = d.get('Deleted', '')

            row = f'{name}\t{count}\t{total_authors[name]}\t{earliest[name].strftime("%Y-%m-%d")}\t{latest[name].strftime("%Y-%m-%d")}\t{download}\t{deleted}'
            print(row)
            rows.append(row)

    with open('authors.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(rows))


if __name__ == '__main__':
    # tweets_1 = get_tweets('json')
    # print(len(tweets_1))
    # tweets_2 = get_tweets('json2')
    # print(len(tweets_2))
    # #
    # combined = tweets_2 | tweets_1
    # print(len(combined))
    #
    # posts = combined.values()
    posts = gather_all_posts_fast()
    log_authors2(posts)