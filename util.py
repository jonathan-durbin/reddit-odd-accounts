import datetime as dt
import re

def timestamp_to_datetime(t):
    return dt.datetime.fromtimestamp(t).isoformat()

def user_is_removed(redditor):
    if (
        (hasattr(redditor, 'is_blocked') and redditor.is_blocked == True)
        or
        (hasattr(redditor, 'is_suspended') and redditor.is_suspended == True)
        and
        hasattr(redditor, 'name')
    ):
        print(f'\n######## {redditor.name} IS A BLOCKED/SUSPENDED ACCOUNT ##########\n')
        return True

    elif hasattr(redditor, 'name') != True:  # Could also do `redditor is None`
        print(f'\n######## FOUND ACCOUNT THAT WAS REMOVED ##########\n')
        return True

    else:
        return False

def update_readme(conn, path_to_file):
    with open(path_to_file, 'r') as f:
        lines = f.readlines()

    total_posts = conn.execute('select count(*) from post').fetchall()[0][0]
    total_accounts = conn.execute('select count(*) from user').fetchall()[0][0]

    lines[7] = f'{total_posts:,} Posts\n'
    lines[8] = f'{total_accounts:,} Accounts\n'

    with open(path_to_file, 'w') as f:
        f.writelines(lines)

def progress_bar(items, item, fill, length):
    # assumes a list with unique elements
    i = items.index(item)

    progress = 1-(len(items)-(i+1))/len(items)
    fill_amount = round((length-2) * progress)
    space = length - fill_amount

    return f'[{fill * fill_amount}{" " * space}]'

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
            foreign key(author) references user(username),
            foreign key(post_parent) references post(postid),
            unique(postid)
        )
        '''
    )

def username_check(username):
    return re.match('^(?!(([A-Z].*?)[-_]?([A-Z].*?)[-_]?(\d+))).*', username)