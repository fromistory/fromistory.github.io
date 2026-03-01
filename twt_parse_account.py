from datetime import datetime
from pathlib import Path

import json
import twitter_utils as utils
import jmespath

from twitter_utils import edit_creation_date


def search_account(acc):
    out_dir = Path(f'media/accounts/{acc}')
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(f'json/accounts/{acc}.json') as f:
        data = json.load(f)
        for d in data:
            print(d)
            legacy = jmespath.search('item.itemContent.tweet_results.result.legacy', d)
            print(legacy)
            if not legacy:
                print('SKIPPING UNKNOWN TYPE')
                continue
            post = utils.make_post(legacy)
            print(post.date)
            # print(post.get_images())

            for i, img in enumerate(post.get_images()):
                # image_id = img['id_str']
                image_url = img['media_url_https']
                image_ext = utils.get_img_ext(image_url)
                image_url = image_url + f'?format={image_ext}&name=orig'
                image_path = f'{out_dir}/{post.date.strftime("%y%m%d")}-{acc}-{post.post_id}-{i}.{image_ext}'
                # print(i, image_url, image_path)
                utils.download_file(image_url, image_path, post.date)

            # break


# --- Main Script ---
if __name__ == "__main__":
    search_account('eoeowlgnlqks')
    # search_account('chaengmorning')
