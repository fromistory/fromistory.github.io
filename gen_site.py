from pathlib import Path

import json
import os
import shutil
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from twitter_utils import *
import pandas as pd

# root_dir = 'json-test'

weird_types = set()

era_dates = [
    [250625, "From Our 20's"],
    [240812, 'Supersonic'],
    [230518, 'Unlock My World'],
    [220608, 'from our Memento Box'],
    [220103, 'Midnight Guest'],
    [210828, 'Talk & Talk'],
    [210507, '9 Way Ticket'],
    [200911, 'My Little Society'],
    [190522, 'Fun Factory'],
    [180930, 'From.9'],
    [180601, 'To. Day'],
    [180112, 'To. Heart'],
    [171130, 'Glass Shoes'],
    [170629, 'Idol School'],
    [0, 'Pre-Debut'],
]

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

gallery_index = 0


def make_image_md(url, caption='', zoom_click=True, figure=True):
    if caption:
        caption = f'<figcaption>{caption}</figcaption>'

    split = url.rsplit('.', maxsplit=1)
    base_url = split[0]
    ext = 'jpg'
    if len(split) > 1:
        ext = split[1]

    # if ext == 'png':
    #     print('Loading url', base_url, ext)

    low_res_url = base_url + '?format=jpg&name=medium'
    orig_url = base_url + f'?format={ext}&name=orig'

    return f'''
<a data-fancybox="gallery{gallery_index}" href="{orig_url}">
    <img src="{low_res_url}" alt="No Image" loading="lazy">
</a>
'''

#     return f'''
# ![]({orig_url}){{ loading=lazy data-gallery="gallery{gallery_index}" srcset="{low_res_url}" }}
# '''


def make_video_md(url, thumb_path, content_type):
#     return f"""
# <div class="video-wrapper">
# <a href="{url}" class="glightbox" data-gallery="gallery{gallery_index}">
#   <div class="video-thumb">
#   <img src="{thumb_path}" alt="Missing Thumbnail" class="skip-lightbox video-thumb" loading="lazy"/>
#   </div>
# </a>
# </div>
# """

#     return f"""
# <div class="video-wrapper">
#     <video
#         controls="controls"
#         preload="none"
#         poster="{thumb_path}"
#         referrerpolicy="same-origin"
#         src="{url}">
#     </video>
# </div>
# """

    return f"""
<div class="video-wrapper" markdown="1">
<video controls="controls" preload="none" poster="{thumb_path}" referrerpolicy="same-origin">
<source src="{url}" type="{content_type}">
</video>
</div>
"""


def make_media_md(post):
    elems = []

    for img in post.get_images():
        image_url = img['media_url_https']
        elems.append(make_image_md(image_url))

    # if len(post.get_videos()) > 1:
    #     print('FOUND MULTI VID')
    #     print(post.event_date)
    #     print(post.author)

    for vid in post.get_videos():
        if video_url := get_video_url(vid):
            elems.append(make_video_md(video_url, vid['media_url_https'], 'video/mp4'))
        else:
            elems.append(vid['media_url_https'])


    # print('Generating media for', data)
    # if media := get_media(data):
    #     for m in media:
    #         image_url = m['media_url_https']
    #         # if not image_url.endswith('.jpg'):
    #         #     breakpoint()
    #
    #         if video_url := get_video_url(data):
    #             print('\tMake video', video_url)
    #             elems.append(make_video_md(video_url, image_url, 'video/mp4'))
    #         # if video_info := m.get('video_info'):
    #         #     varients = video_info['variants']
    #         #     # for v in varients:
    #         #     #     if v['content_type'] == 'video/mp4':
    #         #     #         # video_url = v['url']
    #
    #         else:
    #             print('\tMake img', image_url)
    #             elems.append(make_image_md(image_url))

    grid = '<div class="grid" markdown="1">\n'
    grid += '\n'.join([f'<div class="grid-item glightbox" markdown="1">{e}</div>' for e in elems])
    grid += '\n</div>'

    # grid += '\n'.join(f'  <div>{e}</div>' for e in elems)
    # grid += '\n'.join(f'  <div>{e}</div>' for e in elems)
    # grid += '\n</div>'
    return grid

    # return '\n'.join(elems)


def make_post_md(post: Post):
    # tags = get_tags(post.data)
    # tags_md = '\n'.join(['  - ' + t.removeprefix('#') for t in tags])

    copy_button = f"""
<button class="copy-link-button tooltip" data-copy-link="{post.link}">
<span class="md-icon">:octicons-share-24:{{.big-emoji}}</span>
<span class="tooltiptext">Copied to clipboard</span>
</button>
"""

    post_link = f"""
<div class="post-link" style="text-align: right;" markdown="1">
<a href="{post.link}" target="_blank" rel="noopener noreferrer">:material-twitter:{{.big-emoji}}</a>
</div>
"""

    post_text_and_link = f"""
<div class="post-text-container" markdown="1">
{post.full_text}
</div>
"""

    post_media = f"""
<div class="post-media-container" markdown="1">
{make_media_md(post)}
</div>
"""


    out = f"""
<div class="post-container" markdown="1">
<div class="content-container" markdown="1">
{post_text_and_link}
{post_media}
</div>
<div class="post-footer" markdown="1">
<div class="footer-buttons" markdown="1">
{copy_button}
{post_link}
</div>
</div>
</div>
"""

    return out

