import praw
import sqlite3 as sql
import logging

# set up logging
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
for logger_name in ("praw", "prawcore"):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)


# authenticate
with open('secrets.txt') as f:
    lines = [i.strip().split(': ')[1] for i in f.readlines()]

reddit = praw.Reddit(
    client_id = lines[0],
    client_secret = lines[1],
    password=lines[3],
    user_agent=f'chrome:{lines[2]}:v0.1 (by /u/{lines[2]})',
    username = lines[2],
)

assert reddit.user.me() == lines[2]


# build database
conn = sql.connect('data.db')

conn.execute(
    '''
    create table if not exists user(
        userid int primary key, 
        username text
    )
    '''
)
conn.execute(
    '''
    create table if not exists post(
        postid text primary key, 
        author int, 
        posttype text, 
        postparent text, 
        posttitle text, 
        postcontent text, 
        foreign key(author) references user(userid),
        foreign key(postparent) references post(postid)
    )
    '''
)


