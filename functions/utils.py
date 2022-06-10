# Utility functions for scrape.py

import requests
import pandas as pd
import datetime
import time


def get_authorization():
    with open('secrets.txt') as f:
        lines = [i.strip().split(': ')[1] for i in f.readlines()]

    auth = requests.auth.HTTPBasicAuth(lines[0], lines[1])
    data = {'grant_type': 'password',
            'username': lines[2],
            'password': lines[3]
    }
    headers = {'User-Agent': f'chrome:{lines[2]}:v0.1 (by /u/sus-account-search)'}

    # send our request for an OAuth token
    res = requests.post(
        'https://www.reddit.com/api/v1/access_token',
        auth=auth, data=data, headers=headers
    )

    # convert response to JSON and pull access_token value
    # NOTE: token valid for ~2 hrs
    TOKEN = f"bearer {res.json()['access_token']}"
    print(f'TOKEN ACQUIRED: {TOKEN}')

    # add authorization to our headers dictionary
    headers = {**headers, **{'Authorization': TOKEN}}

    time_authorized = time.time()

    return headers, time_authorized


# regex to (simple-like) format raw json from reddit for toubleshooting:
# '(\w*-?)+':
def parse_result(res, delimiter, replace_text, debug=False):
    df = pd.DataFrame()

    for post in res.json()['data']['children']:
        p = post['data']

        try:
            if p['stickied'] == True:
                continue

            df = df.append({
                'TIME_STORED': str(time.time()),
                'subreddit': p['subreddit'],
                'title': p['title'].replace(delimiter, replace_text),
                'author': p['author'].replace(delimiter, replace_text),
                # 'selftext': p['selftext'],
                'upvote_ratio': p['upvote_ratio'],
                'ups': p['ups'],
                'downs': p['downs'],
                'score': p['score'],
                'num_comments': p['num_comments'],
                'num_crossposts': p['num_crossposts'],
                'subreddit_subscribers': p['subreddit_subscribers'],
                'created_utc': datetime.datetime.fromtimestamp(p['created_utc']).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'id': p['id'].replace(delimiter, replace_text),
                'kind': post['kind']
            }, ignore_index=True)

            if debug == True:
                print(f"Stored post titled \"{p['title']}\" from r/{p['subreddit']}")

        except:
            print(f"Something weird happened.")
            with open('debug-this.txt', 'w') as f:
                f.write(str(res.json()))
            continue
    return df
