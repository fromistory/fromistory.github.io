import json
from pathlib import Path
import jmespath

import twitter_utils as utils

# 220703 https://x.com/JGRfacts/status/1547499683706458113?s=20

def write_replies():
    posts = []

    index = 0

    date_mapping = dict()

    with open('invalid.txt', 'r') as file:
        ignored_auth = set(file.read().split())

    all_posts = utils.gather_all_posts_fast(skip_replies=True)
    for p in all_posts:
        date_mapping[p.post_id] = p.event_date

    for p in Path('json/replies').iterdir():
        # with open(p, 'r', encoding='utf-8') as f:
        #     json_data = json.load(f)
            # utils.make_post(d)

        posts += read_file(p, date_mapping, ignored_auth)
        index += 1
        # if index > 10:
        #     break

    out_path = Path('json/parsed/replies.json')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        as_dicts = [p.to_dict() for p in posts]
        json.dump(as_dicts, f, indent=2)
        # utils.gather_all_posts_fast()

        # for d in json_data:
        #     if d['content']['__typename'] != 'TimelineTimelineItem':
        #         continue
        #
        #     if legacy := jmespath.search('content.itemContent.tweet_results.result.legacy', d):
        #         print('Made post!')
        #         p = utils.make_post_from_legacy(legacy)
        #         posts.append(p)
        #     else:
        #         print('No legacy')
        #         print(d)
        # break
    # with open()
    # posts = utils.gather_all_posts_fast()

    # post_ids = set([p.post_id for p in posts])

    # reply_posts = [p for p in posts if p.replies > 0 and p.has_media() and p.reply_to not in post_ids]

    # for i, p in enumerate(reply_posts):
    #     # if p.replies > 0:
    #         # print(p.data)
    #         # print(p.link, )
    #     print(p.author)
    #     if p.author == 'Honeypow_jh':
    #         continue


    # print(len(reply_posts), '/', len(posts))

def write_tweets():
    posts = []

    index = 0

    date_mapping = dict()

    with open('invalid.txt', 'r') as file:
        ignored_auth = set(file.read().split())

    all_posts = utils.gather_all_posts_fast(skip_replies=True)
    for p in all_posts:
        date_mapping[p.post_id] = p.event_date

    for p in Path('json/tweets').iterdir():
        # with open(p, 'r', encoding='utf-8') as f:
        #     json_data = json.load(f)
            # utils.make_post(d)

        posts += make_posts(p, date_mapping, ignored_auth)
        # index += 1
        # if index > 10:
        #     break

    out_path = Path('json/parsed/tweets.json')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        as_dicts = [p.to_dict() for p in posts]
        json.dump(as_dicts, f, indent=2)


def make_posts(path, date_mapping, ignored_auth):
    with open(path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    results = get_results(json_data)
    posts = []
    event_date = None

    print(f'\nParsing {path}')

    for r in results:
        # print(r)
        if r['__typename'] != 'Tweet':
            continue

        p = utils.make_post_from_result(r, event_date)
        if not p:
            print('Failed to make post', r)
            continue

        if p.author in ignored_auth:
            continue

        # find the event date
        if not event_date:
            event_date = date_mapping.get(p.post_id)
            if not event_date:
                print('ERROR failed to find date for', p.post_id, p.link)
                print(p.to_dict())
                break

            p.event_date = event_date

        print('\tAdded tweet', p.post_id)
        # print(p.to_dict())
        posts.append(p)

    return posts

def read_file(path, date_mapping, ignored_auth):
    with open(path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    results = get_results(json_data)
    posts = []
    orig_auth = None

    posts = []
    event_date = None

    for r in results:
        # print(r)
        if r['__typename'] != 'Tweet':
            continue

        p = utils.make_post_from_result(r, event_date)
        if not p:
            continue

        # find the event date
        if not event_date:
            event_date = date_mapping.get(p.post_id)
            # if not event_date:
            #     print('ERROR failed to find date for', p.post_id, p.link)
            #     print(p.to_dict())
            if not event_date:
                break

            p.event_date = event_date

        if not orig_auth:
            # print('\nParsing chain', p.author, p.link)
            orig_auth = p.author

            if orig_auth in ignored_auth:
                print('Skip ignored auth', orig_auth)
                break
        else:
            if p.author != orig_auth:
                continue

        if not p.has_media():
            continue

        # print('Media reply', p.author, p.link)
        posts.append(p)

    if len(posts) > 1:
        print('\nFound chain', posts[0].link)
        for p in posts[1:]:
            print('Reply', p.link)

        return posts

    return []

def get_results(json_data):
    results = []
    # posts = []
    for d in json_data:
        if d['content']['__typename'] == 'TimelineTimelineItem':
            # print(d)
            # result = d['content']['itemContent']['tweet_results']['result']
            # results.append(result)
            if result := jmespath.search('content.itemContent.tweet_results.result', d):
                results.append(result)
            #     print('Made post!')
            #     p = utils.make_post_from_legacy(legacy)
            #     posts.append(p)
            # else:
            #     print('No legacy')
            #     print(d)

        elif d['content']['__typename'] == 'TimelineTimelineModule':
            items = d['content']['items']
            for i in [item['item']['itemContent'] for item in items]:
                if i['__typename'] == 'TimelineTweet':
                    if result := i.get('tweet_results', {}).get('result', {}):
                        results.append(result)
                    # if result['__typename'] == 'Tweet':
                    #     legacy = result['legacy']
                    #     print('Found legacy')
                    #     results.append(legacy)
                    # else:
                    #     print('Unknown result type?')
                    #     print(result)
                # else:
                #     print('What type is this?')
                #     print(i)
            continue
    return results

if __name__ == '__main__':
    # test_path = Path('json/tweets/1547499683706458113.json')
    # read_file(test_path)

    # write_replies()
    write_tweets()

    # post_ids = set()
    # out_posts = []
    # all_data = []
    #
    # with open('raw/posts.json', 'r', encoding='utf-8') as f:
    #     for d in json.load(f):
    #         post = utils.make_post(d)
    #         if post.post_id not in post_ids:
    #             post_ids.add(post.post_id)
    #         else:
    #             continue
    #         out_posts.append(post)
    #
    # dupes = 0
    #
    # with open('raw/tweets.json', 'r', encoding='utf-8') as f:
    #     data = json.load(f)
    #     total = len(data)
    #     for d in data:
    #         post = utils.make_post(d)
    #         if post.post_id not in post_ids:
    #             dupes += 1
    #             post_ids.add(post)
    #         else:
    #             print('FOUND DUPE', post.post_id, post.link)
    #             continue
    #         out_posts.append(post)
    # print(dupes, '/', total)
