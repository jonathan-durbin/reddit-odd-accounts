# reddit-odd-accounts
A simple repo containing code used to search Reddit for accounts that behave a very specific way.

# Info
At the time of the most recent update, this script has found:

```
41,840 Posts
2,586 Accounts
```

# Background
While browsing Reddit, I happened to find a user who only posted what looked like gibberish on their profile. 

![Example post](/img/example-odd-post.png)

After scrolling down a ways, I saw that this account also makes comments on other (similarly gibberish) posts

![Example comment](/img/example-odd-comment.png)

## Account Naming
I also noticed that these accounts are all named in a similar way. 

```
[word][-|_| ][word][-|_| ][numbers]

in regex (I think this is right):

(.*?)[-_]?(.*?)[-_]?(\d+)
```

I think this name-generation method is not new. Reddit suggests these account names to new users. What's concerning to me is if I see someone with a username like the above, they may be a bot or they may be a real person who doesn't care too much about what their username looks like.

## Patterns
The content of these posts and comments seem to be random but based on real information. In the two images above, I see parts of addresses, recipes, and what looks like a company mission statement.

# Thoughts
What I want to know is: **Why**? 

I have a few ideas.

- To generate fake engagement on accounts that will one day be sold to advertisers.
- Someone somewhere is testing a method of fake account creation and interaction.
    - Maybe to sell the accounts one day.
    - Once the method is perfected, maybe they will start reaching out and interacting with real users for advertisement or to (if you will allow me to put on my tin hat for a moment) affect the sentiment surrounding various topics on Reddit.

