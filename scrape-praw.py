import praw
import sqlite3 as sql
import logging
import datetime as dt

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

def timestamp_to_datetime(t):
    return dt.datetime.fromtimestamp(t).isoformat()

# build database
conn = sql.connect('data.db')

def create_tables(conn):
    conn.execute(
        '''
        create table if not exists user(
            userid text primary key, 
            username text,
            created_at text,
            unique(userid)
        )
        '''
    )
    conn.execute(
        '''
        create table if not exists post(
            postid text primary key, 
            author text, 
            submitted_at text,
            post_type text, 
            post_parent text, 
            post_title text, 
            post_content text, 
            foreign key(author) references user(userid),
            foreign key(post_parent) references post(postid),
            unique(postid)
        )
        '''
    )

refresh = False

if refresh:
    conn.execute('drop table post')
    conn.execute('drop table user')
    create_tables(conn)
    assert (
        len(conn.execute('select * from post').fetchall()) == 0
        and 
        len(conn.execute('select * from user').fetchall()) == 0
    )
else:
    create_tables(conn)

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
        "created_utc": timestamp_to_datetime(first.created_utc)
    }
)
conn.commit()

postids = [i[0] for i in conn.execute('select postid from post').fetchall()]

usernames = [i[0] for i in conn.execute(
    '''
        select distinct username 
        from post 
        join user on user.userid = post.author 
        group by userid
        having count(*) < 50
    ''').fetchall()
]

disallowed_users = ['wikipedia_answer_bot']
for user in disallowed_users:
    usernames.remove(user)

for username in usernames:
    print(f'######### BEGINNING LOOP FOR u/{username} #########')
    redditor = reddit.redditor(username)
    if redditor.is_blocked or redditor.is_suspended:
        continue
    for post in redditor.submissions.new():
        # if post.fullname in postids: 
        #     continue
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
            "author": post.author.fullname,
            "created_utc": timestamp_to_datetime(post.created_utc),
            "title": post.title,
            "selftext": post.selftext
        })
        conn.commit()

        if post.num_comments == 0: 
            continue
        for comment in post.comments.list():
            # if comment.fullname in postids:
            #     continue
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
                "author": comment.author.fullname,
                "created_utc": timestamp_to_datetime(comment.created_utc),
                "parent_id": comment.parent_id,
                "body": comment.body
            })
            conn.commit()
            author = comment.author
            conn.execute('''
                insert or ignore into user (userid, username, created_at)
                values (:fullname, :name, :created_utc)
            ''', {
                "fullname": author.fullname,
                "name": author.name,
                "created_utc": timestamp_to_datetime(author.created_utc)
            })
            conn.commit()

# reddit.redditor("").comments
# reddit.redditor("").submissions
# reddit.redditor("").created_utc
# reddit.redditor("").submissions.new()
#   for post in ^: 
#       post.author, post.comments, post.created_utc, post.fullname
#       post.selftext, post.title
# reddit.redditor("").fullname
# submission.comments.list()

