# reddit-transfer

Synchronizes account data (saved submission, saved comments, friends,
subscriptions, settings) between two reddit accounts. This synchronization is
one-way but also destructive; this means, for example, that if a submission is
saved in the destination account but not in the source account, the submission
will be unsaved in the destination account.

It's called "reddit transfer" instead of "reddit sync" because there's already a
cool app called Sync for Reddit that you should try because it's really cool.

Copying preferences works for all preferences accessible via the API. Some
preferences (e.g., those related to profiles) can't be controlled by the API.
(Or maybe they can, I'm not really concerned with those settings so I haven't
investigated it thoroughly.)

The script can handle accounts with two-factor authentication, too. Either way,
it needs application keys (choose type 'script').

## Usage

Running Python 3.9:

    pip install -r requirements.txt
    python reddit_transfer.py login $OLD_USERNAME
    python reddit_transfer.py login $NEW_USERNAME
    python reddit_transfer.py transfer $OLD_USERNAME $NEW_USERNAME

## Caveats

MFA authentication may be broken. You can authenticate successfully if MFA is
disabled.

