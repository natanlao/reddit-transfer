#!/usr/bin/env python3.8
import configparser
import getpass
import logging
import sys

import praw

log = logging.getLogger('reddit-transfer')
logging.basicConfig(level=logging.INFO)
user_agent = "la.natan.reddit-transfer:v0.0.2"


def get_reddit_object(username: str) -> praw.Reddit:
    """
    Returns a Reddit object authenticated for the given username
    from the stored credentials. If no credentials for the given
    username are stored, prompt the user for credentials and store
    them.

    Credentials are stored in `praw.ini`. The password is not
    stored; the user will always be prompted for it.
    """
    config = configparser.ConfigParser()
    config.read('praw.ini')
    if username not in config:
        config[username] = {
            'username': username,
            'client_id': input(f"Client ID [{username}]: "),
            'client_secret': getpass.getpass(f"Client secret [{username}]: ")
        }
        with open('praw.ini', 'w') as fp:
            config.write(fp)
    password = getpass.getpass(f"Password [{username}]: ")
    auth_code = input(f"Auth code [{username}] (optional): ")
    if auth_code:  # /r/redditdev/comments/74cu2i/-/dnxe1lu/
        password = f'{password}:{auth_code}'
    # We don't specify a site to :class:`praw.Reddit` since praw.ini is loaded
    # at the time that the first instance of :class:`praw.Reddit` is
    # instantiated, and there's no way to ask Praw to reload it.
    return praw.Reddit(password=password, user_agent=user_agent,
                       **config[username])


def sync_data(old_user: str, new_user: str) -> None:
    old = get_reddit_object(old_user)
    new = get_reddit_object(new_user)

    # We could use set.difference here but I think it's overkill and less clear
    old_subs = [sub.display_name for sub in old.user.subreddits(limit=None)]
    log.info(f"{old_user}: found {len(old_subs)} existing subscriptions")
    new_subs = [sub.display_name for sub in new.user.subreddits(limit=None)]
    log.info(f"{new_user}: found {len(new_subs)} existing subscriptions")
    un_sub = [sub for sub in new_subs if sub not in old_subs]
    log.warning(f"{new_user}: unsubscribing from {len(un_sub)} subreddits")
    if len(un_sub) > 0:
        new.subreddit(un_sub[0]).unsubscribe(other_subreddits=un_sub[1:])
    to_sub = [sub for sub in old_subs if sub not in new_subs]
    log.warning(f"{new_user}: subscribing to {len(to_sub)} new subreddits")
    if len(to_sub) > 0:
        new.subreddit(to_sub[0]).subscribe(other_subreddits=to_sub[1:])
    # Since these are bulk operations, we could just unsubscribe from all
    # then resubscribe as needed but I've found that there's some lag between
    # subscribing to a subreddit and the Reddit API recognizing that we've
    # subscribed to a subreddit

    # I unfortunately could find no API for saving in bulk
    old_saved = list(old.user.me().saved(limit=None))
    log.info(f"{old_user}: found {len(old_saved)} existing saved posts, comments")
    new_saved = list(item.id for item in new.user.me().saved(limit=None))
    log.info(f"{new_user}: found {len(new_saved)} existing saved posts, comments")
    new_saved = [item for item in old_saved if item.id not in new_saved]
    log.warning(f"{new_user}: saving {len(new_saved)} posts and comments")
    for i, item in enumerate(new_saved, start=1):
        # This is a little unwieldy, but changing the Reddit instance this way
        # saves us a couple RTTs, or it should, anyway. Maybe there's a better
        # way to do this.
        item._reddit = new
        item.save()
        log.debug(f"{new_user}: saved {item.id=} ({i}/{len(new_saved)})")

    # There is also no API for making friends in bulk :(
    # TODO: remove friends first?
    old_friends = list(old.user.friends())
    log.info(f"{old_user}: found {len(old_friends)} existing friends")
    new_friends = list(friend.name for friend in new.user.friends())
    log.info(f"{new_user}: found {len(new_friends)} existing friends")
    new_friends = [friend for friend in old_friends if friend.name not in new_friends]
    log.warning(f"{new_user}: befriending {len(new_friends)} new users")
    for i, friend in enumerate(new_friends, start=1):
        friend._reddit = new
        friend.friend()
        log.debug(f"{new_user}: added {friend=} ({i}/{len(new_friends)})")

    log.warning(f"{new_user}: copying preferences from {old_user}")
    new.user.preferences.update(**old.user.preferences())

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("./reddit_transfer.py [old-username] [new-username]")
        exit(1)
    _, old_user, new_user = sys.argv
    sync_data(old_user, new_user)
