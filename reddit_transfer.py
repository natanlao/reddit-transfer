# -*- coding: utf-8 -*-
import configparser
import logging

import click
import praw

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)
user_agent = "la.natan.reddit-transfer:v0.0.1"


def get_reddit_object(username: str) -> praw.Reddit:
    """
    Returns a Reddit object authenticated for the given username
    from the stored credentials. If no credentials for the given
    username are stored, we prompt the user for credentials and
    store them.

    Credentials are stored in `praw.ini`. The password is not
    stored; the user will always be prompted for it.
    """
    config = configparser.ConfigParser()
    config.read('praw.ini')
    if username not in config:
        config[username] = {
            'username': username,
            'client_id': click.prompt(f"Client ID [{username}]"),
            'client_secret': click.prompt(f"Client secret [{username}]",
                                          hide_input=True) 
        }
        with open('praw.ini', 'w') as fp:
            config.write(fp)
    password = click.prompt(f"Password [{username}]", hide_input=True)
    auth_code = click.prompt(f"Auth code [{username}] (optional)", default="", show_default=False)
    if auth_code:  # https://www.reddit.com/r/redditdev/comments/74cu2i/-/dnxe1lu/
        password = f'{password}:{auth_code}'
    # We don't specify a site to :class:`praw.Reddit` since praw.ini is loaded
    # at the time that the first instance of :class:`praw.Reddit` is
    # instantiated, and there's no way to ask Praw to reload it.
    return praw.Reddit(password=password, user_agent=user_agent, **config[username])


@click.command()
@click.argument('old_user')
@click.argument('new_user')
def sync_data(old_user: str, new_user: str):
    old = get_reddit_object(old_user)
    new = get_reddit_object(new_user)

    # Transfer subs
    # I don't know a better way to do this
    current = [sub.display_name for sub in new.user.subreddits(limit=None)]
    click.echo(f"Unsubscribing from {len(current)} subreddits")
    if len(current) > 0:
        new.subreddit(current[0]).unsubscribe(other_subreddits=current)  # Unsub from defaults
    subs = [sub.display_name for sub in old.user.subreddits(limit=None)]
    click.echo(f"Subscribing to {len(subs)} subreddits")
    new.subreddit(subs[0]).subscribe(other_subreddits=subs)

    # Transfer saved
    click.echo("Transferring saved posts and comments.")
    old_saved = old.user.me().saved(limit=None)
    new_saved = [item.id for item in new.user.me().saved(limit=None)]
    with click.progressbar(old_saved,
                           label="Transferring saved posts and comments...") \
                           as saved:
        for item in saved:
            if item.id in new_saved:
                log.debug(f"Item {item.id} already saved, skipping...")
                continue
            if isinstance(item, praw.models.Comment):
                log.debug("Saving comment %s", item.id)
                new.comment(item.id).save()
            elif isinstance(item, praw.models.Submission):
                log.debug("Saving submission %s", item.id)
                new.submission(item.id).save()
            else:
                raise

    # Transfer friends
    old_friends = [friend.name for friend in old.user.friends()]
    new_friends = [friend.name for friend in new.user.friends()]
    with click.progressbar(old_friends, label="Transferring friends...") as friends:
        for friend in friends:
            log.debug("Adding friend %s", friend)
            if friend in new_friends:
                log.debug("Friend %s is a duplicate!", friend)
                continue  # Skip duplicate
            new.redditor(friend).friend()

if __name__ == '__main__':
    sync_data()
