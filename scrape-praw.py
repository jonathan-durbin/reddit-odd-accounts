import praw
import sqlite3 as sql
import logging
import re
import random
import util

# set up logging
handler = logging.StreamHandler()
logging_level = logging.INFO
handler.setLevel(logging_level)
for logger_name in ("praw", "prawcore"):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging_level)
    logger.addHandler(handler)


# authenticate
with open('secrets.txt') as f:
    lines = [i.strip().split(': ')[1] for i in f.readlines()]
reddit = praw.Reddit("sus-account-search", config_interpolation="basic")
assert reddit.user.me() == lines[2]

# build database
conn = sql.connect('data.db')

refresh = False

if refresh:
    conn.execute('drop table post')
    conn.execute('drop table user')
    util.create_tables(conn)
    assert (
        len(conn.execute('select * from post').fetchall()) == 0
        and 
        len(conn.execute('select * from user').fetchall()) == 0
    )
    # add first user if the table is empty
    # if len(conn.execute('select * from user').fetchall()) == 0:
    first = reddit.redditor("ButterscotchDue3724")
    conn.execute(
        '''
            insert or ignore into user(userid, username, created_at) 
            values (:fullname, :name, :created_utc)
        ''', {
            "fullname": first.fullname, 
            "name": first.name, 
            "created_utc": util.timestamp_to_datetime(first.created_utc)
        }
    )
    conn.commit()


usernames = [i[0] for i in conn.execute(
    '''
        select distinct author 
        from post 
        group by author
        having count(postid) < 10
    ''').fetchall()
]
random.shuffle(usernames)
print(f'Searching {len(usernames)} usernames.')

disallowed_users = [
    'wikipedia_answer_bot', 
    'AutoModerator', 
    'mamnonsaomai', 
    'Philip_Jeffries',
    'Panda_Triple7',
    'CamT106'
]
for user in disallowed_users:
    if user in usernames:
        usernames.remove(user)
    conn.execute('delete from user where username = :user', {"user": user})
    conn.execute('delete from post where author = :user', {"user": user})
    conn.commit()

util.update_readme(conn, './README.md')

for username in usernames:
    # ignore usernames that don't fit the default username naming convention
    if util.username_check(username):
        conn.execute('delete from user where username = :user', {"user": username})
        conn.execute('delete from post where author = :user', {"user": username})
        conn.commit()
        continue
    redditor = reddit.redditor(username)
    if util.user_is_removed(redditor):
        continue
    print(
f'''######### BEGINNING LOOP FOR u/{username:<20} ################
######### PROGRESS: {util.progress_bar(usernames, username, 'X', 29)} ################'''
    )
    posts = redditor.submissions.new(limit=50)
    num_posts = 0
    for post in posts:
        # print(f'Saving post {post.fullname}')
        conn.execute('''
            insert or ignore into post (
                postid, author, submitted_at, post_type, post_parent,
                post_title, post_content
            ) values (
                :fullname, :author, :created_utc, 'SUBMISSION', NULL,
                :title, :selftext
            )
        ''', {
            "fullname": post.fullname,
            "author": post.author.name,
            "created_utc": util.timestamp_to_datetime(post.created_utc),
            "title": post.title,
            "selftext": post.selftext
        })
        conn.commit()
        num_posts += 1
        if post.num_comments == 0: 
            continue
        comments = post.comments.list()
        num_comments = 0
        for comment in comments:
            if util.user_is_removed(comment.author) or util.username_check(username):
                conn.execute('delete from user where username = :user', {"user": username})
                conn.execute('delete from post where author = :user', {"user": username})
                conn.commit()
                continue
            conn.execute('''
                insert or ignore into post (
                    postid, author, submitted_at, post_type, post_parent,
                    post_title, post_content
                ) values (
                    :fullname, :author, :created_utc, 'COMMENT', :parent_id,
                    NULL, :body
                )
            ''', {
                "fullname": comment.fullname,
                "author": comment.author.name,
                "created_utc": util.timestamp_to_datetime(comment.created_utc),
                "parent_id": comment.parent_id,
                "body": comment.body
            })
            conn.commit()
            num_comments += 1
            author = comment.author
            # ignore author if they are already in the DB
            if author.name in usernames:
                continue
            conn.execute('''
                insert or ignore into user (userid, username, created_at)
                values (:fullname, :name, :created_utc)
            ''', {
                "fullname": author.fullname,
                "name": author.name,
                "created_utc": util.timestamp_to_datetime(author.created_utc)
            })
            conn.commit()
        print(f'Saw {num_comments} comments')
    print(f'Saw {num_posts} posts made by u/{username}')

