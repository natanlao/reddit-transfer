#!/usr/bin/env python3.9
"""
Transfer reddit subscriptions, saved posts/comments, friends, and
settings from one account to another.
"""
import argparse
import collections
import configparser
import functools
import getpass
import logging
import sys
from typing import Mapping, Optional, Set, Sequence

import praw

log = logging.getLogger('reddit-transfer')
logging.basicConfig(level=logging.INFO)
user_agent = "la.natan.reddit-transfer:v0.0.2"


def prompt(question: str,
           suggestion: Optional[str] = None,
           optional: bool = False) -> Optional[str]:
    suggest = f' [{suggestion}]' if suggestion else ''
    option = ' (optional)' if optional else ''
    answer = input(f'{question}{suggest}{option}: ')
    if answer:
        return answer
    elif suggestion:
        return suggestion
    elif optional:
        return None
    else:
        raise ValueError(f'{question} is required')


class Config:

    def __init__(self, username: str, config_file: str = 'praw.ini'):
        # praw.Reddit exposes a config management interface but we can't use
        # it without authenticating
        self.username = username
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def write(self):
        with open(config_file, 'w') as fp:
            self.config.write(fp)
        log.info('Credentials saved to %r', config_file)

    def read(self) -> Mapping:
        return self.config[self.username]

    def login(self):
        """
        Interactive; prompt for login details and store in praw.ini.
        """
        client_id = self.config.get(self.username, 'client_id', fallback=None)
        client_secret = self.config.get(self.username, 'client_secret', fallback=None)
        self.config[username] = {
            'username': self.username,
            'client_id': prompt('Client ID', client_id),
            'client_secret': prompt('Client secret', client_secret)
        }
        self.write()


class User:

    def __init__(self, username: str):
        self.username = username
        password = self.prompt_password()
        config = Config(username)
        try:
            self.reddit = praw.Reddit(username,
                                      password=password,
                                      user_agent=user_agent,
                                      **config.read())
        except configparser.NoSectionError:
            raise RuntimeError(f'Did you run `{sys.argv[0]} login {username}?')

    def prompt_password(self) -> str:
        password = getpass.getpass(f'Password for /u/{self.username}: ')
        # TODO: MFA may be broken
        authcode = prompt(f'MFA for /u/{self.username}', optional=True)
        return f'{password}:{authcode}' if authcode else password

    @functools.cached_property
    def subscriptions(self) -> Set[str]:
        log.info('Fetching subreddits for /u/%s', self.username)
        return {sub.display_name for sub in self.reddit.user.subreddits(limit=None)}

    @functools.cached_property
    def friends(self) -> Set[str]:
        log.info('Fetching friends for /u/%s', self.username)
        return {friend.name for friend in self.reddit.user.friends()}

    @functools.cached_property
    def saved(self) -> Set[str]:
        log.info('Fetching saved comments/posts for /u/%s', self.username)
        return {item for item in self.reddit.user.me().saved(limit=None)}


# To be precise, the behavior implemented is closer to synchronization than
# just transferring data, but there's a (great) client named 'reddit sync'
# and I'd prefer to avoid publicly overloading that term.
def sync_data(src_user: str, dst_user: str) -> None:
    src = User(src_user)
    dst = User(dst_user)

    # Since these are bulk operations, we could just unsubscribe from all
    # then resubscribe as needed but I've found that there's some lag between
    # subscribing to a subreddit and the Reddit API recognizing that we've
    # subscribed to a subreddit
    for sub in dst.subscriptions - src.subscriptions:
        log.info('Unsubscribe from /r/%s', sub)
        dst.reddit.subreddit(sub).unsubscribe()

    for sub in src.subscriptions - dst.subscriptions:
        log.info('Subscribe to /r/%s', sub)
        dst.reddit.subreddit(sub).subscribe()

    for friend in dst.friends - src.friends:
        log.info('Friend /u/%s', friend)
        dst.reddit.redditor(friend).unfriend()

    for friend in src.friends - dst.friends:
        log.info('Unfriend /u/%s', friend)
        dst.reddit.redditor(friend).friend()

    for thing in dst.saved - src.saved:
        # TODO: Leaky abstraction
        log.info('Unsave %r', thing)
        if isinstance(thing, praw.models.Submission):
            dst.reddit.submission(thing.id).unsave()
        elif isinstance(thing, praw.models.Comment):
            dst.reddit.comment(thing.id).unsave()
        else:
            raise RuntimeError('unexpected object type')

    for thing in src.saved - dst.saved:
        log.info('Save %r', thing)
        if isinstance(thing, praw.models.Submission):
            dst.reddit.submission(thing).save()
        elif isinstance(thing, praw.models.Comment):
            dst.reddit.comment(thing).save()
        else:
            raise RuntimeError('unexpected object type')

    log.info(f"Copy preferences from {dst_user}")
    dst.reddit.user.preferences.update(**src.reddit.user.preferences())


def main(argv: Sequence[str]):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(help='Specify action', dest='action')
    subparsers.required = True

    login_parser = subparsers.add_parser('login')
    login_parser.add_argument('username')

    transfer_parser = subparsers.add_parser('transfer')
    transfer_parser.add_argument('src_user', help='User to copy data from')
    transfer_parser.add_argument('dst_user', help='User to copy data to')

    args = parser.parse_args(argv)

    if args.action == 'login':
        Config(args.username).login()
    elif args.action == 'transfer':
        sync_data(args.src_user, args.dst_user)
    else:
        exit(1)


if __name__ == '__main__':
    main(sys.argv[1:])
