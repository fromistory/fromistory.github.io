import time
from pathlib import Path

import json

import twitter_utils as utils

def write_posts():
    # posts = utils.gather_all_posts(['json-test'])
    # events_dict = utils.get_events_dict()
    posts = utils.gather_all_posts(['json/events', 'json2'])
    # posts = utils.gather_all_posts_fast()
    # posts: list[utils.Post] = utils.gather_all_posts(['json-test'])

    as_dicts = []
    invalid_auth = utils.get_invalid_authors()

    for post in posts:
        # Apply initial filters
        if post.author in invalid_auth:
            continue
        if post.event_date not in post.full_text:
            continue
        if not post.has_media():
            continue

        as_dicts.append(post.to_dict())

    # as_dicts = [p.to_dict() for p in posts]

    # dates = set()
    # for p in posts:
    #     formatted = p.date.strftime("%y%m%d")
    #     # print(formatted)
    #     if formatted == "241029":
    #         print(p.to_dict())

        # if p.date.year == 2024 and p.date.month == 10 and p.date.day == 29:
        #     print(p)
        # if p.date == "241029":
        # dates.add(p.date)


    # for p in posts:
        # if int(p.post_id) != 1714279047067546099:
        #     continue

        # print(p.data)

        # if utils.get_legacy(p.data)['reply_count']:
        #     print(p.link, utils.get_legacy(p.data)['reply_count'], p.post_id)
        # print(p.data)

    # for p in posts:
    out_path = Path('json/parsed/posts.json')
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(as_dicts, f, indent=2)

if __name__ == '__main__':
    write_posts()
    # start = time.time()  # record start time
    # posts = utils.gather_all_posts_fast()
    # end = time.time()
    # print(f'{len(posts)} Took: {end - start:.6f}s')
    #
    # start = time.time()  # record start time
    # posts = utils.gather_all_posts(['json', 'json2'])
    # end = time.time()
    # print(f'{len(posts)} Took: {end - start:.6f}s')

    # for p in posts:
    #     print()

    # events_dict = utils.get_events_dict()
    # start = time.time()  # record start time
    # posts = utils.gather_posts([], events_dict)
    # end = time.time()
    # print(f'{len(posts)} Took: {end - start:.6f}s')