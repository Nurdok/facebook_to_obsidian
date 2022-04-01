"""Convert a Facebook post export to Obsidian daily files.

Usage:
    facebook_to_obsidian <facebook_dir> <output_note_dir> <output_media_dir>
"""
import collections
import datetime
import json
import logging
import pathlib
import pprint
from typing import List, Dict

import docopt


class Post:
    def __init__(self, json_post, media_prefix):
        self._json_post = json_post  # For debugging
        self._datetime = datetime.datetime.fromtimestamp(
            json_post['timestamp'])
        self._post_link = None
        self._content_lines = []
        self._media_uris = []
        if 'attachments' in json_post:
            for attachment in json_post['attachments']:
                if 'data' not in attachment or not attachment['data']:
                    break
                for data in attachment['data']:
                    if 'media' in data:
                        assert data['media'] is not None and 'uri' in data[
                            'media']
                        uri = data['media']['uri']
                        assert uri is not None
                        self._media_uris.append(
                            pathlib.PurePosixPath(media_prefix / uri))
                    elif 'external_context' in data:
                        url = data['external_context']['url']
                        if self._post_link:
                            raise RuntimeError("Unexpected link")
                        self._post_link = url
        if 'data' in json_post and json_post['data'] and 'post' in \
                json_post['data'][0]:
            # Facebook export encoding is broken:
            # https://stackoverflow.com/questions/50008296/facebook-json-badly-encoded
            # https://stackoverflow.com/questions/52457095/convert-unicode-escape-to-hebrew-text
            self._content_lines += json_post['data'][0]['post'].encode(
                'latin-1').decode('utf-8').split('\n')

    def to_markdown(self):
        lines = [self.get_callout_header(), *self._content_lines,
                 *self.get_embedded_media_lines()]
        lines = [f"> {line}" for line in lines]
        return '\n'.join(lines)

    def get_embedded_media_lines(self):
        return [f"![[{media_uri}]]" for media_uri in self._media_uris]

    def get_callout_header(self):
        title = "Facebook Post"
        title_ext = ""
        if self._post_link:
            title_ext = f": [External Link]({self._post_link})"
        return f"[!{self.callout_type()}] {title}{title_ext}"

    def is_rtl(self):
        return self.is_hebrew()

    def is_hebrew(self):
        return any(
            "\u0590" <= c <= "\u05EA" for c in ''.join(self._content_lines))

    def callout_type(self):
        return 'facebook' if not self.is_rtl() else 'facebook-rtl'

    def get_date(self):
        return self._datetime.date()

    def get_time(self):
        return self._datetime.time().strftime("%H:%M")


def facebook_to_obsidian(facebook_dir: pathlib.Path,
                         output_note_dir: pathlib.Path,
                         media_prefix: pathlib.PurePath):
    logging.info(f"Reading Facebook data from {facebook_dir}")
    logging.info(f"Writing notes to {output_note_dir}")
    logging.info(f"Assuming media is in {media_prefix}")
    posts: Dict[str, Post] = collections.defaultdict(lambda: [])
    for post_path in facebook_dir.glob("your_posts_*.json"):
        with post_path.open('r', encoding='utf8') as post_file:
            json_posts = json.load(post_file)
        for json_post in json_posts[:-10]:
            try:
                post = Post(json_post, media_prefix)
                posts[post.get_date()].append(post)
            except:
                pprint.pprint(json_post)
                raise

    for date, posts in posts.items():
        if '2020' not in date:
            continue
        daily_note = output_note_dir / f"{date}.md"
        print('Daily note: ' + daily_note)





def main():
    args = docopt.docopt(__doc__)
    facebook_dir = pathlib.Path(args['<facebook_dir>'])
    output_note_dir = pathlib.Path(args['<output_note_dir>'])
    output_media_dir = pathlib.Path(args['<output_media_dir>'])
    facebook_to_obsidian(facebook_dir, output_note_dir, output_media_dir)


if __name__ == '__main__':
    main()
