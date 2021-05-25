# reddit-transfer

Transfer account data (saved posts, saved comments, friends, subscriptions,
settings) between two reddit accounts.

Copying preferences works... kind of. It copies most settings over.

The script can handle accounts with two-factor authentication, too. Either way,
it needs application keys (choose type 'script').

## Usage

Running Python 3.9:

    pip install -r requirements.txt
    python reddit_transfer.py login $OLD_USERNAME
    python reddit_transfer.py login $NEW_USERNAME
    python reddit_transfer.py transfer $OLD_USERNAME $NEW_USERNAME