def make_youtube_md(url):
    embed_url = url.replace('watch?v=', 'embed/')
    return f"""
<div class="youtube-wrapper" markdown="1">
<iframe 
    src="{embed_url}"
    referrerpolicy="strict-origin-when-cross-origin"
    frameborder="0"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"
    allowfullscreen>
</iframe>
</div>
"""

# TODO actually embed the tweet
def make_tweet_md(url):
    return f'<a href="{url}">{url}</a>'

def make_yt_events_md(data):
    mds = []
    data = sorted(data, key=lambda x: x['author'])
    for d in data:
        yt_md = make_youtube_md(f'https://www.youtube.com/watch?v={d['id']}')
        mds.append(f'\n{yt_md}\n')

    # if len(data) > 1:
    return f'''
<div class="author-container" markdown="1">
## YouTube
<div class="grid" markdown="1">
\n{'\n'.join(mds)}
</div>
</div>'''

    # return '\n'.join(mds)


def make_event(event_date, posts: list[Post], events_dict, yt_data):
    # filter the posts
    authors = set([p.author for p in posts])
    def is_valid_post(p):
        for a in authors:
            if a == p.author:
                continue

            if a == 'realfromis_9':
                continue

            if a in p.full_text:
                # print('Skipping retweet', event_date, p.author, a)
                # print(p.full_text, '\n')
                return False

        # print(p.event_date)
        # if int(p.event_date) != 231013:
        #     return False

        return True

    posts = [p for p in posts if is_valid_post(p)]

    if len(posts) == 0:
        print('ERROR', event_date, 'has no posts')
    #     return

    eng_date_name, kor_date_name = get_date_name(event_date, events_dict)

    events = events_dict[event_date]
    out = f"""---
slug: \"{event_date}\"
date: {datetime.strptime(event_date, "%y%m%d")}
hide:
  - navigation
---

# {event_date} {eng_date_name}
"""

    has_alt = False
    for e in events:
        event_name = e['Eng Name']
        if kor := e.get('Kor Name'):
            event_name += f' ({kor})'
        out += f'**{event_name}**\n\n'

        twi_search = e['Twitter']
        if members := e.get('Member'):
            kr_members = [member_dict[m.strip()] for m in members.split(',')]
            if len(kr_members) == 1:
                twi_search = f'https://x.com/search?q="{event_date}"%20OR%20"{event_date}"%20%23{kr_members[0]}'

        if alt := e.get('Alt 1'):
            print('Found alt?', alt)
            if 'x.com/search' in alt:
                twi_search = alt
            elif 'x.com' in alt:
                out += f'* {make_tweet_md(alt)}\n'
                has_alt = True

        if alt := e.get('Alt 2'):
            if 'x.com' in alt:
                out += f'* {make_tweet_md(alt)}\n'

        if has_alt:
            continue

        out += f'* [Twitter search]({twi_search}) | [YouTube search]({e['YouTube']})\n'

        cams = []

        cams = [e.get('Cam 1'), e.get('Cam 2')]
        for cam_text in cams:
            if cam_text:
                cam_urls = cam_text.split('\n')
                for url in cam_urls:
                    out += '<div class="grid" markdown="1">'
                    out += make_youtube_md(url) + '\n'
                    out += '</div>'
        # if cam_1 or cam_2:
        #     out += '<div class="grid" markdown="1">'
        #     if cam_1:
        #         out += make_youtube_md(cam_1) + '\n'
        #
        #     if cam_2:
        #         out += make_youtube_md(cam_2) + '\n'
        #     out += '</div>'

        out += '\n---\n\n'
        # out += f'# {e['Eng Name']}'
        # print(e)

    by_author = dict()
    for p in posts:
        if "open.kakao.com" in p.full_text:
            continue

        by_author.setdefault(p.author, [])
        by_author[p.author].append(p)

    # by_author = dict(sorted(by_author.items(), key=lambda item: len(item[1]), reverse=True))
    by_author = dict(sorted(by_author.items(), key=lambda item: item[0].lower(), reverse=False))


    if not has_alt:
        # embed yt vids
        yt_vids = yt_data.get(event_date, None)
        if yt_vids:
            out += make_yt_events_md(yt_vids)
            # out += '\n---\n'

        first_auth = True
        for auth, ps in by_author.items():
            ps = [p for p in ps if p.has_media()]

            if len(ps):
                if not first_auth:
                    out += '\n</div>\n\n'
                first_auth = False

                out += f'<div class="author-container" markdown="1">\n'
                out += f'## {auth}\n'

                if ps:
                    out += '\n---\n'

                for p in ps:
                    if len(p.get_images()) == 0 and len(p.get_videos()) == 0:
                        continue

                    # if len(p.get_images()) > 0 and len(p.get_videos()) > 0:
                    #     print('FOUND MULTI', p.author, p.event_date)

                    post_md = make_post_md(p)
                    out += post_md
                    out += '\n---\n'

                global gallery_index
                gallery_index += 1

    dir = f'docs/events'
    os.makedirs(dir, exist_ok=True)
    out_path = f'{dir}/{event_date}.md'

    with open(out_path, 'w', encoding='utf-8') as txt:
        txt.writelines(out)

