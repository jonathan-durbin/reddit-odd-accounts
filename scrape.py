import os
import requests
import datetime
import time
import pandas as pd
from functions import utils

# t1_	Comment
# t2_	Account
# t3_	Link
# t4_	Message
# t5_	Subreddit
# t6_	Award

users = ['ButterscotchDue3724']

def scrape(subreddits, hold, delimiter, replace_text, save_dir, filename):
    params = {'limit': 100} # maximum is 100

    # get (first) oauth token, refreshing later if needed
    headers, time_authorized = utils.get_authorization()


    res = requests.get(
        f"https://oauth.reddit.com/u/{users}",
        headers=headers,
        params=params
    )

    for subreddit in subreddits:
        # if the token in the header has expired, refresh it.
        if (time.time() - time_authorized) > 5400:  # number of seconds in 1.5 hours
            print("It's been long enough, refreshing token...")
            headers, time_authorized = utils.get_authorization()

        res = requests.get(
            f"https://oauth.reddit.com/r/{subreddit}/hot",
            headers=headers,
            params=params
        )

        if res.status_code != 200:
            if res.json()['reason'] == 'private':
                print(f'Warning: r/{subreddit} is currently private. Skipping...')
                continue
            else:
                raise ValueError(f"Subreddit: {subreddit} | {res.json()}")

        # Get a pandas dataframe of the result
        data = utils.parse_result(res, delimiter=delimiter, replace_text=replace_text)

        # don't put a header in the csv file more than once.
        if subreddit == subreddits[0]:
            csv_header = True
        else:
            csv_header = False

        data.to_csv(
            f"{save_dir}/{filename}.csv",
            sep=delimiter,  # no delimiter is infallible.
            mode='a',  # append, create file if it doesn't exist.
            index=False,
            header=csv_header
        )

        # 60 requests per minute. res.headers['X-Ratelimit-Reset'] is the countdown.
        print(
            (f"r/{subreddit.ljust(len(max(subreddits, key=len)))} done. "
            f"ETA: {round((len(subreddits) - subreddits.index(subreddit) - 1) * hold)} seconds. "
            f"T-{(res.headers['X-Ratelimit-Reset'] + '.').ljust(4)} to ratelimit reset. "
            f"{res.headers['X-Ratelimit-Remaining'].ljust(5)} requests left. "
            f"Waiting {hold} seconds...")
        )

        # if on last loop, go ahead and break/return. No need to sleep.
        if subreddit == subreddits[-1]: break

        if float(res.headers['X-Ratelimit-Remaining']) <= 2:
            print(f"HEADS UP: {res.headers['X-Ratelimit-Remaining']} requests remaining.")
            time.sleep(res.headers['X-Ratelimit-Reset'])
            continue

        time.sleep(hold)

    return filename


if __name__ == "__main__":
    def main():
        # extract list of subreddit names from file
        with open('subs.txt') as f:
            subs = [i.strip()[2:len(i)-1] for i in f.readlines() if not i.startswith('#') ]

        # count number of files in the save_dir directory, add 1.
        # increment, format nicely
        # combine with today's date
        save_dir='./data/'
        num_data_files = len([i for i in os.listdir(save_dir) if os.path.isfile(save_dir + i)])
        num_data_files = str(num_data_files + 1).rjust(5, '0')
        filename = f"{num_data_files}_{datetime.date.fromtimestamp(time.time()).strftime('%Y-%m-%d')}"

        scrape(
            subreddits=subs,
            hold=1.1,
            # NOTE: If the csv delimiter is in the post title, author name, or post id...
            #   replace it with replace_text
            delimiter='^', replace_text='(caret)',
            save_dir=save_dir, filename = filename
        )

        print('Done.')

    main()
