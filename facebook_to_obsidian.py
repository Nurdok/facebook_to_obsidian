"""Convert a Facebook post export to Obsidian daily files.

Usage:
    facebook_to_obsidian <facebook_dir> <output_dir>
"""

import json
import textwrap

import docopt
import pathlib
import logging
import datetime
import pprint


class Post:
    def __init__(self, json_post):
        self._datetime = datetime.datetime.fromtimestamp(
            json_post['timestamp'])
        self._content = ""
        self._media_uris = []
        if 'attachments' in json_post:
            for attachment in json_post['attachments']:
                if 'data' not in attachment or not attachment['data']:
                    break
                for data in attachment['data']:
                    if 'media' in data:
                        assert data['media'] is not None and 'uri' in data['media']
                        uri = data['media']['uri']
                        assert uri is not None
                        self._media_uris.append(uri)
                    elif 'external_context' in data:
                        url = data['external_context']['url']
                        self._content += f"\n[External link]({url})"
        if 'data' in json_post and json_post['data'] and 'post' in json_post['data'][0]:
            self._content = json_post['data'][0]['post']

    def to_markdown(self):
        ret = "> [!facebook - post] Facebook Post"
        if self._content is not None:
            ret += f"\n> {self._content}"
        for media_uri in self._media_uris:
            ret += f"\n>![[{media_uri}]]"
        return ret

    def get_date(self):
        return self._datetime.date()

    def get_time(self):
        return self._datetime.time().strftime("%H:%M")


def facebook_to_obsidian(facebook_dir: pathlib.Path, output_dir: pathlib.Path):
    logging.info(f"Reading Facebook data from {facebook_dir}")
    logging.info(f"Writing output to {output_dir}")
    for post_path in facebook_dir.glob("your_posts_*.json"):
        with post_path.open('r') as post_file:
            json_posts = json.load(post_file)
        for json_post in json_posts[:-10]:
            try:
                post = Post(json_post)
            except:
                pprint.pprint(json_post)
                raise
            print(post.to_markdown())
            print(post.get_date())
            print(post.get_time())


def main():
    args = docopt.docopt(__doc__)
    facebook_dir = pathlib.Path(args['<facebook_dir>'])
    output_dir = pathlib.Path(args['<output_dir>'])
    facebook_to_obsidian(facebook_dir, output_dir)


if __name__ == '__main__':
    main()