def make_index(events, events_dict):
    sorted_events = sorted(events)

    # 1. Start with the table header
    out = f"""---
hide:
  - navigation
search:
  exclude: true
---

# Events\n\n
"""

    current_era = None

    for e in sorted_events:
        event_date = int(e)
        event_era = None

        for date, era in era_dates:
            if event_date >= date:
                event_era = era
                break
        print(e, event_era, event_date)

        if current_era is not event_era:
            if current_era:
                out += '\n\n'

            current_era = event_era

            out += f"## {event_era}\n\n"

            # out += '<div class="center-table">'
            out += "| Thumbnail | Date |  \n"
            out += "|:---:|:---|\n"  # Defines alignment (center for thumb, left for text)


        # Assumes your script runs from the project root, and 'docs' is a subfolder
        thumb_path_for_mkdocs = f'/assets/thumb/{e}.jpg'
        thumb_path_on_disk = f'docs/{thumb_path_for_mkdocs}'

        if not os.path.exists(thumb_path_on_disk):
            print(f'ERROR: No thumbnail found for {thumb_path_on_disk}')
            print(Path(f"./media/events/{e}").absolute().as_uri())
            print(f'http://localhost:8000/events/{e}')
            # print(test.as_uri())

            # You might want to use a placeholder image here
            image_html = '*(No Thumbnail)*'
        else:
            # 2. Use an HTML img tag to control the height
            # image_html = f'<img src="../{thumb_path_for_mkdocs}" alt="Thumbnail for {e}" style="height: 100px;">'
            image_html = f'![*(No Thumbnail)*]({thumb_path_for_mkdocs}){{ width="128" loading=lazy }}'

        # 3. Create the text part with the link
        eng_date_name, kor_date_name = get_date_name(e, events_dict)
        # link_markdown = f"[**{e}** {eng_date_name}](./{e}){{ loading=lazy }}"
        link_markdown = f"[**{e}**<br>{eng_date_name}<br>{kor_date_name}](./{e})"

        # 4. Add a new row to the table for this event
        out += f"| {image_html} | {link_markdown} |\n"

    with open('docs/events/index.md', 'w', encoding='utf-8') as txt:
        txt.writelines(out)

def get_date_name(date, events_dict):
    if events := events_dict.get(date):
        eng_names = []
        kor_names = []
        for e in events:
            eng = e['Eng Name']
            eng_names.append(eng)
            if kor := e.get('Kor Name'):
                kor_names.append(kor)
            else:
                kor_names.append(eng)

        return ' & '.join(eng_names), ' & '.join(kor_names)
    else:
        print('ERROR failed to find event name for', date)
        return 'Unknown Event', 'Unknown Event'

def get_yt_events():
    with open('json/parsed/youtube_events.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data

    # def is_valid_yt(r):
    #     title = r['title']
    #     # names = ['fromis', '프로미스나인', '프나', '프미나']
    #     banned_terms = ['치어리더', '버스킹']
    #
    #     ignored_authors = ['ThePingiiz', 'parrotsubs', 'papago_9']
    #     if r['author'].lower() in ignored_authors:
    #         return False
    #
    #     if r['length'] < 20:
    #         return False
    #
    #     for b in banned_terms:
    #         if b in title:
    #             print(f'Skipping yt video {b}', f'https://www.youtube.com/watch?v={r['id']}, {title}')
    #             return False
    #
    #     # for n in names:
    #     #     if n in title:
    #     #         return True
    #
    #     return True
    #
    # return {k: [x for x in arr if is_valid_yt(x)] for k, arr in data.items()}

def main():
    yt_data = get_yt_events()
    events_dict = get_events_dict()

    # these are folders!
    # posts_by_event = gather_posts_by_event(['json-test'], events_dict, slow=True)
    posts_by_event = gather_posts_by_event(['json2', 'json'], events_dict)

    print(f'Generating {len(posts_by_event)} events')

    if os.path.exists('docs/events'):
        shutil.rmtree('docs/events')
    os.makedirs('docs/events')

    make_index(posts_by_event.keys(), events_dict)

    for event, posts in posts_by_event.items():
        make_event(event, posts, events_dict, yt_data)

if __name__ == '__main__':
    main()

    # json_data, all_posts = gather_json_data(root_dir)
    # download_all_media(all_posts)
