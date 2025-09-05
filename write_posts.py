import time

import json

import twitter_utils as utils

def write_posts():
    # events_dict = utils.get_events_dict()
    posts = utils.gather_all_posts(['json', 'json2'])
    as_dicts = [p.to_dict() for p in posts]

    # for p in posts:
    with open('raw/posts.json', 'w', encoding='utf-8') as f:
        json.dump(as_dicts, f, indent=2)

if __name__ == '__main__':
    # write_posts()
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

    events_dict = utils.get_events_dict()
    start = time.time()  # record start time
    posts = utils.gather_posts([], events_dict)
    end = time.time()
    print(f'{len(posts)} Took: {end - start:.6f}s')