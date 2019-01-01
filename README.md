Rudimentary reddit account transfer script. Transfer friends, subreddits, and
saved posts. Can handle accounts with two-factor authentication.

# Usage

    $ pip install -r requirements.txt
    $ python reddit_transfer.py <old_username> <new_username>

# Limitations

* Does not properly handle accounts where the amount of saved posts, subreddits, or friends is greater than 1,000
* Logging and progress-tracking is very rudimentary