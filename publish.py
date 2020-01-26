#!/usr/bin/env python
import re
from glob import glob
import traceback
from praw import Reddit
from praw.exceptions import PRAWException
from prawcore.exceptions import PrawcoreException, TooLarge
import argparse
import sys
import os
from pathlib import Path

PROGRAM = "Reddit Stylesheet Updater"
VERSION = "1.3.0"
MAX_EDIT_REASON_LENGTH = 256
IMAGE_SUFFIXES = ['.jpg', '.jpeg', '.png']

TRUE_VALUE = ["true", "yes", "1", "y", "t"]

class Actions:
    @staticmethod
    def error(s):
        print("::error ::%s" % s)

    @staticmethod
    def add_mask(s):
        print("::add-mask::%s" % s)

    @staticmethod
    def warning(s):
        print("::warning ::%s" % s)


class StyleSheetUpdater:

    def __init__(self, ua):
        self.ua = ua

    def main(self):
        argparser = argparse.ArgumentParser('Publish reddit stylesheet')
        argparser.add_argument("-c", "--clear", action='store_true', help="Clear subreddit styles and images before uploading (rarely necessary)")
        argparser.add_argument("-n", "--skip-images", action='store_true', help="Skip uploading images")
        argparser.add_argument("-s", "--cleanup", action='store_true', help="Remove unused images before and after publishing")
        argparser.add_argument("subreddit", help="Subreddit to upload to")
        argparser.add_argument("dir", help="Dir to push files from")
        self.args = argparser.parse_args()

        self._read_env_options()

        sr_name = self.args.subreddit
        input_dir = Path(self.args.dir)
        if not input_dir.exists():
            Actions.error("Input dir %s does not exist" % input_dir)
            sys.exit(1)
        if not input_dir.is_dir():
            Actions.error("Input dir %s is not a dir" % input_dir)
            sys.exit(2)

        self.r = Reddit(user_agent=self.ua)
        self.subreddit = self.r.subreddit(sr_name)

        if self.args.clear:
            self.clear()

        # We do a cleanup before to lower the risk of being unable to upload 
        if self.args.cleanup:
            self.remove_unused_images()
        stylesheet = None
        for fn in input_dir.glob('**/*'):
            if not fn.is_file():
                continue
            suf = fn.suffix.lower()
            if suf == '.css':
                print("Stylesheet: %s" % fn)
                stylesheet = open(fn, 'r', encoding='UTF-8')
            elif suf in IMAGE_SUFFIXES:
                if self.args.skip_images:
                    print("Not uploading image %s" % fn)
                    continue
                try:
                    self.upload_file(fn)
                except TooLarge as e:
                    Actions.error("Image %s too large (%d bytes)" % (fn, fn.stat().st_size))
                    raise e
                except PRAWException as e:
                    # Treating this as a warning since it might already be there
                    Actions.warning("Failed uploading %s (%s)" % (fn, e))
                    traceback.print_exc()
                except PRAWCoreException as e:
                    Actions.error("Could not upload %s - %s" % (fn, e))
                    raise e
            else:
                print("Skipping file %s" % fn)
        # Need to do this last, or the images wouldn't be there
        if stylesheet:
            self.put_stylesheet(stylesheet.read())
        # Cleanup now-orphaned images
        if self.args.cleanup:
            self.remove_unused_images()

    def put_stylesheet(self, styles):
        reason = 'Automatic update to {shorthash} by {author}'.format(
                shorthash=os.environ['GITHUB_SHA'][0:8],
                author=os.environ['GITHUB_ACTOR'],
                ref=os.environ['GITHUB_REF'])
        print("Put stylesheet to %s:\n-------------------------------------------------\n%s\n-------------------------------------------------" % (self.subreddit.display_name, styles))
        reason = reason[:MAX_EDIT_REASON_LENGTH]
        try:
            r = self.subreddit.stylesheet.update(styles, reason=reason)
            if r is not None:
                Actions.warn("Unexpected return updating style: %r" % r)
        except PRAWException as e:
            Actions.error("Error updating style: %s" % e)
            self.check_images(styles)
            raise e

    def remove_unused_images(self):
        available = self._available_images()
        used = self._used_images(self.subreddit.stylesheet().stylesheet)
        unused = available - used
        for i in unused:
            print("Removing unused image %s" % i)
            self.subreddit.stylesheet.delete_image(i)

    def check_images(self, styles):
        available = self._available_images()
        used = self._used_images(styles)
        missing = used - available
        for i in missing:
            Actions.error("Missing image: %s" % i)

    def _available_images(self):
        return set([i['name'] for i in self.subreddit.stylesheet().images])

    def _used_images(self, styles):
        return set(re.findall(r'%%([^%]*)%%', styles))

    def upload_file(self, fn):
        print("Upload file %s" % fn)
        self.subreddit.stylesheet.upload(fn.stem, fn)

    def _read_env_options(self):
        for var, target in (("INPUT_CLEAR", "clear"), ("INPUT_CLEANUP", "cleanup"), ("INPUT_SKIP_IMAGES", "skip_images")):
            if var in os.environ:
                setattr(self.args, target, os.environ[var] in TRUE_VALUE)

    def clear(self):
        print("Clear all styles and files")
        existing_styles = self.subreddit.stylesheet()
        self.put_stylesheet('')
        for image in existing_styles.images:
            print("  Removing %(name)s" % image)
            self.subreddit.stylesheet.delete_image(image['name'])


if __name__ == "__main__":
    DUMMY_VALUE = 'dc38489e-3cc0-4167-83c6-f992d50fb04e'
    Actions.add_mask(os.environ.get('praw_client_id', DUMMY_VALUE))
    Actions.add_mask(os.environ.get('praw_client_secret', DUMMY_VALUE))
    Actions.add_mask(os.environ.get('praw_refresh_token', DUMMY_VALUE))
    Actions.add_mask(os.environ.get('praw_password', DUMMY_VALUE))
    Actions.add_mask(os.environ.get('praw_username', DUMMY_VALUE))

    uploader = StyleSheetUpdater("%s/%s" % (PROGRAM, VERSION))
    uploader.main()
