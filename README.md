# reddit-transfer

Rudimentary reddit account transfer script. Given a new username and an old
username:

1. unsubscribes from all subreddits on the new user,
2. copies all subreddit subscriptions from old user to new user,
3. copies all saved posts and comments from old user to new user,
4. copies all friends from old user to new user, and
5. copies preferences from old user to new user.

Copying preferences works... kind of. It copies most settings over.

The script can handle accounts with two-factor authentication, too. Either way,
it needs application keys (choose type 'script').

## Usage

Running Python 3.9:

    $ pip install -r requirements.txt
    $ python reddit_transfer.py <old_username> <new_username>

## Limitations

* It probably can't properly handle accounts with more than 1,000 saved posts,
  subreddits, or friends. But I haven't tried.
