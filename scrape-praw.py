import praw
import sqlite3 as sql
import logging
import datetime as dt

# set up logging
handler = logging.StreamHandler()
logging_level = logging.Info
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

def timestamp_to_datetime(t):
    return dt.datetime.fromtimestamp(t).isoformat()

def user_is_removed(redditor):
    if (
        (hasattr(redditor, 'is_blocked') and redditor.is_blocked == True)
        or
        (hasattr(redditor, 'is_suspended') and redditor.is_suspended == True)
    ):
        print(f'########{redditor.name} IS A BLOCKED/SUSPENDED ACCOUNT##########')
        return True
    else:
        return False

def update_readme(conn):
    with open('README.md', 'r') as f:
        lines = f.readlines()
    total_posts = conn.execute('select count(*) from post').fetchall()[0][0]
    total_accounts = conn.execute('select count(*) from user').fetchall()[0][0]
    lines[7] = f'{total_posts:,} Posts\n'
    lines[8] = f'{total_accounts:,} Accounts\n'
    with open('README.md', 'w') as f:
        f.writelines(lines)

def progress_bar(items, item, fill, length):
    # assumes a list with unique elements
    i = items.index(item)
    progress = 1-(len(items)-(i+1))/len(items)
    fill_amount = round((length-2) * progress)
    space = length - fill_amount
    return f'[{fill * fill_amount}{" " * space}]'



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

update_readme(conn)

for username in usernames:
    redditor = reddit.redditor(username)
    if user_is_removed(redditor):
        continue
    print(f'''
######### BEGINNING LOOP FOR u/{username:<20} ################
######### PROGRESS: {progress_bar(usernames, username, 'X', 31)} ################''')
    for post in redditor.submissions.new():
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
            if user_is_removed(comment.author):
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

